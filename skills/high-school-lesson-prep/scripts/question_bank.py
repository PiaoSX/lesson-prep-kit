"""Incremental local question-bank metadata index; never opens material contents."""

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile


EXTENSIONS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".md", ".csv", ".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp", ".zip", ".rar", ".7z", ".mp3", ".mp4"}
REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


class BankError(Exception):
    pass


def path_key(path):
    return os.path.normcase(os.path.abspath(path))


def linked(metadata):
    return stat.S_ISLNK(metadata.st_mode) or bool(getattr(metadata, "st_file_attributes", 0) & REPARSE_POINT)


def material_name(name):
    lower = name.casefold()
    return (
        not lower.startswith(("~$", ".~"))
        and lower not in {"desktop.ini", "thumbs.db"}
        and not any(part in {"tmp", "temp", "bak", "part", "crdownload"} for part in lower.split(".")[1:-1])
        and Path(name).suffix.casefold() in EXTENSIONS
    )


def valid_relative(value):
    return (
        isinstance(value, str) and bool(value) and "\\" not in value
        and ":" not in value and "\x00" not in value
        and not PurePosixPath(value).is_absolute()
        and all(part not in {"", ".", ".."} for part in value.split("/"))
    )


def valid_record(record):
    return (
        isinstance(record, dict)
        and type(record.get("size")) is int and record["size"] >= 0
        and type(record.get("mtime_ns")) is int
        and isinstance(record.get("extension"), str)
        and record["extension"] in EXTENSIONS
    )


def load_manifest(state_dir, required=False):
    manifest_path = state_dir / "manifest.json"
    try:
        raw = manifest_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        if required:
            raise BankError("尚无题库索引，请先运行 scan。") from None
        return None
    try:
        manifest = json.loads(raw)
        valid = (
            isinstance(manifest, dict) and manifest.get("schema_version") == 1
            and isinstance(manifest.get("root"), str) and Path(manifest["root"]).is_absolute()
            and isinstance(manifest.get("scanned_at"), str)
            and isinstance(manifest.get("files"), dict)
            and isinstance(manifest.get("last_changes"), dict)
        )
        if not valid:
            raise ValueError("invalid manifest structure")
        for relative, record in manifest["files"].items():
            if not valid_relative(relative) or not valid_record(record):
                raise ValueError("invalid file metadata")
            if PurePosixPath(relative).suffix.casefold() != record["extension"]:
                raise ValueError("inconsistent extension")
        changes = manifest["last_changes"]
        if type(changes.get("baseline")) is not bool:
            raise ValueError("missing baseline flag")
        for kind in ("added", "modified", "removed"):
            if not isinstance(changes.get(kind), list):
                raise ValueError("invalid change lists")
            for item in changes[kind]:
                if not isinstance(item, dict) or not valid_relative(item.get("relative_path")) or not valid_record(item):
                    raise ValueError("invalid change metadata")
        return manifest
    except (ValueError, TypeError) as error:
        raise BankError(f"旧清单无效，已保留原文件：{manifest_path}（{error}）") from error


def collect_files(root, state_dir):
    """Fail on traversal/stat errors; do not follow links or read any file body."""
    records = {}
    pending = [root]
    excluded = path_key(state_dir)
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if path_key(entry.path) == excluded:
                        continue
                    try:
                        metadata = entry.stat(follow_symlinks=False)
                    except OSError as error:
                        raise BankError(f"读取文件元数据失败，未更新清单：{entry.path}（{error}）") from error
                    if linked(metadata):
                        continue
                    if stat.S_ISDIR(metadata.st_mode):
                        pending.append(Path(entry.path))
                    elif stat.S_ISREG(metadata.st_mode) and material_name(entry.name):
                        relative = Path(entry.path).relative_to(root).as_posix()
                        records[relative] = {"size": metadata.st_size, "mtime_ns": metadata.st_mtime_ns, "extension": Path(entry.name).suffix.casefold()}
        except OSError as error:
            raise BankError(f"读取目录失败，未更新清单：{directory}（{error}）") from error
    return dict(sorted(records.items()))


def item_for(root, relative, metadata):
    return {"relative_path": relative, "path": str(root.joinpath(*relative.split("/"))), **metadata}


def report_text(changes):
    local_time = datetime.fromisoformat(changes["scanned_at"]).astimezone(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    lines = ["# 本地题库更新", "", f"扫描时间（北京时间 UTC+08:00）：{local_time}", f"题库：{changes['root']}", "", "仅比较相对路径、文件大小和修改时间；未读取题目内容、未做 OCR、未解压资料。", ""]
    if changes["baseline"]:
        lines.append(f"首次建立基线：现有 {changes['existing']} 个资料文件，新增计为 0。")
    else:
        lines.append(f"现有 {changes['existing']} 个资料文件；新增 {len(changes['added'])}、修改 {len(changes['modified'])}、移除 {len(changes['removed'])}。")
    lines.extend(["", "文件变化不等同于题目内容变化；重命名按移除和新增记录。"])
    for kind, label in (("added", "新增"), ("modified", "修改"), ("removed", "移除")):
        lines.extend(["", f"## {label}（{len(changes[kind])}）", ""])
        for item in changes[kind]:
            target = Path(item["path"]).as_posix().replace("<", "%3C").replace(">", "%3E")
            label = item["relative_path"].replace("[", "\\[").replace("]", "\\]")
            lines.append(f"- [{label}](<{target}>)")
        if not changes[kind]:
            lines.append("无。")
    return "\n".join(lines) + "\n"


def save_state(state_dir, manifest):
    """Stage everything first and replace the authoritative manifest last."""
    state_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {"manifest": str(state_dir / "manifest.json"), "changes": str(state_dir / "changes.json"), "report": str(state_dir / "question-bank-updates.md")}
    contents = [
        (Path(artifacts["changes"]), json.dumps(manifest["last_changes"], ensure_ascii=False, indent=2) + "\n"),
        (Path(artifacts["report"]), report_text(manifest["last_changes"])),
        (Path(artifacts["manifest"]), json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"),
    ]
    staged = []
    try:
        for destination, content in contents:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=state_dir, prefix=".bank-", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                staged.append((temporary, destination))
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        for temporary, destination in staged:
            os.replace(temporary, destination)
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)
    return artifacts


def scan(args):
    supplied_root = Path(args.root).absolute()
    metadata = supplied_root.lstat()
    if linked(metadata) or not stat.S_ISDIR(metadata.st_mode):
        raise BankError(f"题库根路径必须是普通目录：{supplied_root}")
    root = supplied_root.resolve(strict=True)
    state_dir = Path(args.state_dir).absolute() if args.state_dir else root.parent / ".lesson-prep-bank"
    if path_key(root) == path_key(state_dir):
        raise BankError("索引目录不能直接等于题库根目录，请使用单独的子目录或其它目录。")
    previous = load_manifest(state_dir)
    if previous is not None and path_key(previous["root"]) != path_key(root):
        raise BankError("旧清单的题库根路径不匹配，已保留原文件；请指定其它 --state-dir。")
    files = collect_files(root, state_dir)
    old_files = previous["files"] if previous else {}
    baseline = previous is None
    changes = {"baseline": baseline, "root": str(root), "scanned_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "existing": len(files), "content_read": False, "added": [], "modified": [], "removed": []}
    if not baseline:
        for relative in sorted(files.keys() - old_files.keys()):
            changes["added"].append(item_for(root, relative, files[relative]))
        for relative in sorted(files.keys() & old_files.keys()):
            if files[relative] != old_files[relative]:
                changes["modified"].append(item_for(root, relative, files[relative]))
        for relative in sorted(old_files.keys() - files.keys()):
            changes["removed"].append(item_for(root, relative, old_files[relative]))
    manifest = {"schema_version": 1, "root": str(root), "scanned_at": changes["scanned_at"], "files": files, "last_changes": changes}
    artifacts = save_state(state_dir, manifest)
    samples = []
    for kind in ("added", "modified", "removed"):
        samples.extend({"change": kind, **item} for item in changes[kind][:12 - len(samples)])
    return {"ok": True, "baseline": baseline, "root": str(root), "state_dir": str(state_dir), "existing": len(files), "added": len(changes["added"]), "modified": len(changes["modified"]), "removed": len(changes["removed"]), "unchanged": len(files) - len(changes["added"]) - len(changes["modified"]), "content_read": False, "scanned_at": changes["scanned_at"], "change_samples": samples, "artifacts": artifacts}


def search(args):
    state_dir = Path(args.state_dir).absolute()
    manifest = load_manifest(state_dir, required=True)
    queries = [value.strip().casefold() for value in args.query]
    if not all(queries) or args.limit <= 0:
        raise BankError("--query 不能为空，--limit 必须是正整数。")
    root = Path(manifest["root"])
    changed = {item["relative_path"]: kind for kind in ("added", "modified") for item in manifest["last_changes"][kind]}
    results = []
    matched = 0
    for relative, metadata in sorted(manifest["files"].items()):
        if args.changes_only and relative not in changed:
            continue
        if any(query in relative.casefold() for query in queries):
            matched += 1
            if len(results) < args.limit:
                results.append({**item_for(root, relative, metadata), "change": changed.get(relative, "unchanged")})
    return {"ok": True, "root": str(root), "scanned_at": manifest["scanned_at"], "queries": args.query, "changes_only": args.changes_only, "match_type": "path_and_filename", "content_read": False, "notice": "仅按最近扫描的路径和文件名匹配；题目内容未读，需按需打开候选文件核实。", "matched": matched, "results": results}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    scan_parser = commands.add_parser("scan", help="扫描元数据，报告相对上次扫描的变化")
    scan_parser.add_argument("--root", required=True)
    scan_parser.add_argument("--state-dir", required=True)
    search_parser = commands.add_parser("search", help="按路径或文件名找候选资料，不读取内容")
    search_parser.add_argument("--query", action="append", required=True)
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.add_argument("--state-dir", required=True)
    search_parser.add_argument("--changes-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = scan(args) if args.command == "scan" else search(args)
    except (BankError, OSError, UnicodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    raise SystemExit(main())

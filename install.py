#!/usr/bin/env python3
"""Copy the bundled skills into an agent's skills directory without overwriting."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys


ROOT = Path(__file__).resolve().parent
SKILLS = ('high-school-lesson-prep', 'chinese-material-search')
LIBRARY_FILES = ('index.md', 'methods.json', 'mathematics.md', 'physics.md',
                 'chemistry.md', 'biology.md')


def is_link(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))


def fingerprint(directory):
    if is_link(directory) or not directory.is_dir():
        raise ValueError(f'Expected an ordinary directory: {directory}')
    result = {}
    for current, directories, filenames in os.walk(directory):
        for name in directories + filenames:
            path = Path(current) / name
            if is_link(path):
                raise ValueError(f'Links are not allowed in skill resources: {path}')
        for name in filenames:
            path = Path(current) / name
            if not stat.S_ISREG(path.stat().st_mode):
                raise ValueError(f'Unsupported resource: {path}')
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def source_bundles():
    bundles = []
    for name in SKILLS:
        source = ROOT / 'skills' / name
        manifest = fingerprint(source)
        required = ['SKILL.md']
        if name == 'high-school-lesson-prep':
            required += ['references/method-library/' + item for item in LIBRARY_FILES]
        if not all(item in manifest for item in required):
            raise ValueError(f'Incomplete skill bundle: {source}')
        (source / 'SKILL.md').read_text(encoding='utf-8')
        bundles.append((name, source.resolve(), manifest))
    return bundles


def plan(target, bundles):
    if os.path.lexists(target) and (is_link(target) or not target.is_dir()):
        raise ValueError(f'Target must be an ordinary directory: {target}')
    result = []
    for name, source, _ in bundles:
        destination = target / name
        resolved = destination.resolve()
        if resolved.is_relative_to(source) or source.is_relative_to(resolved):
            raise ValueError(f'Installation would overlap its source: {destination}')
        exists = os.path.lexists(destination)
        if exists:
            if is_link(destination) or not destination.is_dir():
                raise ValueError(f'Existing file or link left unchanged: {destination}')
            (destination / 'SKILL.md').read_bytes()
        result.append({'name': name, 'path': str(destination),
                       'status': 'skipped-existing' if exists else 'would-install'})
    return result


def install(target, dry_run=False):
    target = Path(target).expanduser().absolute()
    bundles = source_bundles()
    result = plan(target, bundles)
    if dry_run:
        return {'target': str(target), 'dry_run': True, 'skills': result}
    target.mkdir(parents=True, exist_ok=True)
    lock = target / '.lesson-prep-install.lock'
    try:
        lock.mkdir()
    except FileExistsError:
        raise ValueError(f'Another installation may be active. Lock left unchanged: {lock}') from None
    created = []
    try:
        result = plan(target, bundles)
        for item, (_, source, manifest) in zip(result, bundles):
            if item['status'] == 'skipped-existing':
                continue
            destination = target / item['name']
            destination.mkdir()  # Exclusive creation; never merge into an existing skill.
            created.append(destination)
            shutil.copytree(source, destination, dirs_exist_ok=True)
            if fingerprint(destination) != manifest:
                raise ValueError(f'Copied files did not match the source: {destination}')
            item['status'] = 'installed'
    except Exception:
        for directory in reversed(created):
            if directory.parent == target and not is_link(directory):
                shutil.rmtree(directory)
        raise
    finally:
        lock.rmdir()
    return {'target': str(target), 'dry_run': False, 'skills': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    codex_home = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex')
    parser.add_argument('--target', default=str(codex_home / 'skills'),
                        help='Skills directory (default: CODEX_HOME/skills or ~/.codex/skills)')
    parser.add_argument('--dry-run', action='store_true', help='Print the plan without writing files')
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.target, args.dry_run), ensure_ascii=False, indent=2))
    except (OSError, ValueError) as error:
        print(f'Installation failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())

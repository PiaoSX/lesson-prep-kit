# High School Lesson Preparation and Problem-Solving Method Library

[中文](README.md) | English

An AI Agent skill and method library for teaching mathematics, physics, chemistry, and biology at the Chinese senior high school level, with a focus on one-to-one tutoring, worked solutions, and reusable problem-solving methods.

The skill describes how to research sources, check solutions, prepare teaching materials, and maintain method cards. The library stores approaches with their assumptions, worked examples, and verification status. When solving a problem, identify its conditions and the student's prerequisites before selecting and checking a method.

## What you can use it for

| Task | Main output |
| --- | --- |
| Lesson preparation, revision, and worksheet design | Learning objectives, a teaching sequence, a shared question list, teacher notes with solutions, and a matching student worksheet |
| Worked solutions, error analysis, and alternative approaches | Derivations, assumptions, checks, common mistakes, and useful alternative solutions |
| Method library maintenance | Methods extracted from user suggestions, specified PDFs, or reference solutions, with verification, deduplication, corrections, and index updates |
| Local teaching-material search | A file index, candidate materials, and changes since the previous scan |
| Topic-based resource collection | Online resources collected within the user's permissions, with source, reading-scope, and download records |

Chinese is the default output language. Lesson preparation normally produces teacher notes and a student worksheet with matching, stable question IDs. The teacher version includes answers and the necessary reasoning for each question; the student version omits answers by default. A single-problem explanation or library update does not require a full lesson plan.

## Core files

Both skills are stored under `skills/`. The lesson-preparation skill starts with `SKILL.md` and includes its method library. Preserve the internal directory structure when installing the skills.

```text
skills/
├── high-school-lesson-prep/
│   ├── SKILL.md
│   ├── agents/
│   ├── workflows/
│   ├── references/
│   │   └── method-library/
│   └── scripts/question_bank.py
└── chinese-material-search/
    ├── SKILL.md
    ├── agents/
    └── references/
```

The method library starts with [index.md](skills/high-school-lesson-prep/references/method-library/index.md) (main index). Subject cards are stored in `mathematics.md` (mathematics), `physics.md` (physics), `chemistry.md` (chemistry), and `biology.md` (biology). `methods.json` stores method records and verification status. Packaged file locations in JSON are relative to the library root; internal Markdown links use relative paths and stable method-ID anchors.

This package contains the four subject libraries and their index. It excludes attribution and acquisition records, reading logs, chapter extraction folders, candidate notes, and original textbooks. All packaged filenames are in English; method content remains primarily in Chinese.

## Install with pip

Use Python 3.9 or later with pip. Download and extract the repository, then open PowerShell in the directory containing `pyproject.toml`:

```powershell
python -m pip install .
```

pip prepares the build dependencies declared in `pyproject.toml`; the first installation may require internet access. The skill installer itself uses only the Python standard library.

### Preview and install for Codex

Review the installation plan, then install:

```powershell
python -m lesson_prep_kit.install --dry-run
python -m lesson_prep_kit.install
```

The default destination is `~/.codex/skills`. If `CODEX_HOME` is set, the installer uses its `skills` subdirectory. It copies the lesson-preparation skill, its bundled method library, and the companion Chinese resource-search skill, keeping both skills side by side. A dry run writes no files. Existing skills with matching names are left unchanged.

If your Python scripts directory is on PATH, you can also use the shorter `lesson-prep-install` command with the same arguments.

### Choose another skills directory

For example, install to a shared skills directory:

```powershell
python -m lesson_prep_kit.install --target "$env:USERPROFILE\.agents\skills" --dry-run
python -m lesson_prep_kit.install --target "$env:USERPROFILE\.agents\skills"
```

You can replace `--target` with another skills directory supported by your Agent. The installer copies only the two bundled skills and leaves Agent settings unchanged. It reports conflicting files, links, or incomplete existing skill directories and preserves their contents. If installation fails, it removes skill directories created by that attempt.

In the output, `installed` means files were copied and checked, `skipped-existing` means an existing directory was retained, and `would-install` describes a planned copy during a dry run.

### After installation

Start a new Agent session and confirm that it can read `SKILL.md` and `references/method-library/index.md`. Try a problem with a known answer. A successful file copy does not establish that the host has loaded the skill.

To scan your own external teaching materials, choose a material directory and a separate state directory. You can use the bundled library and user-provided problems without an external collection. Online search, PDF reading, OCR, and Word/PDF export depend on tools provided by the host. Downloads, cloud-drive operations, and library writes follow the current user's permissions and chosen locations.

## Example requests

### Prepare a lesson

> Use high-school-lesson-prep to prepare a 60-minute lesson on conservation of momentum for a Grade 11 student. The student can draw force diagrams for individual objects but struggles to choose a system and check conservation conditions. Use only the local teaching materials I specify, with no online search or downloads this time. Produce teacher notes and a student worksheet with matching question IDs.

### Explain a problem and compare approaches

> Use high-school-lesson-prep to explain the problem I provide. Start with the given conditions and the key decisions, then give a complete solution. If another approach fits this student's background, compare its assumptions and when to teach it. Avoid counting a rearrangement of the same derivation as a separate method.

### Add or correct methods

> Use high-school-lesson-prep to extract physics methods from pages 12–18 of the PDF I specify. Check for existing methods first and retain source page numbers. For each new method, include assumptions, a worked example, and a failure case. Mark anything unresolved as a candidate. Update the subject cards, main index, and JSON records, then report the actual changes.

You can also describe the task without naming the skill. Automatic selection depends on the host's skill discovery and invocation mechanism.

## Method cards and verification status

Method cards use stable IDs. They record names and aliases, problem-type clues, assumptions, prerequisites, key steps, worked examples and checks, failure cases, and verification status.

| Status in the library | Meaning |
| --- | --- |
| 候选待核 — Candidate | A lead has been recorded, but the necessary checks are incomplete |
| 部分核验 — Partially verified | Some principles, steps, or examples have been checked; specific questions remain open |
| 已核验 — Verified within scope | Verification covers the conditions and scope stated in the card |
| 停用 — Disabled | An issue has been found; the affected method or use case is temporarily excluded from recommendations |

Retain each card's detailed verification notes. One worked example, numerical sampling, or agreement with a reference answer does not establish validity for every problem. The library may include competition-level or university extensions; check prerequisites and curriculum scope before teaching them. This English README explains usage; method cards remain primarily in Chinese.

## Local teaching-material index

`scripts/question_bank.py` maintains an incremental file index using paths, file sizes, and modification times. It supports scans and keyword searches over file names and paths. It does not read the full collection, extract individual questions, or deduplicate question content.

The first scan establishes a baseline. Later scans report added, modified, and removed files. File counts are not question counts. Use the script's `--help`, `scan --help`, and `search --help` to inspect arguments. Scans require `--root` and `--state-dir`; searches require the same `--state-dir`. See the [local indexing guide](skills/high-school-lesson-prep/references/local-question-bank.md) for a PowerShell example.

## Updates and corrections

When adding a method, retain its assumptions, worked examples, and verification status. When reporting an error, include the method ID, problem conditions, affected step, and evidence for the correction. Changes to method cards should include consistency checks across subject files, the main index, and JSON records, while preserving existing IDs and verification status.

Before sharing changes, remove student personal information, account credentials, and local runtime caches. Follow the applicable permissions for books, handouts, and web content. A source citation does not grant permission to redistribute the full material.

## License

This project is licensed under the [MIT License](LICENSE). You may use, copy, modify, and distribute it under the terms of that license.
Include the original copyright notice and permission notice in all copies or substantial portions of the project. The project is provided “as is,” without warranty of any kind, express or implied.
Third-party content with separate license notices remains subject to its respective license.

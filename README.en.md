# High School Lesson Preparation and Problem-Solving Method Library

[中文](README.md) | English

An AI Agent skill and method library for teaching mathematics, physics, chemistry, and biology at the Chinese senior high school level, with a focus on one-to-one tutoring, worked solutions, and reusable problem-solving methods.

The skill describes how to research sources, check solutions, prepare teaching materials, and maintain method cards. The library stores approaches with their assumptions, worked examples, and sources. When solving a problem, identify its conditions and the student's prerequisites before selecting and checking a method.

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

The skill folder is named `high-school-lesson-prep`, with `SKILL.md` as its entry point. Preserve the complete folder and its internal directory structure when installing it.

```text
high-school-lesson-prep/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── workflows/
│   ├── prepare-lesson.md
│   ├── solve-question.md
│   └── maintain-methods.md
├── references/
└── scripts/
    └── question_bank.py
```

The method library starts with `总索引.md` (main index). Subject cards are stored in `数学.md` (mathematics), `物理.md` (physics), `化学.md` (chemistry), and `生物.md` (biology). `方法条目与来源.json` stores method records and provenance. You may keep the library outside the skill folder, provided that the skill's references point to its actual location.

## Installation and initial setup

1. Download or clone the repository. Place the complete `high-school-lesson-prep` folder in a skill directory supported by your Agent. Follow your Agent's documentation for its installation path and loading mechanism.
2. Place the method library in a location you intend to maintain. Check the library path, teaching-material directory, and script paths referenced by the skill.
3. In a new session, confirm that your Agent can read `SKILL.md`, the relevant workflows, and the library index. Try a problem with a known solution to check the workflow.
4. For online resource collection, configure the host's search, browsing, and file tools. The current online workflows reference the `chinese-material-search` skill. Install that dependency separately, or adapt the workflows to the search tools available in your host.

**The current maintained version still contains paths and permission statements specific to the author's computer.** Before using it elsewhere, review `I:/卷/题`, `I:/卷/题/解题方法库`, and absolute Python and script paths. Replace them with locations appropriate to your environment. The author's previous permissions for downloads, cloud-drive operations, and file writes do not apply to other users; define your own permitted actions and save locations first.

You need an AI Agent that can read files and follow skill instructions. Running `question_bank.py` requires Python 3; the script uses the standard library. PDF reading, OCR, online search, symbolic computation, and Word/PDF export depend on tools provided by the host. Installing the skill does not add those capabilities.

## Example requests

### Prepare a lesson

> Use high-school-lesson-prep to prepare a 60-minute lesson on conservation of momentum for a Grade 11 student. The student can draw force diagrams for individual objects but struggles to choose a system and check conservation conditions. Use only the local teaching materials I specify, with no online search or downloads this time. Produce teacher notes and a student worksheet with matching question IDs.

### Explain a problem and compare approaches

> Use high-school-lesson-prep to explain the problem I provide. Start with the given conditions and the key decisions, then give a complete solution. If another approach fits this student's background, compare its assumptions and when to teach it. Avoid counting a rearrangement of the same derivation as a separate method.

### Add or correct methods

> Use high-school-lesson-prep to extract physics methods from pages 12–18 of the PDF I specify. Check for existing methods first and retain source page numbers. For each new method, include assumptions, a worked example, and a failure case. Mark anything unresolved as a candidate. Update the subject cards, main index, and JSON records, then report the actual changes.

You can also describe the task without naming the skill. Automatic selection depends on the host's skill discovery and invocation mechanism.

## Method cards and verification status

Method cards use stable IDs. They record names and aliases, problem-type clues, assumptions, prerequisites, key steps, worked examples and checks, failure cases, sources, and the portions actually read.

| Status in the library | Meaning |
| --- | --- |
| 候选待核 — Candidate | A lead has been recorded, but the necessary checks are incomplete |
| 部分核验 — Partially verified | Some principles, steps, or examples have been checked; specific questions remain open |
| 已核验 — Verified within scope | Verification covers the conditions and scope stated in the card |
| 停用 — Disabled | An issue has been found; the affected method or use case is temporarily excluded from recommendations |

Retain each card's detailed verification notes. One worked example, numerical sampling, or agreement with a reference answer does not establish validity for every problem. The library may include competition-level or university extensions; check prerequisites and curriculum scope before teaching them. This English README explains usage; method cards remain primarily in Chinese.

## Local teaching-material index

`scripts/question_bank.py` maintains an incremental file index using paths, file sizes, and modification times. It supports scans and keyword searches over file names and paths. It does not read the full collection, extract individual questions, or deduplicate question content.

The first scan establishes a baseline. Later scans report added, modified, and removed files. File counts are not question counts. Use the script's `--help`, `scan --help`, and `search --help` to inspect available arguments, and explicitly set your material and state directories.

## Updates and corrections

When adding a method, retain its source and actual reading scope. When reporting an error, include the method ID, problem conditions, affected step, and evidence for the correction. Changes to method cards should include consistency checks across subject files, the main index, and JSON records, while preserving existing IDs, source history, and verification status.

Before sharing changes, remove student personal information, account credentials, and local runtime caches. Follow the applicable permissions for books, handouts, and web content. A source citation does not grant permission to redistribute the full material.

## License

Use and redistribution are governed by the repository's `LICENSE`. If no license is provided, contact the author to confirm permission. Third-party materials and excerpts retain their respective rights and licensing terms.

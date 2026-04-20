# Usage Guide

This guide explains how to install, initialize, and operate LLM Wiki Agent. [AGENTS.md](../AGENTS.md) is the agent entrypoint. [WIKI.md](../WIKI.md) is the canonical operating guide.

For Chinese, see [usage.zh-CN.md](usage.zh-CN.md).

## 1. Use Cases

LLM Wiki Agent is useful when you want to turn accumulated source material into a maintainable Markdown wiki:

- Research notes, articles, papers, and clipped web pages.
- Project knowledge, decisions, meeting notes, and technical investigations.
- Personal knowledge bases, reading notes, and topic archives.
- Source-backed questions where traceability, claims, uncertainty, and contradictions matter.

It is not meant to replace one-off chat. The value of this package is durable accumulation: sources, judgments, summaries, contradictions, and follow-up questions are preserved as reusable wiki knowledge.

## 2. Requirements

The current package depends on:

- [uv](https://docs.astral.sh/uv/) for Python environment management. The init scripts run `uv sync`.
- PowerShell for [scripts/init.ps1](../scripts/init.ps1) on Windows.
- Bash for [scripts/init.sh](../scripts/init.sh) on macOS or Linux.
- Obsidian, or any editor that can browse Markdown files.
- An agent that can read repository instruction files, such as Codex, Claude Code, Gemini CLI, OpenCode, or a similar tool.

The initialization script checks for `uv`. If `uv` is not available, it tries the official installer. If installation fails, install `uv` manually and run the script again.

## 3. Install

Enter the repository directory:

```powershell
cd llm-wiki-agent
```

Initialize the current directory on Windows:

```powershell
.\scripts\init.ps1 -VaultRoot .
```

On macOS or Linux:

```sh
./scripts/init.sh -VaultRoot .
```

Or create the wiki structure inside a separate Obsidian vault:

```powershell
.\scripts\init.ps1 -VaultRoot "C:\path\to\your\vault"
```

```sh
./scripts/init.sh -VaultRoot "/path/to/your/vault"
```

The script does two things:

1. Runs `uv sync` in the agent package directory to create or update `.venv/`.
2. Creates `inbox/`, `raw/`, `intake/`, `wiki/`, and the other workflow directories under `-VaultRoot`.

`.venv/` is local runtime state and should not be committed.

## 4. Directory Structure

After initialization, the wiki structure is:

```text
.
├── inbox/
├── raw/
│   ├── digested/
│   ├── needs-review/
│   ├── ignored/
│   └── unsupported/
├── intake/
│   ├── tmp/
│   ├── processed/
│   └── logs/
├── reviews/
│   ├── source-review/
│   └── reflection/
├── logs/
│   └── wiki.md
├── questions/
├── artifacts/
└── wiki/
    ├── home.md
    ├── index.md
    ├── overview.md
    ├── sources/
    ├── entities/
    ├── concepts/
    ├── claims/
    └── syntheses/
```

Core responsibilities:

| Directory | Responsibility |
| --- | --- |
| `inbox/` | Only entrypoint for user-submitted original files. |
| `raw/` | Final state area for original files. It does not store agent-generated Markdown. |
| `intake/tmp/` | Temporary Markdown after conversion and before source review. |
| `intake/processed/` | Accepted Markdown ready for wiki ingestion. |
| `reviews/` | Source review and discussion reflection records. |
| `wiki/` | Durable knowledge pages. |
| `questions/` | Open questions and investigation trails. |
| `artifacts/` | Reports, briefs, drafts, templates, and other user-facing deliverables. |

## 5. First File Intake

Put an original file into `inbox/`:

```text
inbox/
└── example.md
```

Ask the agent:

```text
Process the files in inbox/ according to AGENTS.md and WIKI.md.
```

The agent should:

1. Read [AGENTS.md](../AGENTS.md) and route the task to Add Knowledge.
2. Read [WIKI.md](../WIKI.md) and follow the intake and source review rules.
3. Inspect complete filenames, file types, sizes, and readability.
4. Convert or normalize processable content into `intake/tmp/YYYY-MM-DD/source-slug/source.md`.
5. Run Source Review Gate on the temporary Markdown.
6. Move the original file to `raw/digested/`, `raw/needs-review/`, `raw/ignored/`, or `raw/unsupported/`.
7. Promote only `digested` content into `intake/processed/` and update `wiki/`.
8. Update `reviews/source-review/`, `intake/logs/`, `wiki/index.md`, and `logs/wiki.md`.

## 6. Source Review Gate

Source Review Gate decides whether a source deserves to enter the wiki.

| Outcome | Raw destination | Next action |
| --- | --- | --- |
| `digested` | `raw/digested/` | Promote to `intake/processed/`, create a source card, and update the wiki. |
| `needs-review` | `raw/needs-review/` | Record the review question. Do not update the wiki yet. |
| `ignored` | `raw/ignored/` | Record the reason. Do not update the wiki. |
| `unsupported` | `raw/unsupported/` | Record the blocker. Do not update the wiki. |

A successful converter run does not mean the source is accepted. Empty, garbled, truncated, structurally broken, or image-dependent content should become `needs-review` or `unsupported`.

## 7. Text-First Boundary

This package is text-first:

- Markdown, HTML, PDF, Word, PowerPoint, Excel, CSV, JSON, and XML should become reviewable Markdown before ingestion.
- Images, scans, screenshots, and audio may remain preserved original sources, but they are not first-class wiki content by default.
- If important information depends on unprocessed images, scans, screenshots, or audio, move the original to `raw/needs-review/` and record the missing processing step.
- Do not create attachment asset directories, copy images into wiki pages, or add image-reference schemes unless image handling is explicitly added.

## 8. Use Existing Knowledge

Ask the agent:

```text
What does the wiki say about <topic>?
```

The agent should start from:

1. `wiki/index.md`
2. `wiki/overview.md`
3. Relevant pages under `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `wiki/claims/`, and `wiki/syntheses/`
4. `questions/` and `artifacts/` when prior investigations or deliverables matter

Reports, briefs, outlines, drafts, templates, and comparison tables should be written to `artifacts/`.

## 9. Reflect Discussion Knowledge

Use Reflect for durable discussion-derived knowledge:

- Confirmed user preferences.
- Workflow rules.
- Architecture judgments.
- Reusable conclusions.
- Confirmed concept relationships or research questions.

Unless the user explicitly asks for reflection, the agent should propose the small set of items to preserve and wait for confirmation. Confirmed discussion records are written to `reviews/reflection/YYYY-MM-DD.md`.

## 10. Maintain the Wiki

Useful maintenance requests:

```text
health-check the wiki
find broken links
find stale claims
clean up duplicates
check claims without sources
```

The agent may directly fix mechanical issues. For interpretation, merge, deletion, or source-judgment changes, it should propose the resolution first.

## 11. FAQ

### What if uv is missing?

Run the initialization script first. If installation fails, install `uv` manually and rerun:

```powershell
.\scripts\init.ps1 -VaultRoot .
```

### What if a file is already in raw/?

New user-submitted originals should enter through `inbox/`. `raw/` is a post-review state area, not the intake entrypoint.

### Why did a file become needs-review?

`needs-review` means the file may be valuable, but the agent cannot safely make a final decision yet. Common causes include large files, poor conversion quality, missing image content, unclear source scope, archives needing member selection, or user judgment being required.

### Can converted Markdown go straight into wiki/?

No. Converted Markdown first goes to `intake/tmp/`, then Source Review Gate. Only accepted material goes to `intake/processed/` and then into `wiki/`.

### Should personal wiki content be committed to GitHub?

For a public package repository, do not commit personal `inbox/`, `raw/`, `intake/`, `wiki/`, `logs/`, `questions/`, or `artifacts/` content. The default [.gitignore](../.gitignore) ignores these local runtime directories.

## 12. Recommended Habits

- Process sources in small batches and check one intake cycle before scaling up.
- For large files, ask the agent to inspect metadata, headings, page counts, line counts, or chunk indexes first.
- Preserve counterevidence and uncertainty for disputed claims.
- Run Maintain Wiki periodically for broken links, duplicates, unsourced claims, and stale content.
- Put user-facing deliverables in `artifacts/` and durable knowledge in `wiki/`.

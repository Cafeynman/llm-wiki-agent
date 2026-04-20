# LLM Wiki Agent

This package uses one shared wiki operating guide:

```text
WIKI.md
```

## Runtime Requirement

Use `uv run` for Python commands from the project root.
Do not call `python` or `pip` directly for project tasks unless the user explicitly asks. Python version is defined in `pyproject.toml`.

Before handling any wiki task, read and follow `WIKI.md`.

## Replacement Rule

When a user gives a new direction that replaces a prior plan, replace the old plan completely instead of patching around it: define the single new source of truth, remove old wording and workflows, scan the target files for stale terms, and finish only when the old terms are gone.

## Package Rules

1. Keep package files, runtime configuration, helper scripts, and local skills inside the project root.
2. Keep the local uv virtual environment at `.venv/` when used, and do not commit it.
3. Prefer existing package skills under `skills/` before creating any new skill.
4. Use `wiki/home.md` as the human-facing wiki home.
5. Use `wiki/index.md` as the structured catalog.
6. Use `logs/wiki.md` as the operation history.
7. Put user-facing deliverables in `artifacts/`.
8. Track open investigation questions in `questions/`.
9. Use `inbox/` as the entry point for user-submitted original files.
10. Preserve raw source traceability and do not edit original files under `raw/` unless the user explicitly asks.
11. Treat the package as text-first: source material must become reviewable Markdown before it enters `intake/processed/` or `wiki/`. Attachments and images may remain part of the preserved original source, but they are not first-class wiki content unless the user explicitly asks for image handling.

## Obsidian Markdown

Use Obsidian wikilinks for internal pages. In normal Markdown text, use `[[path/to/page|Alias]]`. Inside Markdown table cells, escape the alias separator so the table parser does not split the cell: `[[path/to/page\|Alias]]`. Keep the whole wikilink inside one cell, close it with `]]` before the next table delimiter, and verify each table row has the same number of unescaped `|` separators.

## Obsidian Frontmatter Properties

When writing Obsidian frontmatter property values, wrap strings containing `"` in `'`, or wrap strings containing `'` in `"`, and escape required special characters to avoid Obsidian `Invalid properties` errors.

## MarkItDown Output Names

When using MarkItDown to generate Markdown from an original file, the output directory name and `.md` filename must preserve the original file's base filename. Except for changing the extension to `.md`, do not replace, delete, transcode, URL encode, change case, or slugify any character.

## Current Tool Limits

This package currently uses MarkItDown as a text-first converter. Remove inline `data:image/...;base64,...` image links from converted Markdown; they are dead links for this wiki. Do not OCR, describe images, copy attachments into wiki pages, or transcribe audio by default. If Word/PDF/PPT/image/audio content depends on figures, scans, screenshots, attachments, or audio, move the original to `raw/needs-review/` and record the missing non-text processing step. Keep `WIKI.md` tool-agnostic; record current converter limitations here.

## Workflow Router

Route requests to one of the three workflows in `WIKI.md`.

Use `Add Knowledge` when the user asks to review sources, intake files, process raw material, ingest a source, extract claims, reflect on a discussion, or file knowledge back into the wiki.

Use `Use Knowledge` when the user asks what the wiki says, asks for evidence or counterarguments, requests a synthesis, or wants an artifact such as a report, brief, outline, draft, template, or comparison table.

Use `Maintain Wiki` when the user asks for lint, cleanup, health check, broken link repair, duplicate detection, stale claim review, or consistency maintenance.

When a request could fit multiple workflows, start with the smallest workflow that can produce the requested result, then continue only if the task requires it.

## Large Sources

For large files, large converted Markdown, archives, tables, slide decks, OCR-heavy documents, or noisy sources, follow the `Large File and Context Budget Policy` in `WIKI.md`. Do not load large sources into context in one pass.

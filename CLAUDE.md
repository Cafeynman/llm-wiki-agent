# LLM Wiki Agent

This package uses one shared wiki operating guide:

```text
WIKI.md
```

## Project Profile

Read `PROJECT.md` for the configurable project context: current subject, goal, audience, scope, terminology, wiki structure requirements, classification preferences, naming preferences, project-specific rules, constraints, and open questions.

On the first project-context interaction, if `PROJECT.md` is missing, blank, or still only a template with no confirmed project context, clarify the current project context with the user and write the confirmed context to `PROJECT.md` before making project-specific assumptions. Fields in `PROJECT.md` are optional unless required for the current task; do not block on blank optional fields, and ask only when the task depends on a missing value.

Treat `PROJECT.md` as the changeable context layer and the single place for project-specific personalization, including special wiki structure requirements, category schemes, naming preferences, and project-specific rules. Do not use it for stable wiki operating rules, runtime commands, repository workflow rules, or the stable wiki contract in `WIKI.md`.

## Runtime Requirement

Use `uv run` for Python commands from the project root.
Do not call `python` or `pip` directly for project tasks unless the user explicitly asks. Python version is defined in `pyproject.toml`.
When a task depends on project-local environment variables, prefer `uv run --env-file .env` from the project root, or set `UV_ENV_FILE=.env` in the current shell for repeated `uv run` commands.

Before handling any wiki task, read and follow `WIKI.md`.

## Replacement Rule

When a user gives a new direction that replaces a prior plan, replace the old plan completely instead of patching around it: define the single new source of truth, remove old wording and workflows, scan the target files for stale terms, and finish only when the old terms are gone.

## Document Ownership

Keep `WIKI.md` focused on wiki operating rules, knowledge workflows, intake, ingest, traceability, and maintenance.

Repository-level workflow instructions, agent behavior rules, runtime usage guidance, setup guidance, and usage-document routing belong in `AGENTS.md` or the relevant docs under `docs/`, not in `WIKI.md`, unless they are part of the wiki operating contract itself.

Keep `WIKI.md`, `AGENTS.md`, and other agent entrypoint files stable and replaceable. Project-specific preferences and requirements belong in `PROJECT.md`, not in `WIKI.md` or agent entrypoint files.

## Package Rules

1. Keep package files, runtime configuration, helper scripts, and local skills inside the project root.
2. Keep the local uv virtual environment at `.venv/` when used, and do not commit it.
3. Put all temporary files and one-off working scripts under `tmp/` to keep the project workspace clean.
4. Prefer existing package skills under `skills/` before creating any new skill.
5. Use `wiki/home.md` as the human-facing wiki home.
6. Use `wiki/index.md` as the structured catalog.
7. Use `logs/wiki.md` as the operation history.
8. Put user-facing deliverables in `artifacts/`.
9. Track open investigation questions in `questions/`.
10. Use `inbox/` as the entry point for user-submitted original files.
11. Preserve raw source traceability and do not edit original files under `raw/` unless the user explicitly asks.
12. Treat the package as text-first: source material must become reviewable Markdown before it enters `intake/processed/` or `wiki/`. Attachments and images may remain part of the preserved original source, but they are not first-class wiki content unless the user explicitly asks for image handling.

## Obsidian Markdown

Use Obsidian wikilinks for internal pages. In normal Markdown text, use `[[path/to/page|Alias]]`. Inside Markdown table cells, escape the alias separator so the table parser does not split the cell: `[[path/to/page\|Alias]]`. Keep the whole wikilink inside one cell, close it with `]]` before the next table delimiter, and verify each table row has the same number of unescaped `|` separators.

Traceability sections in Markdown must use Obsidian wikilinks for vault-internal files and notes. Plain code-formatted paths may be used in YAML frontmatter or command examples, but not as the primary traceability links in normal Markdown text.

## Obsidian Frontmatter Properties

When writing Obsidian frontmatter property values, wrap strings containing `"` in `'`, or wrap strings containing `'` in `"`, and escape required special characters to avoid Obsidian `Invalid properties` errors.

## Intake Output Names

When generating intake Markdown from an original file, including MarkItDown, manual normalization, repaired document extraction, or any other converter, the intake directory name must preserve the original file's base filename and source language. Except for removing the extension, do not replace, delete, transcode, URL encode, change case, translate, romanize, or slugify any character.

Use the same source-language naming rule for `wiki/sources/` source cards. Do not translate a source title into another language or slug unless the user explicitly asks for that naming scheme.

## Current Tool Limits

This package currently uses MarkItDown as a text-first converter. Remove inline `data:image/...;base64,...` image links from converted Markdown; they are dead links for this wiki. Do not OCR, describe images, copy attachments into wiki pages, or transcribe audio by default. If Word/PDF/PPT/image/audio content depends on figures, scans, screenshots, attachments, or audio, move the original to `raw/needs-review/` and record the missing non-text processing step. If OCR is explicitly enabled for a task, read `docs/markitdown-ocr.md` before invoking OCR-related commands. When `.env` defines `MARKITDOWN_OCR_MODEL`, use that value as the default OCR model and pass it explicitly as `--llm-model`; if it is missing, ask the user before proceeding with OCR. Keep `WIKI.md` tool-agnostic; record current converter limitations here.

## Workflow Router

Route requests to one of the three workflows in `WIKI.md`.

Use `Add Knowledge` when the user asks to review sources, intake files, process raw material, ingest a source, extract claims, reflect on a discussion, or file knowledge back into the wiki.

Use `Use Knowledge` when the user asks what the wiki says, asks for evidence or counterarguments, requests a synthesis, or wants an artifact such as a report, brief, outline, draft, template, or comparison table.

Use `Maintain Wiki` when the user asks for lint, cleanup, health check, broken link repair, duplicate detection, stale claim review, or consistency maintenance.

When a request could fit multiple workflows, start with the smallest workflow that can produce the requested result, then continue only if the task requires it.

## Large Sources

For large files, large converted Markdown, archives, tables, slide decks, OCR-heavy documents, or noisy sources, follow the `Large File and Context Budget Policy` in `WIKI.md`. Do not load large sources into context in one pass.

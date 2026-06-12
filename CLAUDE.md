# LLM Wiki Agent

`AGENTS.md` is the canonical agent entrypoint for this repository. This file is a Claude adapter only. Read and follow `AGENTS.md` first; if this file and `AGENTS.md` conflict, `AGENTS.md` wins. Do not add durable project rules only to this file.

This package uses one shared wiki operating guide:

```text
WIKI.md
```

## Project Profile

Read `PROJECT.md` for the configurable project context: current subject, goal, audience, scope, terminology, wiki structure requirements, classification preferences, naming preferences, project-specific rules, constraints, and open questions.

On the first project-context interaction, if `PROJECT.md` is missing, blank, or still only a template with no confirmed project context, clarify the current project context with the user and write the confirmed context to `PROJECT.md` before making project-specific assumptions. Fields in `PROJECT.md` are optional unless required for the current task; do not block on blank optional fields, and ask only when the task depends on a missing value.

During that first project-context confirmation, ask whether the user wants to configure MinerU credentials and whether MinerU should be preferred when it is available. Do not ask for or record the secret value itself; direct the user to copy `.env.example` to `.env` and fill `MINERU_TOKEN` locally. If the user prefers MinerU when available, set `Default provider for document: mineru` and `Prefer MinerU when available: yes` in `PROJECT.md`; otherwise keep MarkItDown as the document default and set `Prefer MinerU when available: no`.

Treat `PROJECT.md` as the changeable context layer and the single place for project-specific personalization, including special wiki structure requirements, category schemes, naming preferences, and project-specific rules. Do not use it for stable wiki operating rules, runtime commands, repository workflow rules, or the stable wiki contract in `WIKI.md`.

## Runtime Requirement

Use `uv run` for Python commands from the project root.
Do not call `python` or `pip` directly for project tasks unless the user explicitly asks. Python version is defined in `pyproject.toml`.
When a task depends on project-local environment variables, use `uv run --env-file .env` from the project root, or set `UV_ENV_FILE=.env` in the current shell for repeated `uv run` commands.
If a required local variable is missing, stop and ask the user to configure `.env`; do not paste secrets or private service URLs into commands, prompts, manifests, logs, wiki pages, source cards, or project instructions.

Before handling any wiki task, read and follow `WIKI.md`.

## Initialization Requirement

Before the first wiki task in a workspace, check whether the package-managed entrypoint files and runtime structure exist. If `.venv/` or required runtime paths such as `inbox/`, `raw/`, `intake/`, `reviews/`, `logs/`, `questions/`, `artifacts/`, or `wiki/` are missing, run the initialization script from the package root instead of creating directories by hand.

Use `.\scripts\init.ps1 -VaultRoot .` on Windows and `./scripts/init.sh -VaultRoot .` on macOS or Linux.

When the user wants the wiki structure in a separate Obsidian vault, pass that vault path as `-VaultRoot`. The initialization script installs the package-managed agent entrypoint files, local skills, scripts, and docs into that vault, creates `PROJECT.md` there when it is missing, creates missing runtime directories and default wiki files, and runs `uv sync` from the initialized vault root. Existing package-managed files in the target root are replaced by the package copy; workspace-specific preferences belong in `PROJECT.md`.

After external-vault initialization, treat the initialized vault root as the working package root for future agent tasks.

## Skill Source

When using skills for this project, read the skill files from this repository's `.agents/skills/` directory first. Treat `.agents/skills/` as the project-local source of truth for package skills, and do not prefer global or external skill copies unless the user explicitly asks.

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
4. Prefer existing package skills under `.agents/skills/` before creating any new skill.
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

## Source-Derived Text Preservation

Preserve source-derived text exactly as content. Do not delete, replace, romanize, slugify, or otherwise normalize special characters just because a target syntax treats them specially. Encode or quote the value only at the output boundary that needs it, such as YAML frontmatter, Markdown table cells, wikilinks, or command examples.

## Obsidian Frontmatter Properties

Do not write user-, source-, or filename-derived strings as unquoted YAML plain scalars in frontmatter. Write free-text values such as `title`, `aliases`, source names, paths, URLs, and descriptions as double-quoted YAML strings, escaping `\` as `\\` and `"` as `\"`, or use a YAML serializer and verify the emitted frontmatter parses. YAML indicator characters can break syntax or silently change the parsed value depending on position and context, including `:`, `#`, `*`, `&`, `!`, `|`, `>`, `[`, `]`, `{`, `}`, `,`, `?`, `-`, `%`, `@`, `` ` ``, and quotes. Keep only fixed safe tokens such as `type`, `status`, `confidence`, dates, and booleans unquoted.

## Intake Output Names

When generating intake Markdown from an original file, including MarkItDown, manual normalization, repaired document extraction, or any other provider, the intake directory name must preserve the original file's base filename and source language. Except for removing the extension, do not replace, delete, transcode, URL encode, change case, translate, romanize, or slugify any character.

Also preserve the source-relative parent path defined in `WIKI.md` when writing `intake/tmp/`, `intake/processed/`, and `wiki/sources/`. Do not add a date directory under `intake/tmp/` or `intake/processed/`; processing dates belong in manifests, logs, and review records.

Use the same source-relative parent and source-language naming rule for `wiki/sources/` source cards. Do not translate a source title into another language or slug unless the user explicitly asks for that naming scheme.

## Source Extraction Providers

Before source extraction, use the local `.agents/skills/source-extraction/` skill. Document, webpage, image, audio, and video extraction choices belong in `PROJECT.md`, not in `AGENTS.md` or `CLAUDE.md`.

OCR, image extraction, audio transcription, and video frame/audio extraction must follow `PROJECT.md`; do not enable them automatically. Real API keys, tokens, and private service URLs belong only in the local project-root `.env` file and must not be written into project instructions, manifests, logs, wiki pages, source cards, or skill files. Provider setup documents may name required environment variables, but local values must stay in `.env`.

## Workflow Router

Route requests to one of the three workflows in `WIKI.md`.

Use `Add Knowledge` when the user asks to review sources, intake files, process raw material, ingest a source, extract claims, reflect on a discussion, or file knowledge back into the wiki.

Use `Use Knowledge` when the user asks what the wiki says, asks for evidence or counterarguments, requests a synthesis, or wants an artifact such as a report, brief, outline, draft, template, or comparison table.

Use `Maintain Wiki` when the user asks for lint, cleanup, health check, broken link repair, duplicate detection, stale claim review, or consistency maintenance.

When a request could fit multiple workflows, start with the smallest workflow that can produce the requested result, then continue only if the task requires it.

## Large Sources

For large files, large extracted Markdown, archives, tables, slide decks, OCR-heavy documents, or noisy sources, follow the `Large File and Context Budget Policy` in `WIKI.md`. Do not load large sources into context in one pass.

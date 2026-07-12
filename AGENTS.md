# LLM Wiki Agent

This package uses one shared wiki operating guide:

```text
WIKI.md
```

## Project Profile

Read `PROJECT.md` for configurable project context. If it is missing, blank, or still only a template when project context matters, clarify the needed context and write only confirmed values there.

When confirming project context fields such as theme, goal, audience, scope, terminology, wiki structure, classification, naming, project-specific rules, constraints, and open questions, ask open-ended questions. Do not present preset choices, inferred defaults, or suggested category schemes for those fields unless the user asks for examples.

During first project-context confirmation, ask whether the user wants to configure MinerU credentials, which MinerU profile should be used for API mode, and whether MinerU should be preferred when available. Record only non-secret choices in `PROJECT.md`; direct the user to copy `.env.example` to `.env` and fill only the variables required by the selected profile.

Use yes/no questions or short choices only for bounded operational preferences such as whether to configure MinerU, which MinerU profile to use for API mode, whether to prefer MinerU when available, or whether to enable OCR, transcription, or frame OCR.

`PROJECT.md` is the only place for project-specific personalization. Do not use it for stable wiki rules, runtime commands, repository workflow rules, or the stable wiki contract in `WIKI.md`.

## Scenario Packages

Reusable scenario packages live under `scenarios/`. They are optional initialization guides for specialized workspaces, not active project configuration. Use a scenario package only when the user explicitly asks to initialize or adapt the workspace from a named scenario.

When applying a scenario package:

1. Read `scenarios/<name>/README.md` first.
2. Use `scenarios/<name>/PROJECT.template.md` only to confirm and update project-specific fields in the root `PROJECT.md`.
3. Use `scenarios/<name>/starter-pages.md` only to create the smallest useful initial pages for the confirmed project context.
4. Do not modify `WIKI.md` or `AGENTS.md` as part of scenario initialization.
5. Do not treat scenario files as active wiki knowledge or runtime state.
6. If a scenario README defines additional files, follow that scenario's stated structure without generalizing it to other scenarios.

## Runtime Requirement

Use `uv run` for Python commands from the project root. Do not call `python` or `pip` directly for project tasks unless the user explicitly asks.

When a task depends on project-local environment variables, use `uv run --env-file .env` or set `UV_ENV_FILE=.env` for repeated commands. If a required local variable is missing, stop and ask the user to configure `.env`; do not paste secrets or private service URLs into commands, prompts, manifests, logs, wiki pages, source cards, or project instructions.

Before handling any wiki task, read and follow `WIKI.md`.

## Initialization Requirement

Before the first wiki task in a workspace, check whether package-managed entrypoint files and runtime structure exist. If `.venv/` or required runtime paths such as `inbox/`, `raw/`, `intake/`, `reviews/`, `logs/`, `questions/`, `artifacts/`, or `wiki/` are missing, run the initialization script from the package root instead of creating directories by hand.

Use `.\scripts\init.ps1 -VaultRoot .` on Windows and `./scripts/init.sh -VaultRoot .` on macOS or Linux.

When the user wants the wiki structure in a separate Obsidian vault, pass that vault path as `-VaultRoot`. After external-vault initialization, treat the initialized vault root as the working package root. Existing package-managed files are replaced by the package copy; workspace-specific preferences belong in `PROJECT.md`.

## Skill Source

When using skills for this project, read the skill files from this repository's `.agents/skills/` directory first. Treat `.agents/skills/` as the project-local source of truth for package skills, and do not prefer global or external skill copies unless the user explicitly asks.

## Delegation Context

When delegating wiki or source-processing work to subagents, Claude Code, AGY, external reviewers, or another runtime, do not assume repository context is inherited. Include the workspace root, the target vault root when different, `AGENTS.md` as the canonical entrypoint, relevant `WIKI.md` contract sections, `PROJECT.md` when naming or extraction preferences matter, relevant local `.agents/skills/` paths, and the source-language naming rule. Do not include secrets, private endpoints, tokens, or credentials in delegated prompts.

## Replacement and Target-State Writing

When the user explicitly gives a new direction that replaces a prior plan, apply it to the affected agent-owned current-state surfaces: operational docs, prompts, workflows, dashboards, queue pages, scenarios, skills, and requested deliverables. Update those surfaces so they describe the confirmed target state directly, and remove stale operational wording that would cause an agent or user to follow the replaced plan.

Do not apply this cleanup to raw sources, preserved source-derived text, quoted material, append-only logs, historical review records, evidence and counterevidence, aliases, lifecycle history, or older claims that remain useful as stale or archived knowledge. Preserve those records and mark their current status when needed.

Prefer direct target-state prose: what the system does, what the user does, and what the final design is. Use negative, contrastive, or corrective phrasing when it states a required constraint, prevents a concrete risk, records source limitations, preserves disagreement, marks superseded knowledge, or answers a user-requested comparison.

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
10. Use `inbox/` as the entry point for user-submitted original files and generated live-URL source captures.
11. Preserve raw source traceability and do not edit lifecycle source artifacts under `raw/` unless the user explicitly asks.
12. Treat the package as text-first: source material must become reviewable Markdown before it enters `intake/processed/` or `wiki/`. Providers may automatically preserve returned attachments and images under the same intake folder as `source.md`; promote or delete them with that folder. Passive preservation does not make them first-class wiki content or authorize OCR, visual interpretation, or image-derived knowledge.

## Obsidian Markdown and Frontmatter

Use the local `.agents/skills/obsidian-markdown/` skill for Obsidian syntax, table-cell wikilinks, embeds, callouts, and properties. Traceability links to vault-internal files and notes must use Obsidian wikilinks.

Frontmatter `sources:` entries for vault-internal files must be quoted wikilink strings such as `"[[raw/digested/source-relative-parent/original-filename.ext]]"` or `"[[intake/processed/source-relative-parent/original-source-base-filename/source.md]]"`. Omit `source-relative-parent/` only when the source is directly under the intake root. Free-text values derived from users, sources, filenames, titles, paths, URLs, or descriptions must be quoted or emitted by a YAML serializer; see `.agents/skills/obsidian-markdown/references/PROPERTIES.md`.

Preserve source-derived text exactly as content. Encode or quote values only at the output boundary that needs it, such as YAML frontmatter, Markdown table cells, wikilinks, or command examples.

## Intake Output Names

When generating intake Markdown from an original file, including MarkItDown, manual normalization, repaired document extraction, or any other provider, the intake directory name must preserve the original file's base filename and source language. Except for removing the extension, do not replace, delete, transcode, URL encode, change case, translate, romanize, convert to pinyin, or slugify any character.

Also preserve the source-relative parent path defined in `WIKI.md` when writing `intake/tmp/`, `intake/processed/`, and `wiki/sources/`. Do not add a date directory under `intake/tmp/` or `intake/processed/`; processing dates belong in manifests, logs, and review records.

Use the same source-relative parent and the `WIKI.md` source-language naming rule for `wiki/sources/` source cards. Do not translate, romanize, convert to pinyin, or slugify a source title unless the user explicitly asks for that naming scheme.

For a submitted live URL, follow the deterministic Defuddle source-capture naming rule in `WIKI.md`. The generated URL capture is the lifecycle source artifact for that non-file source and is the sole exception to original-file naming and to the rule that generated Markdown does not enter `raw/`. Do not apply that exception to summaries, normalized provider output, chunks, or user-submitted files.

## Source Extraction Providers

Before source extraction, use the local `.agents/skills/source-extraction/` skill. Document, webpage, image, audio, and video extraction choices belong in `PROJECT.md`, not in `AGENTS.md` or `CLAUDE.md`.

OCR, active image extraction or interpretation, audio transcription, and video frame/audio extraction must follow `PROJECT.md`; do not enable them automatically. Copying images already returned by the selected provider into the same intake folder is passive source preservation and does not require separate approval. Real API keys, tokens, and private service URLs belong only in the local project-root `.env` file and must not be written into project instructions, manifests, logs, wiki pages, source cards, or skill files. Provider setup documents may name required environment variables, but local values must stay in `.env`.

## Workflow Router

Route requests to one of the three workflows in `WIKI.md`.

Use `Add Knowledge` when the user asks to review sources, intake files, process raw material, ingest a source, extract claims, reflect on a discussion, or file knowledge back into the wiki.

Use `Use Knowledge` when the user asks what the wiki says, asks for evidence or counterarguments, requests a synthesis, or wants an artifact such as a report, brief, outline, draft, template, or comparison table.

Use `Maintain Wiki` when the user asks for lint, cleanup, health check, broken link repair, duplicate detection, stale claim review, or consistency maintenance.

When a request could fit multiple workflows, start with the smallest workflow that can produce the requested result, then continue only if the task requires it.

## Wiki Agent Behavior

Work like a careful Obsidian wiki maintainer: prefer small traceable updates, preserve useful existing structure, do not invent facts or citations, mark uncertainty clearly, keep raw originals unmodified, and use the shortest workflow that fully satisfies the user's request.

Update `wiki/index.md` and `logs/wiki.md` whenever wiki content changes. Update `wiki/home.md` only when the wiki purpose, main topics, current artifacts, or major open questions change. Create pages when they improve reuse, traceability, or synthesis, not for every named thing.

## Large Sources

For large, structured, or noisy sources, follow the `Large File and Context Budget Policy` in `WIKI.md`; use `.agents/skills/source-extraction/references/large-source-chunking.md` only for detailed chunking mechanics.

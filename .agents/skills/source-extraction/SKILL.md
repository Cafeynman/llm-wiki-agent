---
name: source-extraction
description: Use whenever processing source material into intake Markdown, including inbox intake, document extraction, webpage extraction, OCR decisions, MinerU or MarkItDown selection, Defuddle extraction, or audio/video transcription policy checks. This skill defines source kinds, provider selection, provider safety rules, and the required output contract before Source Review Gate.
---

# Source Extraction

Use this skill before any wiki intake step that turns original material into reviewable Markdown.

The stable intake contract remains in `WIKI.md`. This skill decides how to choose and operate an extraction provider without letting any provider bypass Source Review Gate.

## Required Reading

1. Read `PROJECT.md` and use the `Source Extraction Preferences` section when present.
2. Read `references/contract.md` before running a provider.
3. Read `references/source-kinds.md` to classify the original material.
4. Read `references/provider-registry.md` to select a provider.
5. Read only the selected provider's `usage.md`; read its `setup.md` only when setup, configuration, missing tools, or API keys are relevant.

## Workflow

1. Classify the original material by source kind.
2. Check `PROJECT.md` for the configured provider or policy for that kind.
3. On the first source-intake interaction for a project, if the relevant `PROJECT.md` preference is blank, missing, or `Preferences status` is `unconfirmed`, ask the user to confirm it before extraction. After confirmation, update `Preferences status` to `confirmed`.
4. If the kind is configured as `unsupported`, move through the normal WIKI intake handling for unsupported material.
5. If the policy is `ask-before-ocr`, `ask-before-transcription`, or `ask-before-transcription-or-frame-ocr`, ask the user before enabling that extraction.
6. Run the provider only against the original source, never against another provider's generated Markdown.
7. Write provider output to `intake/tmp/YYYY-MM-DD/original-source-base-filename/source.md`.
8. Record provider metadata, warnings, and missing content in the intake manifest or review notes.
9. Continue to Source Review Gate. The provider does not decide whether the source is `digested`, `needs-review`, `ignored`, or `unsupported`.

## Security Rules

- Do not write API keys, tokens, session cookies, or private credentials into `PROJECT.md`, `WIKI.md`, `AGENTS.md`, `CLAUDE.md`, manifests, logs, wiki pages, source cards, or skill files.
- Provider setup documents may name required environment variables.
- Agents may check whether required environment variables are present, but must not print, log, or persist their values.
- When a provider needs local secrets, use the project-root `.env` file and run commands from the project root with `uv run --env-file .env ...` when applicable.

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
5. For PDF documents, read `references/pdf-preflight.md` before selecting the document provider.
6. For large, structured, or noisy sources that need chunking, read `references/large-source-chunking.md` before finalizing intake output.
7. Read only the selected provider's `usage.md`; read its `setup.md` only when setup, configuration, missing tools, or API keys are relevant. If the selected provider has REST API guidance, read its API reference only when API mode or provider smoke checks are relevant.

## Workflow

1. Classify the original material by source kind.
2. Check `PROJECT.md` for the configured provider or policy for that kind.
3. On the first source-intake interaction for a project, if the relevant `PROJECT.md` preference is blank, missing, or `Preferences status` is `unconfirmed`, ask the user to confirm it before extraction. For document intake, also ask whether the user wants to configure MinerU credentials and whether MinerU should be preferred when it is available. If the user chooses MinerU as the preferred available provider, set `Default provider for document: mineru` and `Prefer MinerU when available: yes`; if not, keep MarkItDown as the document default and set `Prefer MinerU when available: no`. After confirmation, update `Preferences status` and the non-secret provider preferences in `PROJECT.md`.
4. If the kind is configured as `unsupported`, move through the normal WIKI intake handling for unsupported material.
5. If the policy is `ask-before-ocr`, `ask-before-transcription`, or `ask-before-transcription-or-frame-ocr`, ask the user before enabling that extraction.
6. Run the provider only against the original source, never against another provider's generated Markdown.
7. Write provider output to `intake/tmp/source-relative-parent/original-source-base-filename/source.md`, omitting `source-relative-parent` when the source is directly under the intake root. The `original-source-base-filename` segment preserves the original base filename exactly after removing only the extension; do not slugify, translate, lowercase, URL encode, or simplify it.
8. Record provider metadata, warnings, missing content, and any chunking decisions in the intake manifest or review notes.
9. Continue to Source Review Gate. The provider does not decide whether the source is `digested`, `needs-review`, `ignored`, or `unsupported`.

## Security Rules

- Do not write API keys, tokens, session cookies, or private credentials into `PROJECT.md`, `WIKI.md`, `AGENTS.md`, `CLAUDE.md`, manifests, logs, wiki pages, source cards, or skill files.
- Provider setup documents may name required environment variables.
- Agents may check whether required environment variables are present, but must not print, log, or persist their values.
- When a provider needs local secrets, use the project-root `.env` file and run commands from the project root with `uv run --env-file .env ...` when applicable.
- If a selected provider mode requires a secret and `.env` or the required variable is missing, stop before extraction and ask the user to configure `.env`.
- Keep provider-specific variable names in the provider setup document. Keep project-specific non-secret choices in `PROJECT.md`.

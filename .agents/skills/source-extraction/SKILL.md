---
name: source-extraction
description: Use whenever processing source material into intake Markdown, including inbox intake, document extraction, webpage extraction, OCR decisions, MinerU or MarkItDown selection, Defuddle extraction, or audio/video transcription policy checks. This skill defines source kinds, provider selection, provider safety rules, and the required output contract before Source Review Gate.
---

# Source Extraction

Use this skill before any wiki intake step that turns original material into reviewable Markdown.

`WIKI.md` contains the short lifecycle read at every conversation start. This skill and `references/intake-lifecycle.md` own provider operation and the detailed intake procedure.

## Required Reading

1. Use the `Source Extraction Preferences` already read from `PROJECT.md` at conversation start.
2. Read `references/intake-lifecycle.md` for source movement, review outcomes, cleanup, and accepted intake files.
3. Read `references/source-kinds.md` to classify the submitted material.
4. Read only the selected provider's `usage.md`. Read `provider-registry.md` when the configured provider is missing or an alternative must be selected, and read `contract.md` when changing provider behavior, handling side outputs, reprocessing, credentials, or provider limits.
5. For PDF documents, read `references/pdf-preflight.md` before selecting the document provider.
6. For large, structured, or noisy sources that need chunking, read `references/large-source-chunking.md` before finalizing intake output.
7. Read a provider's `setup.md` only for setup, configuration, missing tools, or credentials. Read an API reference only for that provider's API mode or smoke check.

## Workflow

1. Classify the lifecycle source and read its configured provider or policy from `PROJECT.md`.
2. When the relevant preference is unconfirmed, ask only the bounded provider questions needed for this source, then record the confirmed non-secret choices in `PROJECT.md`.
3. Run required credential or reachability checks for the selected provider profile. Record only status; local values remain in `.env`.
4. Apply the configured approval gate for OCR, transcription, or frame OCR.
5. For a new extraction, run one selected provider against the lifecycle source. Resume useful pending-review output according to `references/intake-lifecycle.md` before deciding to re-extract. Defuddle creates a live URL's first deterministic capture; later intake stages that capture unchanged. Provider output never becomes input to a second provider.
6. Write or stage `source.md` at the path defined by `references/intake-lifecycle.md`, preserving source-derived names and content.
7. For reviewed line-range plans, use `build_chunks.py` as documented in `large-source-chunking.md`; it supports stable semantic paths and explicit image decisions with staged validation. Run `audit_intake_file.py`; resolve hard reviewability failures. When it reports `large_source`, preserve `source.md` prose and order, applying only the explicitly authorized image-markup changes defined in `intake-lifecycle.md`, and follow the chunk construction, audit, warning disposition, and visible reviewed-size decision procedure in `large-source-chunking.md`.
8. Keep provider-returned side outputs with the same temporary intake folder and record warnings, missing content, and relevant audit findings.
9. Continue through the outcome, movement, cleanup, final-path focused lint, and logging steps in `references/intake-lifecycle.md`. The provider does not choose the Source Review Gate outcome. After final placement and ingest when applicable, use the scoped closeout check in that reference; its structural result does not replace source review.

## Security Rules

- Do not write API keys, tokens, session cookies, or private credentials into `PROJECT.md`, `WIKI.md`, agent entrypoint files, manifests, logs, wiki pages, source cards, or skill files.
- Provider setup documents may name required environment variables.
- Agents may check whether required environment variables are present, but must not print, log, or persist their values.
- When a provider needs local secrets, use the project-root `.env` file and run commands from the project root with `uv run --env-file .env ...` when applicable.
- If a selected provider mode requires a secret and `.env` or the required variable is missing, stop before extraction and ask the user to configure `.env`.
- Keep provider-specific variable names in the provider setup document. Keep project-specific non-secret choices in `PROJECT.md`.

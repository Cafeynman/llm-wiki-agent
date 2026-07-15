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
3. On the first source-intake interaction for a project, if the relevant `PROJECT.md` preference is blank, missing, or `Preferences status` is `unconfirmed`, ask the user to confirm it before extraction. For document intake, also ask whether the user wants to configure MinerU credentials, which MinerU profile should be used when API mode is selected, and whether MinerU should be preferred when it is available. These bounded provider questions may use yes/no or short choices, but do not present preset choices for open-ended project context fields such as theme, goal, audience, structure, classification, naming, or project-specific rules. If the user chooses MinerU as the preferred available provider, set `Default provider for document: mineru` and `Prefer MinerU when available: yes`; if not, keep MarkItDown as the document default and set `Prefer MinerU when available: no`. After confirmation, update `Preferences status` and the non-secret provider preferences in `PROJECT.md`.
4. If `PROJECT.md` selects a MinerU profile with credential or reachability requirements, follow that profile's setup and smoke-check instructions before the first extraction in a workspace. Only mark `MinerU credential status` as `confirmed` after the selected profile's check passes; use `not-required` only when the selected profile explicitly needs no credential. If the check fails, stop before extraction, keep the profile or credential status pending or failed, and send the profile's documentation link to the user.
5. If the kind is configured as `unsupported`, move through the normal WIKI intake handling for unsupported material.
6. If the policy is `ask-before-ocr`, `ask-before-transcription`, or `ask-before-transcription-or-frame-ocr`, ask the user before enabling that extraction.
7. Run the provider only against the lifecycle source. For a submitted live URL, use Defuddle once to create the deterministic Markdown source capture under `inbox/web/` required by `WIKI.md`; that capture becomes the lifecycle source artifact. Never feed one provider's extraction output into another provider.
8. For a URL capture or other Markdown source artifact, stage its content unchanged at `intake/tmp/source-relative-parent/original-source-base-filename/source.md`. For other source kinds, write provider output there. Omit `source-relative-parent` when the source is directly under the intake root. Original-file base names remain exact after removing only the extension; the generated URL-capture filename follows the single explicit rule in `WIKI.md`.
9. Run `uv run --no-project .agents/skills/source-extraction/scripts/audit_intake_file.py <source.md>` from the package root against the `source.md` just produced by this intake step. Normal files produce no output. If the script reports `large_source`, read `references/large-source-chunking.md` and create semantic chunks before Source Review Gate when the source has reliable boundaries.
10. When `chunks/` is generated, run `uv run --no-project .agents/skills/source-extraction/scripts/audit_chunks.py <intake-folder>` from the package root before Source Review Gate. Resolve hard errors before promotion, or move through the normal `needs-review` handling in `WIKI.md`; warnings are extraction or chunking caveats for review notes.
11. If a large source has no reliable boundaries, cannot be chunked without breaking tables or continuous arguments, or requires user judgment before choosing a split, move through the normal `needs-review` handling in `WIKI.md`.
12. Keep provider-returned attachments under the same intake folder as `source.md`. Promote or delete them with that folder, and record their paths or disposition in the manifest, source review, or intake log for the final outcome. Passive copying does not authorize OCR or interpretation. Record provider metadata, warnings, missing content, intake file audit alerts, chunk audit warnings, and any chunking decisions in the same durable records. Do not persist normal no-alert audit results.
13. Continue to Source Review Gate. The provider does not decide whether the source is `digested`, `needs-review`, `ignored`, or `unsupported`.

## Security Rules

- Do not write API keys, tokens, session cookies, or private credentials into `PROJECT.md`, `WIKI.md`, agent entrypoint files, manifests, logs, wiki pages, source cards, or skill files.
- Provider setup documents may name required environment variables.
- Agents may check whether required environment variables are present, but must not print, log, or persist their values.
- When a provider needs local secrets, use the project-root `.env` file and run commands from the project root with `uv run --env-file .env ...` when applicable.
- If a selected provider mode requires a secret and `.env` or the required variable is missing, stop before extraction and ask the user to configure `.env`.
- Keep provider-specific variable names in the provider setup document. Keep project-specific non-secret choices in `PROJECT.md`.

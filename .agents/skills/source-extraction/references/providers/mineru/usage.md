# MinerU Usage

Use MinerU when `PROJECT.md` selects `mineru` for documents, when `PROJECT.md` confirms `Prefer MinerU when available: yes`, or when the user explicitly chooses MinerU for complex document parsing.

## Supported Source Kinds

- `document`
- selected scan-heavy or image-like document inputs when OCR/image extraction has been approved

## Profiles and Modes

MinerU is used through API profiles in this package. Use `setup.md` for shared local environment setup.

API profiles live under `profiles/`. Use the active profile recorded in `PROJECT.md`; when no profile is recorded and API mode matters, clarify the intended profile before extraction.

- `profiles/public-api.md`
- `profiles/fastapi.md`

Each profile owns its API route family, documented limits, credential rules, smoke check, and script invocation details. Current API profiles support local file upload only.

## Provider Choice

When both MarkItDown and MinerU are available:

- If `PROJECT.md` confirms `Prefer MinerU when available: yes`, use MinerU for supported document inputs when the required mode is available.
- If that preference is `no` or `unconfirmed`, keep MarkItDown as the ordinary document default and choose MinerU for scanned PDFs, image-heavy PDFs, dense tables, formulas, multi-column academic layouts, or explicit user requests.
- If `PROJECT.md` sets a MinerU profile, follow that profile's setup and invocation contract.
- If a PDF is being processed, run the lightweight PDF preflight before selecting the provider.
- Do not switch from MarkItDown to MinerU as an implicit fallback. Explain the observed issue and confirm the provider change unless `PROJECT.md` already authorizes the MinerU preference.

## Credential Handling

Follow the selected profile's credential requirements. Secret values and private endpoint values belong only in the project-root `.env` file. If a profile requires a credential and the required local variable is missing, stop before extraction and ask the user to configure `.env`. If a profile explicitly needs no credential, record the credential status as not required in project context or review notes. Do not paste tokens or private endpoint URLs into command examples, prompts, manifests, logs, review notes, wiki pages, or source cards.

## Output Handling

- Save the returned Markdown as `<intake-tmp-dir>/source.md`, even when the provider first returns ZIP-based side outputs.
- Record the MinerU profile, batch id or task id, model version, credential status as present or not required, warnings, missing content, and result URLs in the intake manifest or review notes.
- If MinerU returns extra outputs, preserve only what is needed for `source.md` unless the user explicitly asks to keep additional artifacts.
- Follow the selected profile's error handling for file-size, page-count, format, queue, timeout, rate-limit, and parsing failures.
- Do not split PDFs automatically. If the selected mode cannot accept the whole file, ask the user to approve a page-range or section split strategy first.
- If an approved split produces multiple Markdown files, merge them into the original source's `<intake-tmp-dir>/source.md` in page order. Keep per-part Markdown only as traceability side outputs, and record page ranges and part paths in the intake manifest or review notes.

## OCR and Images

Do not enable MinerU OCR or image extraction automatically. If `PROJECT.md` says `ask-before-ocr`, ask the user before setting OCR options such as the active profile's OCR flag.

## Source

MinerU API behavior should be checked against the upstream documentation when changing this provider:

- <https://github.com/opendatalab/MinerU-Ecosystem/tree/main/skills>
- <https://mineru.net/apiManage/docs>

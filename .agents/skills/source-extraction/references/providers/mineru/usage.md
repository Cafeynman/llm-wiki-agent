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
- Treat exit code `0` as “every requested item produced a current non-empty `source.md`.” `needs_review: true` may accompany exit `0`; review warnings do not make a usable extraction a command failure.
- Record the MinerU profile, batch id or task id, model version, credential status as present or not required, warnings, missing content, and result URLs in the intake manifest or review notes.
- Preserve returned source images under the same intake folder as `source.md`. Promote or delete them with that folder and record their paths or disposition. Keep other provider artifacts only when they are required for traceability or the user explicitly asks.
- Follow the selected profile's error handling for file-size, page-count, format, queue, timeout, rate-limit, and parsing failures.
- Do not split PDFs automatically. If the selected mode cannot accept the whole file, ask the user to approve a page-range or section split strategy first.
- If an approved split produces multiple Markdown files, merge them into the original source's `<intake-tmp-dir>/source.md` in page order. Keep per-part Markdown only as traceability side outputs, and record page ranges and part paths in the intake manifest or review notes.

## OCR and Images

Do not enable MinerU OCR, image analysis, or an option that actively requests image extraction automatically. If `PROJECT.md` says `ask-before-ocr`, ask the user before setting those options. Images already present in the selected provider's returned package may be copied automatically as passive source attachments; copying does not authorize OCR or interpretation.

## Source

MinerU API behavior should be checked against the upstream documentation when changing this provider:

- <https://github.com/opendatalab/MinerU-Ecosystem/tree/main/skills>
- <https://mineru.net/apiManage/docs>

## Safe Reruns and Publication

Both API profiles decode into a unique sibling staging directory. A non-empty
Markdown result is published to the existing public output path only after
extraction succeeds. Each source's `result.json` records `output_owner` and the
exact `owned_files` with content hashes; batch diagnostics and root response
attachments (`response.json`, `batch-result.zip`) consistently use `batch.json`
on both successful and failed attempts. A source publication conflict is reported
in batch diagnostics and the non-zero exit; other successful sources still publish.
These fields track provider output ownership, not source identity or wiki state.

A rerun replaces or retires only recorded, unchanged files. Neighboring source
folders, user-added attachments, and unrelated files remain intact. A conflicting
unowned or modified file causes a non-zero result naming its path. Older results
without ownership fields must be preserved and rerun into a fresh output folder;
there is no automatic adoption by filename, directory prefix, or marker file.
Public source paths, successful-item publication, partial-failure exit behavior,
and warning handling remain unchanged.

A failed extraction leaves the previous source and successful `result.json`
untouched. Its new diagnostic is `last-failure.json` when a previous report exists,
or `result.json` on a first attempt. A retained `last-failure.json` is historical
evidence of the last failed attempt; successful reruns do not retire it. The
current result report and exit status determine the current extraction state. The exit status and current batch diagnostics
identify the failed attempt; an old `source.md` does not make it successful.

Publication serializes each source with a short-lived `.mineru-publish.lock`.
Filesystem replacement errors restore affected old files. Before replacement, a
sibling `.mineru-recovery-*` directory stores the old files and `recovery.json`
(target, affected paths, paths that previously existed, and preparation phase).
Only a valid record with phase `recoverable` identifies a complete backup to
restore. `preparing` or missing/invalid records are incomplete: publication has
not been established and those backups must not be used to overwrite outputs.
`restored` means rollback finished; `published` means publication finished.
Inspect the actual output before cleaning any interrupted backup. Recovery is
file-level; harmless empty directories created during a failed attempt may remain. Successful publication
removes this backup. An interrupted process can leave the lock and backup: inspect
that exact recovery record, restore only its affected paths (remove newly created
paths absent from `existing`), then remove the stale lock before retrying. Do not
clear the output directory or infer other disposable directories. An interrupted
process may also leave a `.mineru-stage-*` sibling: inspect that exact directory,
confirm its run has stopped and no needed unpublished results remain, then remove
only that confirmed temporary directory. Linked output
paths and unsafe ZIP paths are rejected. Batch input names that differ only by case are rejected conservatively for
portable output directories. One writer still owns each source; shared
batch reports must be serialized by the caller.

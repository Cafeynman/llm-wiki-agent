# MinerU Public API Profile

Use this profile when the project wants the public token-backed MinerU API host.

## Profile Id

`public-api`

## Required Project State

Record this profile in `PROJECT.md` when the public API should be the active MinerU path:

```md
- MinerU profile: public-api
- MinerU profile status: pending | confirmed | failed
```

Keep the credential status in `PROJECT.md` as a separate runtime check result:

```md
- MinerU credential status: unconfigured | pending | confirmed | failed
```

## Environment Variables

Required for this profile:

- `MINERU_TOKEN`

Optional:

- `MINERU_BASE_URL`

If `MINERU_BASE_URL` is empty, use the public host:

- `https://mineru.net`

The generic upload script may also be reused by other MinerU deployments that do not require a token. Do not store real values in skill files, manifests, logs, wiki pages, source cards, `PROJECT.md`, or prompts.

## Profile Contract

- API family: token-backed async extract API
- Authentication for this profile: `Authorization: Bearer <MINERU_TOKEN>`
- Submission pattern for this implementation: request upload URLs, upload local files, poll batch result, download ZIP result
- Source input for this implementation: local file upload only
- Result surface: `full_zip_url`, currently returned as a direct download URL, with `full.md` inside the ZIP used as the normalized Markdown source

## Documented Limits

These limits belong to this profile, not to generic MinerU selection logic:

- File size: up to 200 MB
- Pages: up to 200 pages
- Supported types: PDF, images, Doc, Docx, Ppt, PPTx, Xls, Xlsx, and HTML when using the HTML model
- Batch support: yes, up to 200 files overall
- Upload-link request size: up to 50 files per request
- Output formats: ZIP package containing Markdown and JSON by default, with optional extra export formats

Source: upstream MinerU API docs at <https://mineru.net/apiManage/docs>.

## Limit and Error Handling

For this profile, invoke the parse script with `--max-files-per-batch 50 --max-file-mb 200`. If either local precheck fails, the script exits before uploading and the source should move through the normal WIKI `needs-review` path when the user can approve a split or smaller batch. Use `unsupported` only when the source cannot be retried under this profile.

If the API returns a failed item, missing `full_zip_url`, queue timeout, format rejection, page-count rejection, rate-limit error, or parsing error, the script writes `result.json` for the item, writes `batch.json` for processed results when available, and exits non-zero. Record the profile id, batch id, failed state, and `err_msg` in the intake manifest or review notes before Source Review Gate decides `needs-review` or `unsupported`.

Multi-file runs require unique original base filenames within the batch output root. Duplicate base filenames fail rather than silently suffixing or slugifying directories, because the intake directory name must preserve the original base filename exactly.

## Endpoints

- Upload-link request: `POST /api/v4/file-urls/batch`
- Batch result query: `GET /api/v4/extract-results/batch/{batch_id}`

This repository currently implements only the local upload flow through one `file-urls/batch` request per run. For this profile, run the script with a 50-file local precheck.

## Request Shape

Minimum upload-link request body for ordinary documents:

```json
{
  "files": [
    {
      "name": "demo.pdf",
      "data_id": "demo"
    }
  ],
  "model_version": "vlm"
}
```

Current documented model choices:

- `pipeline`
- `vlm`
- `MinerU-HTML`

Only use `MinerU-HTML` for HTML sources.

Common request parameters exposed by the current script:

- `files[].name`
- `files[].data_id`
- `files[].is_ocr`
- `files[].page_ranges`
- `model_version`
- `language`
- `enable_formula`
- `enable_table`
- `extra_formats`
- `callback`
- `seed`
- `no_cache`
- `cache_tolerance`

Current CLI surface:

- `--file` repeated for one or more local files
- `--model-version`
- `--language`
- `--enable-formula` or `--no-enable-formula`
- `--enable-table` or `--no-enable-table`
- `--is-ocr`
- `--page-ranges`
- `--data-id`
- `--extra-format`
- `--callback`
- `--seed`
- `--no-cache`
- `--cache-tolerance`
- `--max-files-per-batch`
- `--max-file-mb`
- `--base-url`
- `--timeout`
- `--poll-interval`
- `--max-polls`
- `--keep-result-zip`
- `--keep-all-extracted`

## Smoke Check

Run:

```bash
uv run --env-file .env python .agents/skills/source-extraction/references/providers/mineru/scripts/smoke_check.py --base-url "https://mineru.net" --requires-token --docs-url "https://mineru.net/apiManage/docs"
```

This check verifies the public API host is reachable and whether the configured token is accepted. It creates one upload-link batch record but does not upload file bytes or download parse output.

## Parse Script

Run:

```bash
uv run --env-file .env python .agents/skills/source-extraction/references/providers/mineru/scripts/api_parse.py --file "attachments/test-files/mineru-api/1512.03385-resnet.pdf" --output-dir "tmp/mineru-api-resnet" --base-url "https://mineru.net" --docs-url "https://mineru.net/apiManage/docs" --max-files-per-batch 50 --max-file-mb 200
```

For batch upload, repeat `--file`. One-file runs write directly into `--output-dir`. Multi-file runs create one subdirectory per file, named with the original file base filename, plus a root-level `batch.json`.

For this profile, pass `--max-files-per-batch 50` and `--max-file-mb 200` so local prechecks match the public-host upload-link request limits. The script defaults these prechecks to disabled so other MinerU profiles can reuse the same runner without inheriting this profile's limits.

## Output Contract

Single-file run:

- `source.md`
- `full.md`
- `images/` when images are present in the returned package
- `result.json`
- `batch.json`

Batch run:

- `batch.json`
- one subdirectory per uploaded file
- each subdirectory is named with the original file base filename
- each subdirectory contains `source.md`, `full.md`, optional `images/`, and `result.json`

`source.md` is the normalized Markdown surface for later intake handling. `full.md` and `images/` are kept as the default traceable MinerU side outputs. The script removes the downloaded ZIP and unrequested files such as returned originals, layout JSON, model JSON, and content-list exports by default. Use `--keep-result-zip` only when the user asks to preserve the downloaded ZIP, and use `--keep-all-extracted` only when the user asks to inspect every returned artifact.

If `full.md` contains watermark-like text such as `watermark` or `水印`, `result.json` and `batch.json` set `needs_review: true` with a review reason. The provider still writes `source.md`; Source Review Gate decides whether the source can proceed.

## Test Fixture

This repository keeps a stable public PDF fixture for this profile at:

- `attachments/test-files/mineru-api/1512.03385-resnet.pdf`

The fixture is for repeatable local upload checks.

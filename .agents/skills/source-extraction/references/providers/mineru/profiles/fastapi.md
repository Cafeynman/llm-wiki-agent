# MinerU FastAPI Profile

Use this profile when the project uses a MinerU `mineru-api` or `mineru-router` deployment that exposes the FastAPI route family.

## Profile ID

`fastapi`

Record this profile in `PROJECT.md` when this route family is the active MinerU path:

```md
- MinerU profile: fastapi
- MinerU profile status: pending | confirmed | failed
- MinerU credential status: not-required | pending | confirmed | failed
```

## Environment Variables

Required for this profile:

- `MINERU_FASTAPI_BASE_URL`

Optional:

- `MINERU_FASTAPI_TOKEN`
- `MINERU_FASTAPI_SERVER_URL`
- `MINERU_FASTAPI_USER_AGENT`

`MINERU_FASTAPI_BASE_URL` is the deployment root, for example the root that serves `/health`, `/file_parse`, and `/tasks`. Do not store real private endpoint values, tokens, internal model-server URLs, or gateway-specific values in skill files, manifests, logs, wiki pages, source cards, `PROJECT.md`, or prompts.

## Route Family

This profile uses the FastAPI routes exposed by `mineru-api` and `mineru-router`:

| Route | Method | Purpose |
| --- | --- | --- |
| `/health` | `GET` | Smoke check and service metadata |
| `/file_parse` | `POST` | Synchronous parse; waits for the task result |
| `/tasks` | `POST` | Asynchronous task submission |
| `/tasks/{task_id}` | `GET` | Asynchronous task status |
| `/tasks/{task_id}/result` | `GET` | Asynchronous task result download |

Use `scripts/fastapi_parse.py` for this route family. The script submits multipart files directly to `/file_parse` or `/tasks`.

## Request Surface

The parse script sends multipart form data with one or more `files` fields and the selected options below.

Core options:

| Script flag | FastAPI field | Notes |
| --- | --- | --- |
| `--backend` | `backend` | `pipeline`, `vlm-engine`, `vlm-http-client`, `hybrid-engine`, or `hybrid-http-client` |
| `--lang-list` | `lang_list` | Repeat the flag for multiple language values; primarily useful for pipeline OCR |
| `--parse-method` | `parse_method` | `auto`, `txt`, or `ocr`; pipeline/hybrid-oriented |
| `--effort` | `effort` | `medium` or `high`; hybrid-oriented |
| `--server-url` or `MINERU_FASTAPI_SERVER_URL` | `server_url` | Required only for `*-http-client` backends that need an OpenAI-compatible VLM server |

Feature toggles:

| Script flag | FastAPI field |
| --- | --- |
| `--formula-enable` / `--no-formula-enable` | `formula_enable` |
| `--table-enable` / `--no-table-enable` | `table_enable` |
| `--image-analysis` / `--no-image-analysis` | `image_analysis` |

Output controls:

| Script flag | FastAPI field |
| --- | --- |
| `--return-md` / `--no-return-md` | `return_md` |
| `--return-images` / `--no-return-images` | `return_images` |
| `--response-format-zip` / `--no-response-format-zip` | `response_format_zip` |
| `--return-content-list` / `--no-return-content-list` | `return_content_list` |
| `--return-middle-json` / `--no-return-middle-json` | `return_middle_json` |
| `--return-model-output` / `--no-return-model-output` | `return_model_output` |
| `--return-original-file` / `--no-return-original-file` | `return_original_file` |
| `--client-side-output-generation` / `--no-client-side-output-generation` | `client_side_output_generation` |

Page range controls:

| Script flag | FastAPI field |
| --- | --- |
| `--start-page-id` | `start_page_id` |
| `--end-page-id` | `end_page_id` |

## Recommended Invocation

Run the smoke check before first extraction:

```bash
uv run --env-file .env python .agents/skills/source-extraction/references/providers/mineru/scripts/fastapi_smoke_check.py
```

Synchronous parse:

```bash
uv run --env-file .env python .agents/skills/source-extraction/references/providers/mineru/scripts/fastapi_parse.py --mode sync --file "path/to/document.pdf" --output-dir "tmp/mineru-fastapi-document" --backend "hybrid-http-client" --effort "high" --parse-method "auto" --formula-enable --table-enable --image-analysis --return-md --return-images --response-format-zip --no-return-original-file --user-agent "curl/8.0"
```

Asynchronous parse for larger files:

```bash
uv run --env-file .env python .agents/skills/source-extraction/references/providers/mineru/scripts/fastapi_parse.py --mode async --file "path/to/large-document.pdf" --output-dir "tmp/mineru-fastapi-large-document" --backend "hybrid-http-client" --effort "high" --parse-method "auto" --formula-enable --table-enable --image-analysis --return-md --return-images --response-format-zip --no-return-original-file --poll-interval 10 --max-wait 3600 --user-agent "curl/8.0"
```

For an English paper or formula-heavy document, `--backend "vlm-engine"` is usually a smaller invocation and does not need `--server-url`.

Use `--start-page-id` and `--end-page-id` only for an explicitly approved page-range parse. Do not split a full source automatically.

## Output Handling

The script accepts ZIP or JSON responses:

- ZIP responses are normalized into `source.md`, `full.md`, optional `images/`, and `result.json`.
- JSON responses are normalized from `md_content` into `source.md`, `full.md`, and `result.json`.
- `response.json`, `result.zip`, and full `extracted/` contents are kept only when `--keep-json-response`, `--keep-result-zip`, or `--keep-all-extracted` is explicitly set.
- Multi-file runs require unique original base filenames and write one output directory per original base filename.
- Watermark-like text in `full.md` marks `needs_review: true`; Source Review Gate decides whether the source can proceed.

For ZIP output with images, the expected service layout contains Markdown and an `images/` directory under the same result folder. The script copies only images referenced from that result folder into the normalized `images/` directory.

## Error Handling

If the service returns JSON without `md_content`, a ZIP without an identifiable Markdown file, a failed async task, or an async timeout, the script writes review metadata when enough task context exists and exits non-zero. Record the profile id, task id when present, status history, backend, parse method, and error summary in the intake manifest or review notes before Source Review Gate decides `needs-review` or `unsupported`.

Use `needs-review` when the user can retry with a different backend, page range, async mode, gateway delay, or service configuration. Use `unsupported` only when this profile cannot process the source after an explicit user-approved retry strategy.

Common deployment-specific failures:

- `413 Request Entity Too Large`: use async mode or adjust the gateway upload limit.
- `403` or HTML response: gateway/WAF filtering may be involved; retry later, set `MINERU_FASTAPI_USER_AGENT`, or ask the service owner to adjust filtering.
- Timeout in sync mode: retry with `--mode async`.
- Missing images in Markdown output: rerun with `--return-images --response-format-zip`.

## Sources

Use the selected deployment's `/docs` Swagger UI for exact live behavior. The route family also matches the MinerU local usage documentation for `mineru-api` and `mineru-router`:

- <https://opendatalab.github.io/MinerU/zh/usage/quick_usage/>

# MinerU Usage

Use MinerU when `PROJECT.md` selects `mineru` for documents, or when the user explicitly chooses MinerU for complex document parsing.

## Supported Source Kinds

- `document`
- selected scan-heavy or image-like document inputs when OCR/image extraction has been approved

## Modes

MinerU provides two API families:

- Precise parsing API: token required, supports single and batch jobs, up to 200 MB and 200 pages, more output formats, and model choices such as `pipeline`, `vlm`, and `MinerU-HTML`.
- Agent lightweight parsing API: no token, IP-rate-limited, up to 10 MB and 20 pages, asynchronous submission and polling, Markdown-only output.

Prefer the Agent lightweight API for small agent workflow trials when network use is approved and the source fits its limits. Prefer the precise API only when the user has configured credentials and needs its larger limits or richer parsing.

Use `MinerU-HTML` only for HTML sources supported by the precise parsing API. The Agent lightweight URL endpoint is for remote files and does not support HTML.

## Credential Handling

The Agent lightweight API does not require `.env` credentials.

The precise parsing API requires `MINERU_API_TOKEN` in the project-root `.env` file. Private deployments or custom hosted services also require `MINERU_BASE_URL` in `.env`. Any `uv` command or helper script that calls this mode must run from the project root with:

```bash
uv run --env-file .env <mineru-helper-command>
```

For repeated `uv run` commands in the same shell, `UV_ENV_FILE=.env` may be set instead. If `.env`, `MINERU_API_TOKEN`, or a required `MINERU_BASE_URL` is missing, stop before extraction and ask the user to configure it. Do not paste tokens or private endpoint URLs into command examples, prompts, manifests, logs, review notes, wiki pages, or source cards.

## Output Handling

- Save the returned Markdown as `<intake-tmp-dir>/source.md`.
- Record the MinerU mode, model version, task id, OCR flag, credential status as present or not required, warnings, missing content, and result URLs in the intake manifest or review notes.
- If MinerU returns a ZIP, extract only the Markdown needed for `source.md` unless the user explicitly asks to preserve additional artifacts.
- If MinerU reports file-size, page-count, format, queue, timeout, or parsing failures, follow WIKI handling for `needs-review` or `unsupported` based on whether the source can be retried with user judgment.

## OCR and Images

Do not enable MinerU OCR or image extraction automatically. If `PROJECT.md` says `ask-before-ocr`, ask the user before setting OCR options such as `is_ocr`.

## Source

MinerU API behavior should be checked against the official documentation when changing this provider: <https://mineru.net/apiManage/docs>.

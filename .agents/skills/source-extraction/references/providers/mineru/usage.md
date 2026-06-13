# MinerU Usage

Use MinerU when `PROJECT.md` selects `mineru` for documents, when `PROJECT.md` confirms `Prefer MinerU when available: yes`, or when the user explicitly chooses MinerU for complex document parsing.

## Supported Source Kinds

- `document`
- selected scan-heavy or image-like document inputs when OCR/image extraction has been approved

## Modes

MinerU can be used through the official CLI or REST APIs. Use `setup.md` for installation and local credential setup. Use `api.md` only when REST API mode, API/key checks, or official endpoint details are relevant.

The official CLI provides two extraction modes:

- `flash-extract`: no token, one input at a time, up to 10 MB and 20 pages, Markdown output only, formula and table recognition on by default, OCR off by default.
- `extract`: token required, single or batch inputs, up to 200 MB and 200 pages, Markdown plus optional HTML, LaTeX, DOCX, and JSON outputs, model choices such as `vlm`, `pipeline`, and HTML model behavior for HTML inputs.

Prefer `flash-extract` for small Markdown-only trials when network use is approved and the source fits its limits. Prefer `extract` when the user configured credentials and needs larger limits, batch processing, model selection, or richer output formats.

Use MinerU web crawling only when the user explicitly chooses it for a webpage. The repository default webpage provider remains Defuddle.

The official REST APIs have two families:

- Precision API: token required, supports single-file or batch workflows and richer outputs.
- Agent lightweight API: no token, IP-rate-limited, single-file Markdown output for agent workflows.

Do not start either REST API parsing flow during a smoke check. Use the non-submitting checks in `api.md` instead.

## Provider Choice

When both MarkItDown and MinerU are available:

- If `PROJECT.md` confirms `Prefer MinerU when available: yes`, use MinerU for supported document inputs when the required mode is available.
- If that preference is `no` or `unconfirmed`, keep MarkItDown as the ordinary document default and choose MinerU for scanned PDFs, image-heavy PDFs, dense tables, formulas, multi-column academic layouts, or explicit user requests.
- If a PDF is being processed, run the lightweight PDF preflight before selecting the provider.
- Do not switch from MarkItDown to MinerU as an implicit fallback. Explain the observed issue and confirm the provider change unless `PROJECT.md` already authorizes the MinerU preference.

## Credential Handling

`flash-extract` does not require `.env` credentials.

`extract` requires `MINERU_TOKEN` in the project-root `.env` file. Private deployments or custom hosted services also require `MINERU_BASE_URL` in `.env`. Any command that calls this mode must run from the project root with:

```bash
uv run --env-file .env mineru-open-api extract <source>
```

For repeated `uv run` commands in the same shell, `UV_ENV_FILE=.env` may be set instead. If `.env`, `MINERU_TOKEN`, or a required `MINERU_BASE_URL` is missing, stop before extraction and ask the user to configure it. Do not paste tokens or private endpoint URLs into command examples, prompts, manifests, logs, review notes, wiki pages, or source cards.

After the user configures `MINERU_TOKEN`, run the smoke check from `setup.md` before the first token-required MinerU extraction in the workspace. Treat the key as pending until the smoke check passes, and stop before extraction if the check fails.

## CLI Examples

Print Markdown to stdout for a small document:

```bash
mineru-open-api flash-extract "report.pdf"
```

Save Markdown into the intake temporary directory:

```bash
mineru-open-api flash-extract "report.pdf" -o "intake/tmp/report"
```

Run precision extraction after credentials are configured:

```bash
uv run --env-file .env mineru-open-api extract "report.pdf" -f md -o "intake/tmp/report"
```

For private deployments, pass the base URL from the environment without printing its value:

```bash
uv run --env-file .env mineru-open-api extract "report.pdf" -f md -o "intake/tmp/report" --base-url "$MINERU_BASE_URL"
```

Output rules:

- Without `-o`, extracted text goes to stdout and progress or errors go to stderr.
- Without `-o`, use only one input and one text output format.
- Batch mode and binary formats such as DOCX require `-o`.
- Quote source paths that contain spaces or punctuation.

## Output Handling

- Save the returned Markdown as `<intake-tmp-dir>/source.md`, even when the CLI writes a provider-specific filename first.
- Record the MinerU mode, model version, task id, OCR flag, credential status as present or not required, warnings, missing content, and result URLs in the intake manifest or review notes.
- If MinerU returns extra outputs, preserve only what is needed for `source.md` unless the user explicitly asks to keep additional artifacts.
- If MinerU reports file-size, page-count, format, queue, timeout, rate-limit, or parsing failures, follow WIKI handling for `needs-review` or `unsupported` based on whether the source can be retried with user judgment.
- Do not split PDFs automatically. If the selected mode cannot accept the whole file, ask the user to approve a page-range or section split strategy first.
- If an approved split produces multiple Markdown files, merge them into the original source's `<intake-tmp-dir>/source.md` in page order. Keep per-part Markdown only as traceability side outputs, and record page ranges and part paths in the intake manifest or review notes.

## OCR and Images

Do not enable MinerU OCR or image extraction automatically. If `PROJECT.md` says `ask-before-ocr`, ask the user before setting OCR options such as `--ocr`.

## Source

MinerU CLI and API behavior should be checked against the official documentation when changing this provider:

- <https://github.com/opendatalab/MinerU-Ecosystem/tree/main/skills>
- <https://github.com/opendatalab/MinerU-Ecosystem/tree/main/cli>
- <https://mineru.net/apiManage/docs>

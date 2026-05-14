# MinerU Setup

MinerU may be used through local tooling or hosted APIs. Choose the setup that matches the project and user approval.

## Agent Lightweight API

The official MinerU documentation describes an Agent lightweight API that does not require an authorization token. It is IP-rate-limited, supports smaller files, and returns Markdown through an asynchronous submit-and-poll flow.

Limits:

- File size: up to 10 MB
- Pages: up to 20 pages
- Supported types: PDF, images, Docx, PPTx, Xlsx
- Output: Markdown only
- Authorization: no token

Useful endpoints:

- `POST https://mineru.net/api/v1/agent/parse/url`
- `POST https://mineru.net/api/v1/agent/parse/file`

This mode still requires network access approval in restricted environments.

## Precise Parsing API

The precise parsing API requires a token in an `Authorization: Bearer ...` header and supports larger files, batch parsing, and richer output formats.

Limits and behavior:

- File size: up to 200 MB
- Pages: up to 200 pages
- Supported types: PDF, images, Doc, Docx, PPT, PPTx, Xls, Xlsx, and HTML when using `MinerU-HTML`
- Output: ZIP containing Markdown and JSON by default, with optional docx/html/latex exports where supported
- Authorization: Bearer token required

Useful endpoints:

- `POST https://mineru.net/api/v4/extract/task`
- `GET https://mineru.net/api/v4/extract/task/{task_id}`
- `POST https://mineru.net/api/v4/file-urls/batch`

If using token-based mode, keep the token in the project-root `.env` file. Suggested variable names:

- `MINERU_API_TOKEN`
- `MINERU_BASE_URL` when a custom endpoint is required

Do not store tokens in `PROJECT.md`, `WIKI.md`, `AGENTS.md`, `CLAUDE.md`, manifests, logs, wiki pages, source cards, or skill files.

## Official Documentation

Use the official MinerU API documentation for current limits and parameters: <https://mineru.net/apiManage/docs>.

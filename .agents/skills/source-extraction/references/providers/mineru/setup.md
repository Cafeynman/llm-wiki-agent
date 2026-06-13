# MinerU Setup

MinerU may be used through the official `mineru-open-api` CLI. Choose the setup that matches the project and user approval.

## Official CLI

Install or update the CLI with the official installer for the current platform:

```powershell
irm https://cdn-mineru.openxlab.org.cn/open-api-cli/install.ps1 | iex
```

```bash
curl -fsSL https://cdn-mineru.openxlab.org.cn/open-api-cli/install.sh | sh
```

Verify the installed command:

```bash
mineru-open-api version
```

The upstream skill also documents npm and Go install paths. Prefer the official CLI documentation when install behavior changes.

## Basic Provider Smoke Check

Run the smoke check after the user confirms `MINERU_TOKEN` has been configured and before the first token-required MinerU extraction in a workspace. The check must not submit a document URL, request an upload URL, upload a file, poll a real parsing task, or download parsing output.

Run from the project root after `.env` is configured:

```bash
uv run python .agents/skills/source-extraction/references/providers/mineru/scripts/smoke_check.py
```

The script reads `MINERU_TOKEN` and optional `MINERU_BASE_URL` from the current environment or `.env`. It reports only whether required values are present and whether the API routes accept the request shape. It must not print secret values or private endpoint URLs.

Treat a configured token as pending until this smoke check passes. Only then record `MinerU API key status: confirmed` in `PROJECT.md`. If the check fails, keep the status pending or failed, stop before extraction, and send the user the official API documentation link.

If `.env` or `MINERU_TOKEN` is missing, send the user the official MinerU API documentation link so they can view or apply for API access:

- <https://mineru.net/apiManage/docs>

Do not ask the user to paste the token into chat. Tell them to configure it locally in `.env`.

## Flash Extraction

`mineru-open-api flash-extract` does not require an authorization token. It is intended for small files and quick Markdown extraction.

Limits:

- File size: up to 10 MB
- Pages: up to 20 pages
- Supported types: PDF, images, Docx, PPTx, Xls, Xlsx
- Output: Markdown only
- Authorization: no token

This mode still requires network access approval in restricted environments.

## Precision Extraction

`mineru-open-api extract` requires a token and supports larger files, batch parsing, and richer output formats.

Limits and behavior:

- File size: up to 200 MB
- Pages: up to 200 pages
- Supported types: PDF, images, Doc, Docx, PPT, PPTx, Xls, Xlsx, and HTML when using the HTML model
- Output formats: Markdown, HTML, LaTeX, DOCX, and JSON where supported
- Authorization: token required

If using token-based mode, keep the token in the project-root `.env` file. Required variable for the official CLI:

- `MINERU_TOKEN`

Optional variable, only when a private deployment or custom hosted endpoint is required:

- `MINERU_BASE_URL`

The CLI resolves tokens in this order: `--token`, `MINERU_TOKEN`, then `~/.mineru/config.yaml`. This package uses the project-root `.env` file as the credential source of truth, so prefer `MINERU_TOKEN` loaded from `.env` instead of `--token` or global CLI config. Do not use `--token` in recorded command examples because it risks exposing secrets in shell history and logs.

Use `.env.example` as the non-secret template. Do not store tokens or private endpoint values in `PROJECT.md`, `WIKI.md`, `AGENTS.md`, `CLAUDE.md`, manifests, logs, wiki pages, source cards, or skill files. Agents may check whether `MINERU_TOKEN` and any required `MINERU_BASE_URL` are present, but must not print or persist their values.

## Official Documentation

Use the official MinerU CLI and API documentation for current limits and parameters:

- <https://github.com/opendatalab/MinerU-Ecosystem/tree/main/cli>
- <https://mineru.net/apiManage/docs>

# markitdown-ocr Guide

[中文版](markitdown-ocr.zh-CN.md)

Use `markitdown-ocr` only when important content is inside scans, screenshots, or embedded images. Keep the default workflow text-first. Do not enable OCR unless the user asks for it or plain `markitdown` misses critical text.

## First Install

```sh
uv add markitdown-ocr openai
uv run markitdown --list-plugins
```

The plugin list should include `ocr`.

## One-Time Setup

Prepare `base_url`, `api_key`, and the repo-local default OCR model once. If `.env` already has the correct values, do not configure them again.

`.env`
```env
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
OPENAI_API_KEY=your-api-key
MARKITDOWN_OCR_MODEL=gpt-4o
```

Load `.env` every time:

```sh
uv run --env-file .env markitdown input.pdf --use-plugins --llm-client openai --llm-model <value from MARKITDOWN_OCR_MODEL> -o output.md
```

If you prefer, set `UV_ENV_FILE=.env` in your shell environment once and reuse plain `uv run` in that same shell.

That shell-level shortcut is optional. The portable command is still the `--env-file .env` form above.

## Daily Command

```sh
uv run --env-file .env markitdown input.pdf --use-plugins --llm-client openai --llm-model <value from MARKITDOWN_OCR_MODEL> -o output.md
```

- Prefer environment variables for OpenAI-compatible setups.
- Verify plugin discovery with `uv run markitdown --list-plugins`.
- `OPENAI_BASE_URL` and `OPENAI_API_KEY` come from `.env`, so you do not need to repeat them in the command.
- This repo treats `MARKITDOWN_OCR_MODEL` as the default OCR model.
- The agent should read `MARKITDOWN_OCR_MODEL` from `.env` and pass it explicitly as `--llm-model`.
- Keep passing `--llm-client openai`. If `llm_client` or `llm_model` is missing, the plugin may load but OCR will be skipped.

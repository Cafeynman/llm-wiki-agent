<h1 align="center"><b>🔍 markitdown-ocr Guide</b></h1>

<p align="center">
  <b><i><font size="4">Handling scans, screenshots, and embedded images.</font></i></b>
</p>

<p align="center">
  <a href="markitdown-ocr.zh-CN.md">🇨🇳 中文</a> ·
  <a href="markitdown-ocr.md">🇬🇧 English</a>
</p>

<p align="center">
  <a href="../README.md">🏠 Back to Home</a> · <a href="usage.md">📖 Usage Guide</a>
</p>

---

> [!WARNING]
> Use `markitdown-ocr` **only** when important content is locked inside scans, screenshots, or embedded images. Keep the default workflow text-first. **Do not** enable OCR unless explicitly asked or if plain `markitdown` misses critical text.

## 🚀 1. First Install

To use OCR, add the required dependencies:
```bash
uv add markitdown-ocr openai
uv run markitdown --list-plugins
```
> **Check:** The plugin list output should include `ocr`.

---

## ⚙️ 2. One-Time Setup

You only need to prepare `base_url`, `api_key`, and the repo-local default OCR model once. If your `.env` is already set up, you can skip this.

Create or update `.env`:
```env
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
OPENAI_API_KEY=your-api-key
MARKITDOWN_OCR_MODEL=gpt-4o
```

When running, load `.env` every time:
```bash
uv run --env-file .env markitdown input.pdf --use-plugins --llm-client openai --llm-model <value from MARKITDOWN_OCR_MODEL> -o output.md
```

> [!TIP]
> **Optional Shell Shortcut:** Set `UV_ENV_FILE=.env` in your shell environment once, and you can simply use `uv run` in that shell without repeatedly specifying the env file. However, the portable command is still the `--env-file .env` format.

---

## ⚡ 3. Daily Command

For day-to-day OCR processing:
```bash
uv run --env-file .env markitdown input.pdf --use-plugins --llm-client openai --llm-model <value from MARKITDOWN_OCR_MODEL> -o output.md
```

### 📋 Key Rules
- **Environment Variables:** Prefer using `.env` variables for OpenAI-compatible setups so you don't repeat them in the command.
- **Verification:** Verify plugin discovery with `uv run markitdown --list-plugins`.
- **Default Model:** This repo treats `MARKITDOWN_OCR_MODEL` as the default OCR model. The agent should read it from `.env` and pass it explicitly via `--llm-model`.
- **Client Flag:** Always keep passing `--llm-client openai`. If `llm_client` or `llm_model` is missing, the plugin might load but OCR will be skipped entirely.

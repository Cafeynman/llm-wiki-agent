# markitdown-ocr 指南

[ENGLISH VERSION](markitdown-ocr.md)

`markitdown-ocr` 只适合处理关键信息主要在扫描页、截图、嵌入图片里的 PDF、Word、PowerPoint、Excel。默认流程仍然是 text-first。只有用户明确要求，或普通 `markitdown` 提不出关键文本时，才开启 OCR。

## 首次安装

```sh
uv add markitdown-ocr openai
uv run markitdown --list-plugins
```

插件列表里应包含 `ocr`。

## 一次性配置

先一次性准备好 `base_url`、`api_key` 和仓库本地默认 OCR 模型。如果 `.env` 里已经有正确值，就不要重复配置。

`.env`
```env
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
OPENAI_API_KEY=your-api-key
MARKITDOWN_OCR_MODEL=gpt-4o
```

每次显式加载 `.env`：

```sh
uv run --env-file .env markitdown input.pdf --use-plugins --llm-client openai --llm-model <从 MARKITDOWN_OCR_MODEL 读取的值> -o output.md
```

如果你愿意，也可以先在当前 shell 环境里设置 `UV_ENV_FILE=.env`，之后在同一个 shell 里复用普通 `uv run`。

但这只是可选捷径。默认仍然建议使用上面带 `--env-file .env` 的命令。

## 后续日常命令

```sh
uv run --env-file .env markitdown input.pdf --use-plugins --llm-client openai --llm-model <从 MARKITDOWN_OCR_MODEL 读取的值> -o output.md
```

- OpenAI 兼容接口优先用环境变量。
- 用 `uv run markitdown --list-plugins` 检查是否已发现 OCR 插件。
- 配好 `.env` 之后，命令里不需要每次重复写 `OPENAI_BASE_URL` 和 `OPENAI_API_KEY`。
- 本仓库把 `MARKITDOWN_OCR_MODEL` 作为默认 OCR 模型。
- agent 应从 `.env` 里读取 `MARKITDOWN_OCR_MODEL`，再手动传给 `--llm-model`。
- `--llm-client openai` 仍然要带；如果缺 `llm_client` 或 `llm_model`，插件可能会加载，但 OCR 会被跳过。

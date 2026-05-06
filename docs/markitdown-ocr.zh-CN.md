<h1 align="center"><b>🔍 markitdown-ocr 指南</b></h1>

<p align="center">
  <b><i><font size="4">处理扫描件、截图和嵌入的图片。</font></i></b>
</p>

<p align="center">
  <a href="markitdown-ocr.zh-CN.md">🇨🇳 中文</a> ·
  <a href="markitdown-ocr.md">🇬🇧 English</a>
</p>

<p align="center">
  <a href="../README.zh-CN.md">🏠 返回首页</a> · <a href="usage.zh-CN.md">📖 使用指南</a>
</p>

---

> [!WARNING]
> 只有当重要内容被锁在扫描件、截图或嵌入图片中时，才使用 `markitdown-ocr`。 保持默认的“文本优先”工作流。**不要**轻易开启 OCR，除非已明确要求或者普通的 `markitdown` 遗漏了关键文本。

## 🚀 1. 首次安装

如果要使用 OCR，请添加依赖：
```bash
uv add markitdown-ocr openai
uv run markitdown --list-plugins
```
> **检查:** 插件列表输出中必须包含 `ocr`。

---

## ⚙️ 2. 一次性设置

你只需设置一次 `base_url`, `api_key`，以及仓库级别的默认 OCR 模型。如果你的 `.env` 已经配置好，可以跳过此步。

创建或更新 `.env`:
```env
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
OPENAI_API_KEY=your-api-key
MARKITDOWN_OCR_MODEL=gpt-4o
```

运行时，每次都要加载 `.env`:
```bash
uv run --env-file .env markitdown input.pdf --use-plugins --llm-client openai --llm-model <value from MARKITDOWN_OCR_MODEL> -o output.md
```

> [!TIP]
> **可选的环境变量快捷方式:** 你可以在 Shell 中全局设置一次 `UV_ENV_FILE=.env`，之后在同一个 Shell 会话中只需使用普通的 `uv run` 即可。但为了脚本的便携性，官方写法仍推荐显式加上 `--env-file .env`。

---

## ⚡ 3. 日常使用命令

日常的 OCR 处理命令：
```bash
uv run --env-file .env markitdown input.pdf --use-plugins --llm-client openai --llm-model <value from MARKITDOWN_OCR_MODEL> -o output.md
```

### 📋 核心规则
- **环境变量优先:** 对于兼容 OpenAI 的接口设置，优先使用 `.env` 文件，避免在命令行中反复输入长参数。
- **验证插件:** 遇到问题时用 `uv run markitdown --list-plugins` 验证插件加载。
- **默认模型:** 本仓库将 `MARKITDOWN_OCR_MODEL` 视为默认的 OCR 模型。智能体应当从 `.env` 读取该值，并通过 `--llm-model` 显式传递。
- **Client 参数:** 务必保留 `--llm-client openai`。如果 `llm_client` 或 `llm_model` 缺失，插件或许能加载，但 OCR 会被完全跳过。

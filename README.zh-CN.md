# LLM Wiki Agent 最佳实践

[English](README.md)

LLM Wiki Agent 是一个面向 LLM agent 的最佳实践工作流包，用于构建和维护一个持久、可追溯、Obsidian 风格的 Markdown 知识库。

这个包给 agent 提供明确的操作契约：原始文件进入 `inbox/`，原始文件保存在 `raw/`，可审查的 Markdown 写入 `intake/`，长期知识沉淀到 `wiki/`，面向用户的交付物保存到 `artifacts/`。

## 这是什么

这不是完整应用服务器，也不是 Obsidian 插件。它是一个可移植的 agent workflow 包，适合 Codex、Claude Code、Gemini CLI、OpenCode 或其他能读取项目说明文件的 agent 使用。

核心流程很简单：

1. 把 source 文件放进 `inbox/`。
2. 要求 agent 按 [AGENTS.md](AGENTS.md) 和 [WIKI.md](WIKI.md) 处理。
3. agent 把有价值的 source 转成可审查 Markdown。
4. agent 在写入 wiki 前先做 source review。
5. 被接受的知识会变成 `wiki/` 下的互链 Markdown 页面。

## 快速开始

克隆或下载仓库后进入目录：

```powershell
cd llm-wiki-agent
```

初始化 Python 环境并创建 wiki 目录结构：

```powershell
.\scripts\init.ps1 -VaultRoot .
```

如果要把 wiki 结构创建到单独的 Obsidian vault：

```powershell
.\scripts\init.ps1 -VaultRoot "C:\path\to\your\vault"
```

然后用你的 agent 打开该目录或 vault，并让它以 [AGENTS.md](AGENTS.md) 作为入口。执行 wiki 任务前，agent 应读取 [WIKI.md](WIKI.md)。

完整使用说明见 [docs/usage.zh-CN.md](docs/usage.zh-CN.md)。

## 第一次最小运行

初始化后，把一个 source 文件放进 `inbox/`：

```text
inbox/
└── example.md
```

向 agent 发送：

```text
Process the files in inbox/ according to AGENTS.md and WIKI.md.
```

预期生命周期是：

```text
inbox/ -> intake/tmp/ -> source review -> raw/<state>/ + intake/processed/ + wiki/
```

原始文件最终只会进入一个 raw 状态：

```text
raw/digested/
raw/needs-review/
raw/ignored/
raw/unsupported/
```

只有 `digested` source 会进入 `intake/processed/` 并继续更新 `wiki/`。

## 核心工作流

本包只保留三种 agent 工作流：

| 工作流 | 适用场景 |
| --- | --- |
| Add Knowledge | 添加文件、审查 source、转换资料、ingest 已接受知识、回流已确认讨论结论。 |
| Use Knowledge | 使用 wiki 回答问题、综合页面、或在 `artifacts/` 下创建交付物。 |
| Maintain Wiki | 检查断链、缺失来源、过期 claim、矛盾、重复页面和日志缺口。 |

agent 应选择能够完整满足当前请求的最短工作流。

## 包内容

```text
.
├── README.md
├── README.zh-CN.md
├── AGENTS.md
├── WIKI.md
├── LICENSE
├── pyproject.toml
├── scripts/
│   └── init.ps1
├── skills/
└── docs/
    ├── usage.md
    ├── usage.zh-CN.md
    ├── references.md
    ├── references.zh-CN.md
    ├── acknowledgements.md
    └── acknowledgements.zh-CN.md
```

## 设计边界

- 当前工作流是文本优先。附件、扫描件、截图、图片和音频可以作为原始 source 保存，但默认不是 wiki 的一等内容，除非你明确添加图片或音频处理。
- wiki 更新前必须先做 source review。转换命令成功不代表 source 被接受。
- 原始 source 文件应保持可追溯。agent 生成的 Markdown 属于 `intake/`，不属于 `raw/`。
- 报告、brief、outline、draft、模板等面向用户的交付物应写入 `artifacts/`，不要写入 `wiki/`。
- 本包优先使用显式 traceability，而不是隐藏 memory。长期 claim 应引用 source card、intake output、raw 文件或已确认的讨论记录。

## 文档

- [README.md](README.md)：英文首页。
- [docs/usage.md](docs/usage.md)：英文使用手册。
- [docs/usage.zh-CN.md](docs/usage.zh-CN.md)：中文使用手册。
- [AGENTS.md](AGENTS.md)：agent 入口和工作流路由。
- [WIKI.md](WIKI.md)：agent 执行时的主规则。
- [docs/references.md](docs/references.md)：英文引用。
- [docs/references.zh-CN.md](docs/references.zh-CN.md)：中文引用。
- [docs/acknowledgements.md](docs/acknowledgements.md)：英文感谢。
- [docs/acknowledgements.zh-CN.md](docs/acknowledgements.zh-CN.md)：中文感谢。

## 引用与感谢

本包基于 LLM Wiki pattern 及相关公开实践整理而成。见 [docs/references.zh-CN.md](docs/references.zh-CN.md) 和 [docs/acknowledgements.zh-CN.md](docs/acknowledgements.zh-CN.md)。

## 开源协议

MIT License。见 [LICENSE](LICENSE)。

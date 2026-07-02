<h1 align="center"><b>LLM Wiki Agent</b></h1>

<h2 align="center"><b>通过 LLM 智能体构建并维护一个持久化、可溯源的 Obsidian 风格 Markdown 知识库。</b></h2>

<p align="center">
  <b><i><font size="4">只需将文件放入收件箱，让智能体为你构建 Wiki。</font></i></b>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12"></a>
  <a href="https://docs.astral.sh/uv/"><img src="https://img.shields.io/badge/Package_Manager-uv-blue?logo=python&logoColor=white" alt="uv Package Manager"></a>
  <a href="https://obsidian.md/"><img src="https://img.shields.io/badge/Optimized_for-Obsidian-483699?logo=obsidian&logoColor=white" alt="Optimized for Obsidian"></a>
  <a href="#%EF%B8%8F-核心特性与设计边界"><img src="https://img.shields.io/badge/⚠️_Rules-Text_First-orange" alt="Text-First Boundaries"></a>
</p>

<p align="center">
  <a href="README.zh-CN.md">🇨🇳 中文</a> ·
  <a href="README.md">🇬🇧 English</a>
</p>

<p align="center">
  <a href="docs/usage.zh-CN.md">📖 使用指南</a> · <a href="AGENTS.md">🤖 智能体规则</a> · <a href="WIKI.md">🧠 Wiki 规则</a> · <a href="PROJECT.md">⚙️ 项目上下文</a>
</p>

---

## ⚡ 快速开始：从零到 Wiki

克隆或下载此仓库，然后初始化环境：

```bash
cd llm-wiki-agent

# Windows
.\scripts\init.ps1 -VaultRoot .

# macOS / Linux
./scripts/init.sh -VaultRoot .
```

*提示：如果要使用单独的 Obsidian 库，请传递库路径，例如 `.\scripts\init.ps1 -VaultRoot "C:\path\to\your\vault"`。目标库会成为工作根目录，并获得包管理的智能体文件、本地技能、脚本、文档和运行结构。包管理文件会被包副本替换；库级个性化偏好应放在 `PROJECT.md`。*

默认来源提取偏好记录在 `PROJECT.md`。首次确认项目上下文时，智能体会询问是否配置 MinerU、API 模式下使用哪个 MinerU profile，以及 MinerU 可用时是否优先使用 MinerU；选择该偏好时会把 MinerU 记录为文档默认 provider。
如果使用需要本地服务配置的 provider 或 OCR 后端，请将 `.env.example` 复制为初始化后工作根目录中的 `.env`，并只填写所选 provider profile 真正需要的变量。真实 `.env` 已被 Git 忽略；智能体运行 provider 命令时应通过 `uv run --env-file .env` 加载它。
后续升级包文件时，请使用 [使用指南](docs/usage.zh-CN.md#升级包文件) 中的 manifest 驱动升级脚本。

`scenarios/` 下的可选场景包可将初始化后的工作区适配为考试备考等专门用途；见 [可选场景包](docs/usage.zh-CN.md#可选场景包)。

**你的最小化首次运行：**
1. 将源文件放入 `inbox/example.md`。
2. 对智能体说：*"请根据 AGENTS.md, PROJECT.md 和 WIKI.md 处理 inbox/ 中的文件。"*
3. 观察智能体将你的文件处理到 `wiki/` 目录！

---

## 🤔 这是什么？

**你投放文件，智能体整理知识，你获得一个可溯源的 Wiki。**

本仓库**不是**一个完整的应用服务器，也**不是** Obsidian 的替代品。它是一个**便携的工作流包**，专为能够读取仓库指令的智能体（如 Codex, Claude Code, Gemini CLI, OpenCode 等）设计。

该项目为你的智能体提供了一份严格而清晰的操作契约：
<table>
<tr><td>📥</td><td><code>inbox/</code></td><td>源文件的唯一入口</td></tr>
<tr><td>🗄️</td><td><code>raw/</code></td><td>原始文件的持久化保存地</td></tr>
<tr><td>⚙️</td><td><code>intake/</code></td><td>生成可审查 Markdown 的处理区</td></tr>
<tr><td>🧠</td><td><code>wiki/</code></td><td>写入持久化知识的页面库</td></tr>
<tr><td>📦</td><td><code>artifacts/</code></td><td>保存面向用户的交付物的目录</td></tr>
</table>

---

## 🔬 核心工作流

该包严格限制智能体在三个主要工作流内运行。智能体会自动选择能够满足请求的最小工作流：

| 工作流 | 何时使用 | 它的作用 |
|-----------|-------------|--------------|
| **➕ 添加知识 (Add Knowledge)** | 添加文件、审查来源、提取材料。 | 将文件从 `inbox/` 推进至 `intake/` 再到 `wiki/`，并反射确认的讨论见解。 |
| **💡 使用知识 (Use Knowledge)** | 回答问题、综合页面、生成交付物。 | 检索 wiki，并在 `artifacts/` 目录下生成报告、简报、草案或对照表。 |
| **🧹 维护 Wiki (Maintain Wiki)** | 健康检查、清理死链、查找过期声明。 | 查找矛盾、检测重复、记录日志空白，确保溯源完整。 |

---

## ✨ 核心特性与设计边界

| 特性 | 描述 |
|---------|------------|
| **📜 文本优先 (Text-First)** | 提取结果必须是 Markdown。附件和图片作为原始来源保留在 `raw/` 中。 |
| **🔍 来源审查门 (Source Review)** | 成功提取是不够的。智能体在将来源接受进 wiki 之前必须进行审查。 |
| **🔗 显式溯源 (Explicit Traceability)** | 提倡显式链接而非依赖隐藏记忆。所有声明必须引用来源卡片、原始文件或讨论记录。 |
| **📂 原始文件留存 (Original Preservation)** | 妥善保管原始文件。生成的 Markdown 保存在 `intake/`，绝不混入 `raw/`。 |
| **⚙️ 可替换上下文 (Replaceable Context)** | `PROJECT.md` 包含你的特定偏好。`WIKI.md` 和 `AGENTS.md` 则是稳定的工作流规则。 |
| **🛡️ 安全的交付物 (Safe Artifacts)** | 面向用户的报告、简报、大纲和草案进入 `artifacts/`，保持 `wiki/` 的纯净。 |

---

## 🛠️ 推荐配置

为了最大化发挥 LLM Wiki Agent 的能力，建议搭配以下工具使用：
- **[Claudian](https://github.com/YishenTu/claudian)**：如果你想要一个面向 Obsidian 的本地智能体环境，这是推荐选择。
- **[Obsidian Web Clipper](https://github.com/obsidianmd/obsidian-clipper)**：推荐用于将网页无缝剪辑为 Markdown 源材料。

---

## 🧩 项目结构

<details>
<summary>点击查看完整目录结构</summary>

```text
.
├── README.md
├── README.zh-CN.md
├── AGENTS.md
├── PROJECT.md
├── WIKI.md
├── LICENSE
├── pyproject.toml
├── .env.example
├── scripts/
│   ├── init.ps1
│   ├── init.sh
│   ├── upgrade-manifest.txt
│   ├── upgrade.ps1
│   └── upgrade.sh
├── scenarios/
│   ├── README.md
│   └── exam-study/
├── .agents/
│   └── skills/
└── docs/
    ├── usage.md
    ├── usage.zh-CN.md
    ├── references.md
    ├── references.zh-CN.md
    ├── acknowledgements.md
    └── acknowledgements.zh-CN.md
```

</details>

---

## 🙏 致谢与参考

本工作流包基于 LLM Wiki 模式及相关的开源工作构建。请查看 [参考资料 (References)](docs/references.zh-CN.md) 和 [致谢 (Acknowledgements)](docs/acknowledgements.zh-CN.md) 获取详情。

---

## 📄 开源协议

MIT License. 参见 [LICENSE](LICENSE)。

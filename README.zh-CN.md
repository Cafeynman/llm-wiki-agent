<h1 align="center"><b>LLM Wiki Agent</b></h1>

<h2 align="center"><b>通过 LLM 智能体构建并维护一个持久化、可溯源的 Markdown 知识库。</b></h2>

<p align="center">
  <b><i><font size="4">只需将文件放入收件箱，让智能体为你构建 Wiki。</font></i></b>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12"></a>
  <a href="https://docs.astral.sh/uv/"><img src="https://img.shields.io/badge/Package_Manager-uv-blue?logo=python&logoColor=white" alt="uv Package Manager"></a>
  <a href="https://obsidian.md/"><img src="https://img.shields.io/badge/Obsidian-Compatible-483699?logo=obsidian&logoColor=white" alt="Obsidian Compatible"></a>
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

*提示：如果要使用单独的工作目录，包括现有 Obsidian 库，请传递该路径，例如 `.\scripts\init.ps1 -VaultRoot "C:\path\to\your\workspace"`。目标目录会成为工作根目录，并获得包管理的智能体文件、本地技能、脚本、文档和运行结构。包管理文件会被包副本替换；工作区个性化偏好应放在 `PROJECT.md`。*

默认来源提取偏好记录在 `PROJECT.md`。首次确认项目上下文时，智能体会询问是否配置 MinerU、API 模式下使用哪个 MinerU profile，以及 MinerU 可用时是否优先使用 MinerU；选择该偏好时会把 MinerU 记录为文档默认 provider。
如果使用需要本地服务配置的 provider 或 OCR 后端，请将 `.env.example` 复制为初始化后工作根目录中的 `.env`，并只填写所选 provider profile 真正需要的变量。真实 `.env` 已被 Git 忽略；智能体运行 provider 命令时应通过 `uv run --env-file .env` 加载它。
后续升级包文件时，请使用 [使用指南](docs/usage.zh-CN.md#升级包文件) 中的 manifest 驱动升级脚本。
默认 `.gitignore` 会让本地 wiki 运行内容保持私有；如果这个 checkout 本身是需要版本化的 wiki 项目，请参考 [Git Ignore 模板](docs/gitignore-templates.zh-CN.md)。

`scenarios/` 下的可选场景包可将初始化后的工作区适配为考试备考等专门用途；见 [可选场景包](docs/usage.zh-CN.md#可选场景包)。

**你的最小化首次运行：**
1. 将源文件放入 `inbox/`，或者把一个实时 URL 作为来源交给智能体。
2. 对智能体说：*"请根据 AGENTS.md、PROJECT.md 和 WIKI.md 处理这些来源。"*
3. 智能体会先通过 Defuddle 固化 URL，审查来源，并只在接受后更新 wiki。

---

## 🤔 这是什么？

**你提供文件或链接，智能体整理知识，你获得一个可溯源的 Wiki。**

本仓库**不是**一个完整的应用服务器，也不绑定特定智能体平台。它是一个**便携的工作流包**，任何能够读取仓库指令、编辑文件并执行所需命令的智能体都可以使用。Obsidian 和 Claudian 都是可选界面，不是运行要求。

该项目为你的智能体提供了一份严格而清晰的操作契约：
<table>
<tr><td>📥</td><td><code>inbox/</code></td><td>提交文件和 URL 来源捕获文件的入口</td></tr>
<tr><td>🗄️</td><td><code>raw/</code></td><td>生命周期来源工件的持久化保存地</td></tr>
<tr><td>⚙️</td><td><code>intake/</code></td><td>生成可审查 Markdown 的处理区</td></tr>
<tr><td>📝</td><td><code>reviews/</code></td><td>记录来源审查决定与讨论反射</td></tr>
<tr><td>⏱️</td><td><code>logs/</code></td><td>记录 wiki 操作历史</td></tr>
<tr><td>❓</td><td><code>questions/</code></td><td>保存悬而未决的调查线索</td></tr>
<tr><td>🧠</td><td><code>wiki/</code></td><td>写入持久化知识的页面库</td></tr>
<tr><td>📦</td><td><code>artifacts/</code></td><td>保存面向用户的交付物的目录</td></tr>
</table>

---

## 🔬 核心工作流

该包严格限制智能体在三个主要工作流内运行。智能体会自动选择能够满足请求的最小工作流：

| 工作流 | 何时使用 | 它的作用 |
|-----------|-------------|--------------|
| **➕ 添加知识 (Add Knowledge)** | 添加文件或 URL、审查来源、提取材料。 | 将来源工件从 `inbox/` 推进至 `intake/` 再到 `wiki/`，并反射确认的讨论见解。 |
| **💡 使用知识 (Use Knowledge)** | 回答问题、综合页面、生成交付物。 | 检索 wiki，并在 `artifacts/` 目录下生成报告、简报、草案或对照表。 |
| **🧹 维护 Wiki (Maintain Wiki)** | 健康检查、清理死链、查找过期声明。 | 查找矛盾、检测重复、记录日志空白，确保溯源完整。 |

---

## ✨ 核心特性与设计边界

| 特性 | 描述 |
|---------|------------|
| **📜 文本优先 (Text-First)** | 提取结果必须是 Markdown。提供方返回的附件可以保存在 `source.md` 旁，但不会被自动解释。 |
| **🔍 来源审查门 (Source Review)** | 成功提取是不够的。智能体在将来源接受进 wiki 之前必须进行审查。 |
| **🔗 显式溯源 (Explicit Traceability)** | 提倡显式链接而非依赖隐藏记忆。所有声明必须引用来源卡片、原始文件或讨论记录。 |
| **📂 来源留存 (Source Preservation)** | 提交文件会被保留；Defuddle 捕获文件是实时 URL 的生命周期原件，其他生成 Markdown 仍保存在 `intake/`。 |
| **⚙️ 可替换上下文 (Replaceable Context)** | `PROJECT.md` 包含你的特定偏好。`WIKI.md` 和 `AGENTS.md` 则是稳定的工作流规则。 |
| **🛡️ 安全的交付物 (Safe Artifacts)** | 面向用户的报告、简报、大纲和草案进入 `artifacts/`，保持 `wiki/` 的纯净。 |

---

## 🛠️ 可选界面

LLM Wiki Agent 可以直接通过文件系统运行，不需要安装 Obsidian 或 Claudian。如果你希望使用 Obsidian 界面：

- **Claudian** 可以把受支持的智能体运行时嵌入 Obsidian 库中。请按照 [YishenTu/claudian 仓库](https://github.com/YishenTu/claudian)或 [Claudian 官网](https://claudian.xyz/zh/)的最新安装说明操作，再查看 [provider 文档](https://claudian.xyz/zh/docs/providers/)。本仓库的配置建议见 [使用指南](docs/usage.zh-CN.md#可选的-obsidian-与-claudian-界面)。
- **[Obsidian Web Clipper](https://github.com/obsidianmd/obsidian-clipper)** 可以把网页收集为 Markdown 来源材料。

---

## 🧩 项目结构

<details>
<summary>点击查看包管理文件和初始化后的运行目录</summary>

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
    ├── gitignore-templates.md
    ├── gitignore-templates.zh-CN.md
    ├── source-lifecycle.md
    ├── source-lifecycle.zh-CN.md
    ├── wiki-page-templates.md
    ├── wiki-page-templates.zh-CN.md
    ├── references.md
    ├── references.zh-CN.md
    ├── acknowledgements.md
    └── acknowledgements.zh-CN.md
```

初始化后，工作根目录还会包含由初始化或升级脚本创建的本地运行目录。
这些目录用于保存当前工作区数据，默认会被 Git 忽略。如果要把持久化 wiki 内容纳入
Git，请参考 [Git Ignore 模板](docs/gitignore-templates.zh-CN.md)。

```text
.
├── inbox/             提交文件和实时 URL 捕获文件的入口
├── raw/               按审查状态保存的生命周期来源工件
├── intake/            临时和已接受的 Markdown 提取输出
├── reviews/           来源审查与讨论反射记录
├── logs/              Wiki 操作历史
├── questions/         悬而未决的问题与调查线索
├── artifacts/         面向用户的交付物
└── wiki/              持久化知识页面
```

</details>

---

## 🙏 致谢与参考

本工作流包基于 LLM Wiki 模式及相关的开源工作构建。请查看 [参考资料 (References)](docs/references.zh-CN.md) 和 [致谢 (Acknowledgements)](docs/acknowledgements.zh-CN.md) 获取详情。

---

## 📄 开源协议

MIT License. 参见 [LICENSE](LICENSE)。

# 使用手册

本文说明如何安装、初始化和日常使用 LLM Wiki Agent。[AGENTS.md](../AGENTS.md) 是 agent 入口，[WIKI.md](../WIKI.md) 是主工作规则。

英文版见 [usage.md](usage.md)。

## 1. 适用场景

LLM Wiki Agent 适合把长期积累的资料整理成一个可持续维护的 Markdown wiki：

- 研究资料、文章、论文、网页剪藏。
- 项目知识、决策记录、会议纪要、技术调研。
- 个人知识库、读书笔记、主题资料库。
- 需要反复追溯来源、整理 claim、保留不确定性的问题。

它不适合作为一次性问答工具。一次性问答可以直接问模型；本包的价值在于把来源、判断、摘要、矛盾和后续问题沉淀成可复用的 wiki。

## 2. 前置条件

当前包依赖：

- [uv](https://docs.astral.sh/uv/)，用于 Python 环境管理。初始化脚本会运行 `uv sync`。
- PowerShell，用于在 Windows 运行初始化脚本 [scripts/init.ps1](../scripts/init.ps1)。
- Bash，用于在 macOS 或 Linux 运行初始化脚本 [scripts/init.sh](../scripts/init.sh)。
- Obsidian 或任意可以浏览 Markdown 文件的编辑器。
- 一个能读取项目说明文件的 agent，例如 Codex、Claude Code、Gemini CLI、OpenCode 或类似工具。

初始化脚本会检查 `uv`。如果本机没有 `uv`，脚本会尝试通过官方安装脚本安装；安装失败时，按脚本提示手动安装后重新运行。

## 3. 安装

进入仓库目录：

```powershell
cd llm-wiki-agent
```

在 Windows 初始化当前目录：

```powershell
.\scripts\init.ps1 -VaultRoot .
```

在 macOS 或 Linux：

```sh
./scripts/init.sh -VaultRoot .
```

或把 wiki 结构创建到一个单独的 Obsidian vault：

```powershell
.\scripts\init.ps1 -VaultRoot "C:\path\to\your\vault"
```

```sh
./scripts/init.sh -VaultRoot "/path/to/your/vault"
```

脚本会执行两件事：

1. 在 agent 包目录运行 `uv sync`，创建或同步 `.venv/`。
2. 在 `-VaultRoot` 指定的位置创建 `inbox/`、`raw/`、`intake/`、`wiki/` 等目录。

`.venv/` 是本地环境目录，不应提交到 git。

## 4. 目录结构

初始化后的 wiki 结构如下：

```text
.
├── inbox/
├── raw/
│   ├── digested/
│   ├── needs-review/
│   ├── ignored/
│   └── unsupported/
├── intake/
│   ├── tmp/
│   ├── processed/
│   └── logs/
├── reviews/
│   ├── source-review/
│   └── reflection/
├── logs/
│   └── wiki.md
├── questions/
├── artifacts/
└── wiki/
    ├── home.md
    ├── index.md
    ├── overview.md
    ├── sources/
    ├── entities/
    ├── concepts/
    ├── claims/
    └── syntheses/
```

核心职责：

| 目录 | 职责 |
| --- | --- |
| `inbox/` | 用户投递原始文件的唯一入口。 |
| `raw/` | 保存原始文件的最终状态，不保存 agent 生成的 Markdown。 |
| `intake/tmp/` | 转换后、审查前的临时 Markdown。 |
| `intake/processed/` | 已通过审查、可用于 wiki ingest 的 Markdown。 |
| `reviews/` | source review 和 discussion reflection 记录。 |
| `wiki/` | 可持续维护的知识页面。 |
| `questions/` | 未解决问题和调查线索。 |
| `artifacts/` | 面向用户的报告、brief、草稿、模板等交付物。 |

## 5. 第一次处理文件

把原始文件放入 `inbox/`：

```text
inbox/
└── example.md
```

向 agent 发出请求：

```text
请按照 AGENTS.md 和 WIKI.md 处理 inbox/ 中的文件。
```

agent 应按以下顺序处理：

1. 读取 [AGENTS.md](../AGENTS.md)，确认任务属于 Add Knowledge。
2. 读取 [WIKI.md](../WIKI.md)，使用其中的 intake 和 source review 规则。
3. 检查 `inbox/` 中的完整文件名、类型、大小和可读性。
4. 将可处理内容转换或规范化到 `intake/tmp/YYYY-MM-DD/source-slug/source.md`。
5. 基于临时 Markdown 运行 Source Review Gate。
6. 将原始文件移动到 `raw/digested/`、`raw/needs-review/`、`raw/ignored/` 或 `raw/unsupported/`。
7. 只有 `digested` 内容进入 `intake/processed/` 并继续更新 `wiki/`。
8. 更新 `reviews/source-review/`、`intake/logs/`、`wiki/index.md` 和 `logs/wiki.md`。

## 6. Source Review Gate

Source Review Gate 决定一个 source 是否值得进入 wiki。

| 结果 | 原始文件位置 | 后续动作 |
| --- | --- | --- |
| `digested` | `raw/digested/` | 进入 `intake/processed/`，创建 source card，并更新 wiki。 |
| `needs-review` | `raw/needs-review/` | 记录需要用户判断的问题，暂不更新 wiki。 |
| `ignored` | `raw/ignored/` | 记录忽略原因，暂不更新 wiki。 |
| `unsupported` | `raw/unsupported/` | 记录无法处理的原因，暂不更新 wiki。 |

转换命令成功不代表 source 可用。乱码、空内容、明显截断、结构破碎、缺失关键文本、依赖图片或扫描页的信息，都应进入 `needs-review` 或 `unsupported`。

## 7. 文本优先边界

当前工作流是 text-first：

- Markdown、网页、PDF、Word、PowerPoint、Excel、CSV、JSON、XML 等文件应先转为可审查 Markdown。
- 图片、扫描件、截图和音频可以作为原始来源保存，但默认不是 wiki 的一等内容。
- 如果某个文件的重要信息依赖未处理的图片、扫描页、截图或音频，移动到 `raw/needs-review/` 并记录缺失处理步骤。
- 不要默认创建附件资源目录、复制图片到 wiki 页面，或添加图片引用方案。

## 8. 使用已有知识

当你想从 wiki 中获得答案时，向 agent 提问：

```text
wiki 里关于 <主题> 是怎么说的？
```

agent 应先读：

1. `wiki/index.md`
2. `wiki/overview.md`
3. 相关 `wiki/sources/`、`wiki/entities/`、`wiki/concepts/`、`wiki/claims/`、`wiki/syntheses/`
4. 必要时读取 `questions/` 和 `artifacts/`

需要生成报告、brief、outline、draft、模板或对比表时，交付物应写入 `artifacts/`。

## 9. 讨论内容回流

讨论产生的长期有效知识使用 Reflect 处理。适合回流的内容包括：

- 用户确认的偏好。
- 工作流规则。
- 架构判断。
- 可长期复用的结论。
- 已确认的概念关系或待研究问题。

没有明确要求时，agent 应先列出建议回流的要点并等待确认。确认后，讨论来源记录写入 `reviews/reflection/YYYY-MM-DD.md`。

## 10. 维护 Wiki

可以使用这些自然语言请求：

```text
检查 wiki 健康状态
查找断开的链接
查找过期的 claim
清理重复页面
检查没有来源的 claim
```

agent 可以直接修复机械问题。涉及解释、合并、删除、来源判断变化的问题，应先给出方案并等待确认。

## 11. 常见问题

### uv 不存在怎么办

先运行初始化脚本。脚本会尝试安装 `uv`。如果安装失败，手动安装 `uv`，然后重新运行：

```powershell
.\scripts\init.ps1 -VaultRoot .
```

### 文件已经放进 raw/ 了怎么办

把用户新投递的原始文件放回 `inbox/` 再处理。`raw/` 是处理后的状态区，不是入口。

### 为什么文件进了 needs-review

`needs-review` 表示文件可能有价值，但 agent 当前不能可靠完成最终判断。常见原因包括内容太大、转换质量差、缺少关键图片信息、来源范围不清、压缩包需要选择成员、或内容需要用户判断。

### 可以直接把转换结果写进 wiki 吗

不可以。转换结果先进入 `intake/tmp/`，通过 Source Review Gate 后才能进入 `intake/processed/`，然后再更新 `wiki/`。

### GitHub 仓库里要提交个人 wiki 内容吗

公开分享本 agent 包时，不建议提交个人 `inbox/`、`raw/`、`intake/`、`wiki/`、`logs/`、`questions/` 或 `artifacts/` 内容。默认 [.gitignore](../.gitignore) 会忽略这些本地运行目录。

## 12. 推荐工作习惯

- 小批量投递 source，先确认一轮 intake 质量，再增加规模。
- 对大文件先让 agent 读 metadata、目录、页数、行数或 chunk index。
- 对有争议的 claim 保留反证和不确定性，不要压成单一结论。
- 经常要求 agent 运行 Maintain Wiki，检查断链、重复页面、无来源 claim 和过期内容。
- 把用户交付物放在 `artifacts/`，把长期知识放在 `wiki/`。

<h1 align="center"><b>📖 使用指南</b></h1>

<p align="center">
  <b><i><font size="4">如何安装、初始化和操作 LLM Wiki Agent。</font></i></b>
</p>

<p align="center">
  <a href="usage.zh-CN.md">🇨🇳 中文</a> ·
  <a href="usage.md">🇬🇧 English</a>
</p>

<p align="center">
  <a href="../README.zh-CN.md">🏠 返回首页</a> · <a href="../AGENTS.md">🤖 智能体规则</a> · <a href="../WIKI.md">🧠 Wiki 规则</a> · <a href="../PROJECT.md">⚙️ 项目上下文</a>
</p>

---

> **注意：** [AGENTS.md](../AGENTS.md) 是智能体入口。 [PROJECT.md](../PROJECT.md) 包含了当前工作区的配置项。 [WIKI.md](../WIKI.md) 是核心的操作指南。 请保持 `WIKI.md` 稳定，而日常的个性化设置请修改 `PROJECT.md`。

## 🎯 1. 适用场景

**LLM Wiki Agent 非常适合处理：**
- 研究笔记、文章、论文和剪辑的网页。
- 项目知识、决策记录、会议纪要和技术调研。
- 个人知识库、阅读笔记和主题归档。
- 需要溯源、关注声明、不确定性和矛盾的查询驱动型知识库。

它**不是**用来进行一次性闲聊的工具。它的核心价值在于持久化的积累：将来源、判断和矛盾点作为可复用的 wiki 知识妥善保存。

---

## ⚙️ 2. 环境要求

开始前，请确保你拥有：
- [uv](https://docs.astral.sh/uv/)，用于 Python 环境管理 (初始化脚本会运行 `uv sync`)。
- PowerShell (Windows) 或 Bash (macOS/Linux) 用于执行初始化脚本。
- Obsidian，或任何标准的 Markdown 编辑器。
- 一个能够读取仓库级别指令的 AI 智能体 (例如 Codex, Claude Code, Gemini CLI, OpenCode)。

---

## 🚀 3. 安装与初始化

```bash
cd llm-wiki-agent

# Windows
.\scripts\init.ps1 -VaultRoot .

# macOS / Linux
./scripts/init.sh -VaultRoot .
```

若要在单独的现有 Obsidian 库中创建结构：
```bash
# Windows
.\scripts\init.ps1 -VaultRoot "C:\path\to\your\vault"

# macOS / Linux
./scripts/init.sh -VaultRoot "/path/to/your/vault"
```

**它的作用是：**
1. 运行 `uv sync` 来创建或更新 `.venv/` 本地运行环境。
2. 创建所有必要的工作流目录 (`inbox/`, `raw/`, `intake/`, `wiki/` 等)。

---

## 📂 4. 目录结构与职责

| 目录 | 职责说明 |
| --- | --- |
| `inbox/` | 📥 用户提交原始文件的**唯一入口**。 |
| `raw/` | 🗄️ 原始文件的最终存放地。(不存放智能体生成的 Markdown)。 |
| `intake/tmp/` | ⚙️ 存放转换后且未进行来源审查前的临时 Markdown 文件。 |
| `intake/processed/` | ✅ 存放已接受并准备写入 wiki 的 Markdown 文件。 |
| `reviews/` | 📝 存放来源审查记录与讨论反射记录。 |
| `logs/` | ⏱️ 存放高维度的 wiki 操作历史记录 (`logs/wiki.md`)。 |
| `wiki/` | 🧠 存放持久化的知识库页面。 |
| `questions/` | ❓ 存放悬而未决的问题与调查线索。 |
| `artifacts/` | 📦 存放报告、简报、草案、模板等面向用户的交付物。 |

---

## 📥 5. 首次摄入文件工作流

遵循以下生命周期来添加新知识：

1. **放入文件：** 将原始文件放入 `inbox/` (如 `inbox/example.md`)。
2. **提示智能体：** 询问智能体：*"请根据 AGENTS.md, PROJECT.md 和 WIKI.md 处理 inbox/ 中的文件。"*
3. **智能体操作：** 
    - 智能体将内容转换为 `intake/tmp/YYYY-MM-DD/source.md`。
    - 它会执行 **来源审查门 (Source Review Gate)**。
    - 原始文件被移入 `raw/` 下对应的状态子目录。
    - 只有被标记为 `digested` (已通过) 的内容才会被移至 `intake/processed/` 并用于更新 `wiki/`。

---

## 🔍 6. 来源审查门 (Source Review Gate) 结果

来源审查门是决定一个来源是否有资格进入 wiki 的严格边界。

| 审查结果 | 目标路径 | 下一步动作 |
| --- | --- | --- |
| **`digested`** | `raw/digested/` | 推进至 `intake/processed/`，创建来源卡片，更新 wiki。 |
| **`needs-review`**| `raw/needs-review/`| 记录审查疑问。(如需要人工判断或图像处理)。**暂不更新 wiki**。 |
| **`ignored`** | `raw/ignored/` | 记录忽略理由。**不更新 wiki**。 |
| **`unsupported`** | `raw/unsupported/` | 记录阻碍原因。**不更新 wiki**。 |

> [!WARNING]
> 一次成功的格式转换**不**代表它会被自动接受进入 wiki。空白、乱码或严重依赖图片的文件会被标记为 `needs-review`。

---

## 📜 7. 文本优先边界 (Text-First)

LLM Wiki Agent 严格遵循“文本优先”思维进行操作：
- 所有可读文档 (HTML, PDF, Word, PPT, Excel 等) 在摄入前都会转为 Markdown。
- 扫描件、图片和音频作为原始来源保留在 `raw/`，但它们**不是**一等公民 (wiki 内容)。
- 除非已明确配置图片处理机制，否则不要将图片直接复制到 wiki 页面内。

> [!TIP]
> 关于 OCR 处理，请参考 [markitdown-ocr.zh-CN.md](markitdown-ocr.zh-CN.md)。OCR 是可选的，并且默认不开启。

---

## 🧠 8. 使用现有知识

要使用知识库，请询问智能体：
*"wiki 里面关于 <topic> 是怎么说的？"*

智能体会搜索：
1. `wiki/index.md` & `wiki/overview.md`
2. `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `wiki/claims/`
3. `questions/` 和 `artifacts/`

智能体应当将生成的所有交付物 (报告、模板、草案) 放置在 `artifacts/` 目录中。

---

## 🪞 9. 反射 (Reflect) 讨论知识

你可以要求智能体通过“反射”固化讨论中的知识，例如：
- 确认的用户偏好
- 架构层面的判定
- 可复用的结论

这些内容将被写入 `reviews/reflection/YYYY-MM-DD.md`。

---

## 🧹 10. 维护 Wiki

通过以下询问来进行定期的维护：
- *"对 wiki 进行健康检查"*
- *"找出死链 (broken links)"*
- *"清理重复内容"*
- *"找出没有来源引用的声明 (claims)"*

---

## ❓ 11. 常见问题 (FAQ)

<details>
<summary><b>如果找不到 <code>uv</code> 怎么办？</b></summary>
先运行初始化脚本。如果自动安装失败，请手动安装 <code>uv</code> 然后再次运行初始化脚本。
</details>

<details>
<summary><b>如果文件已经在 <code>raw/</code> 里面了呢？</b></summary>
新提交的原始文件必须通过 <code>inbox/</code> 进入。 <code>raw/</code> 是一个审查后的状态保留区，而不是摄入的入口。
</details>

<details>
<summary><b>转换后的 Markdown 能不能直接放进 <code>wiki/</code>？</b></summary>
不行。转换后的 Markdown 首先会进入 <code>intake/tmp/</code>，接受来源审查门 (Source Review Gate) 的检查。只有通过的材料才能进入 <code>intake/processed/</code>，最后写入 <code>wiki/</code>。
</details>

<details>
<summary><b>我应该把个人 wiki 内容提交到 GitHub 吗？</b></summary>
不要。默认的 <code>.gitignore</code> 会忽略本地运行目录，比如 <code>inbox/</code>, <code>raw/</code>, <code>intake/</code> 和 <code>wiki/</code>。
</details>

---

## 💡 12. 推荐习惯

- 将源文件分为小批量处理，等确认一个摄入周期成功后再批量导入。
- 面对大文件，先让智能体检查其元数据或分块索引。
- 面对有争议的声明时，保留其反证依据和不确定性。
- 定期运行 **Maintain Wiki (维护 Wiki)** 任务。
- 将面向用户的交付产物放在 `artifacts/`，而将持久化的知识放在 `wiki/`。

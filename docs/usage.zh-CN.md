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
- [uv](https://docs.astral.sh/uv/)，用于 Python 环境管理 (初始化脚本会依据锁文件并使用官方 PyPI 索引运行 `uv sync --locked`)。
- PowerShell (Windows) 或 Bash (macOS/Linux) 用于执行初始化脚本。
- 当你要使用默认网页提取器时，需要 Node.js/npm 或已安装的 Defuddle CLI。
- 任意标准 Markdown 编辑器；Obsidian 是可选项。
- 一个能够读取仓库指令、编辑文件并执行所需命令的智能体运行时。

### 推荐的智能体运行时

本工作流包不依赖特定智能体平台。作为默认配置，本指南推荐使用 [OpenCode](https://opencode.ai/docs/)。请按照 OpenCode 的最新文档完成安装和配置，然后从初始化后的工作根目录启动。其他兼容的智能体运行时仍然受支持。

```bash
opencode auth login
opencode
```

---

## 🚀 3. 安装与初始化

```bash
cd llm-wiki-agent

# Windows
.\scripts\init.ps1 -VaultRoot .

# macOS / Linux
./scripts/init.sh -VaultRoot .
```

若要在单独的工作目录中创建结构，包括现有 Obsidian 库：
```bash
# Windows
.\scripts\init.ps1 -VaultRoot "C:\path\to\your\vault"

# macOS / Linux
./scripts/init.sh -VaultRoot "/path/to/your/vault"
```

外部根目录初始化完成后，请从初始化后的根目录打开或运行智能体。目标目录会得到包管理的入口文件、本地技能、脚本、文档、运行目录和项目环境。目标目录中已有的包管理文件会被包副本替换；工作区个性化偏好应放在 `PROJECT.md`。

**它的作用是：**
1. 将包管理的入口文件、本地技能、脚本和文档安装到目标根目录。
2. 在缺失时创建 `PROJECT.md`，并将来源提取偏好放在那里，由智能体在需要时确认，包括是否配置 MinerU、API 模式下使用哪个 MinerU profile，以及 MinerU 可用时是否优先使用 MinerU。
3. 补齐缺失的工作流目录和默认 wiki 文件 (`inbox/`, `raw/`, `intake/`, `reviews/`, `logs/`, `wiki/` 等)，不覆盖已有运行内容。
4. 在 `.gitignore` 缺失时写入默认模板；如果已有 `.gitignore` 没有 wiki 运行目录策略，则追加默认私有运行目录段落。
5. 在初始化后的根目录运行 `uv sync --locked --default-index https://pypi.org/simple`，根据已提交的锁文件创建或更新 `.venv` 本地运行环境。

### 可选的 Obsidian 与 Claudian 界面

Obsidian 和 Claudian 都不是必需项。本工作流包可以通过文件系统配合任意兼容智能体运行时工作。如果你希望在 Obsidian 中使用内嵌的智能体界面，请按照 [YishenTu/claudian 仓库](https://github.com/YishenTu/claudian)或 [Claudian 官网](https://claudian.xyz/zh/)的最新安装说明操作，然后查看 [provider 文档](https://claudian.xyz/zh/docs/providers/)。

在这条可选的 Claudian 使用路径中，本工作流包默认推荐选择 OpenCode provider。这是本工作流包的配置建议，并不表示 OpenCode 是 Claudian 唯一支持的 provider；Claudian 支持的其他 provider 仍然可以使用。

### 可选场景包

`scenarios/` 下的场景包为特定类型的工作区提供可选初始化指导。它们不会在基础初始化时自动生效。普通初始化脚本完成后，需要明确要求智能体应用某个场景，例如：

```text
根据 scenarios/exam-study/ 初始化当前库。
先读场景 README，再询问我 PROJECT.md 中需要确认的字段，
然后用 starter-pages.md 创建最小有用的起始页面。
```

场景初始化只能把已确认的项目级取值写入 `PROJECT.md`，只创建当前场景需要的最小起始页面，并保持 `WIKI.md` 和 `AGENTS.md` 不变。

### 升级包文件

将新版本包应用到已有工作区时，使用升级脚本：

```bash
# Windows
.\scripts\upgrade.ps1 -TargetRoot "C:\path\to\your\workspace"

# macOS / Linux
./scripts/upgrade.sh -TargetRoot "/path/to/your/workspace"
```

升级会处理 `scripts/upgrade-manifest.txt` 中列出的条目，在缺失时创建 `PROJECT.md`，补齐缺失的运行目录和默认 wiki 文件，并在目标根目录运行 `uv sync --locked --default-index https://pypi.org/simple`。列出的文件会被覆盖；列出的目录，包括 `scenarios/`，会按包文件合并覆盖，并保留目标目录中额外存在的条目。已有 `.gitignore` 会被保留；缺失的本地基线规则会被补齐，只有在不存在 wiki 运行目录策略时才会追加默认私有运行目录段落。工作区个性化配置应放在 `PROJECT.md`。

### 本地服务密钥

当 provider 需要本地凭据或部署专属 endpoint 时，请将 `.env.example` 复制为初始化后根目录中的 `.env`，并只填写所选 provider profile 需要的变量。

配置需要 smoke check 的 provider profile 后，首次提取前应先运行该检查。具体检查内容和所需本地变量由 profile 定义。

首次确认项目上下文时，或来源提取偏好仍未确认时，智能体会询问你是否要配置 MinerU、API 模式下使用哪个 MinerU profile，以及 MinerU 可用时是否优先用于受支持的文档。如果你选择优先 MinerU，智能体会在 `PROJECT.md` 中把文档默认 provider 记录为 MinerU。如果你不配置或不设为优先，MarkItDown 仍是普通文档的默认 provider，MinerU 只用于明确选择或复杂文档提取。

真实 `.env` 是本地运行配置，已被 Git 忽略，不能写入 `PROJECT.md`, `WIKI.md`, manifest, log, review note, wiki 页面、source card 或提示词。依赖 `.env` 的智能体命令必须从项目根目录通过 `uv run --env-file .env ...` 运行；如果同一个 shell 中要重复执行 `uv run`，也可以先设置 `UV_ENV_FILE=.env`。

初始化和升级脚本只安装不含密钥的 `.env.example` 模板，不会创建或覆盖真实 `.env`。

---

## 📂 4. 目录结构与职责

| 目录 | 职责说明 |
| --- | --- |
| `inbox/` | 📥 提交原始文件和实时 URL 来源捕获文件的入口。 |
| `raw/` | 🗄️ 生命周期来源工件的状态存放地，并保留来源相对路径。Defuddle URL 捕获文件是唯一允许存放于此的生成来源工件。 |
| `intake/tmp/` | ⚙️ 存放提取后且未进行来源审查前的临时 Markdown 文件。 |
| `intake/processed/` | ✅ 存放已接受并准备写入 wiki 的 Markdown 文件。 |
| `reviews/` | 📝 存放来源审查记录与讨论反射记录。 |
| `logs/` | ⏱️ 存放高维度的 wiki 操作历史记录 (`logs/wiki.md`)。 |
| `wiki/` | 🧠 存放持久化的知识库页面。 |
| `questions/` | ❓ 存放悬而未决的问题与调查线索。 |
| `artifacts/` | 📦 存放报告、简报、草案、模板等面向用户的交付物。 |

---

## 📥 5. 首次摄入来源工作流

精确生命周期规则以 [WIKI.md](../WIKI.md) 为准。第一次小规模摄入通常如下：

1. **提交来源：** 将原始文件放入 `inbox/`，或者把一个实时 URL 交给智能体。
2. **提示智能体：** 询问智能体：*"请根据 AGENTS.md、PROJECT.md 和 WIKI.md 处理这些来源。"*
3. **预期结果：**
    - 实时 URL 会由 Defuddle 处理一次，生成 `inbox/web/<页面标题>--<URL 哈希>.md`；该捕获文件随后与提交的 Markdown 文件走同一生命周期。
    - 临时 Markdown 会出现在 `intake/tmp/<source-relative-parent>/<source-base-filename>/source.md`。如果输入文件位于嵌套目录，输出会保留其来源相对父路径。
    - **来源审查门 (Source Review Gate)** 会决定最终来源状态。
    - 生命周期来源工件会被移入 `raw/` 下对应的状态子目录，并保留其在 `inbox/` 下的相对路径。
    - 只有被标记为 `digested` 的内容才会被移至 `intake/processed/` 并用于更新 `wiki/`。

如需查看包含中间状态和最终目录状态的批量示例，请阅读 [来源生命周期示例](source-lifecycle.zh-CN.md)。

用户可以直接使用自然语言提出请求，例如：

- *"处理 raw 文件"*
- *"审查来源"*
- *"摄入这个来源"*
- *"捕获并摄入这个 URL"*
- *"wiki 里关于这个主题是怎么说的？"*
- *"创建一个 artifact"*
- *"对 wiki 做健康检查"*

---

## 🔍 6. 来源审查门 (Source Review Gate) 结果

这里是快速参考。权威的来源审查门规则以 [WIKI.md](../WIKI.md) 为准。

| 审查结果 | 目标路径 | 下一步动作 |
| --- | --- | --- |
| **`digested`** | `raw/digested/<source-relative-path>` | 推进至 `intake/processed/`，创建来源卡片，更新 wiki。 |
| **`needs-review`**| `raw/needs-review/<source-relative-path>`| 记录审查疑问。(如需要人工判断或图像处理)。**暂不更新 wiki**。 |
| **`ignored`** | `raw/ignored/<source-relative-path>` | 记录忽略理由。**不更新 wiki**。 |
| **`unsupported`** | `raw/unsupported/<source-relative-path>` | 记录阻碍原因。**不更新 wiki**。 |

> [!WARNING]
> 一次成功的来源提取**不**代表它会被自动接受进入 wiki。空白、严重乱码、结构破损或严重依赖图片的文件会被标记为 `needs-review`。如果主体内容约半数以上不可读，就不能把它当作质量良好的输入。

---

## 📜 7. 文本优先边界 (Text-First)

LLM Wiki Agent 采用文本优先的摄入路径：
- 所有可读文档 (HTML, PDF, Word, PPT, Excel 等) 在摄入前都会转为 Markdown。
- 扫描件、图片、音频和视频作为原始来源保留在 `raw/`，但除非已明确配置并批准提取，否则它们**不是**一等公民 (wiki 内容)。
- 所选提供方已经返回的图片可以自动保存在 `source.md` 所在的 intake 目录中，并随该目录一起推进或删除。
- 除非已明确配置并批准图片处理，否则不要把图片放入 wiki 页面，也不要执行 OCR 或视觉解释。

---

## 🧠 8. 使用现有知识

要使用知识库，请询问智能体：
*"wiki 里面关于 <topic> 是怎么说的？"*

智能体会先用 `wiki/index.md`、`wiki/overview.md`、搜索、标题或链接索引定位相关范围，然后只读取相关页面或章节：
1. `wiki/index.md` 中的导航条目，以及 `wiki/overview.md` 中的相关综合章节
2. `wiki/sources/`、`wiki/entities/`、`wiki/concepts/`、`wiki/claims/`、`wiki/syntheses/` 下的相关页面
3. `questions/` 和 `artifacts/` 中的相关调查记录与交付物

报告、模板、草案等生成交付物应放在 `artifacts/` 目录中。

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
<summary><b>如果找不到 Defuddle 怎么办？</b></summary>
默认实时 URL 捕获提供方是 Defuddle。请通过 npm 安装，或让智能体按照 <code>.agents/skills/source-extraction/references/providers/defuddle/setup.md</code> 执行。实时 URL 不会直接进入 <code>intake/tmp/</code>；Defuddle 会先在 <code>inbox/web/</code> 下生成来源捕获文件。
</details>

<details>
<summary><b>如果文件已经在 <code>raw/</code> 里面了呢？</b></summary>
新的来源工件必须通过 <code>inbox/</code> 进入。提交文件保持不变；实时 URL 则以确定性的 Defuddle 来源捕获文件进入。已经位于 <code>raw/&lt;state&gt;/</code> 中的工件可以从当前状态目录继续重新处理，因为它已经进入过生命周期。重新处理时必须保留 <code>raw/&lt;state&gt;/</code> 之后的相对路径；当来源移动到新状态时，旧状态目录中的那份必须移除。
</details>

<details>
<summary><b>提取后的 Markdown 能不能直接放进 <code>wiki/</code>？</b></summary>
不行。提取后的 Markdown 首先会进入 <code>intake/tmp/</code>，接受来源审查门 (Source Review Gate) 的检查。只有通过的材料才能进入 <code>intake/processed/</code>，最后写入 <code>wiki/</code>。
</details>

<details>
<summary><b>我应该把个人 wiki 内容提交到 GitHub 吗？</b></summary>
默认不要。包默认配置会让本地运行目录保持私有。如果这个 checkout 是个人或团队 wiki 项目，并且持久化 wiki 内容需要进入版本库，请参考<a href="gitignore-templates.zh-CN.md">Git Ignore 模板</a>。
</details>

---

## 💡 12. 推荐习惯

- 将源文件分为小批量处理，等确认一个摄入周期成功后再批量导入。
- 面对大文件，先让智能体检查其元数据或分块索引。
- 面对有争议的声明时，保留其反证依据和不确定性。
- 定期运行 **Maintain Wiki (维护 Wiki)** 任务。
- 将面向用户的交付产物放在 `artifacts/`，而将持久化的知识放在 `wiki/`。

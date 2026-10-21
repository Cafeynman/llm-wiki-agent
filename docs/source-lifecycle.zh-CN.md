# 来源生命周期示例

这个示例说明 `inbox/` 中一批文件的预期生命周期。核心合同以 `WIKI.md` 为准，详细步骤由 `.agents/skills/source-extraction/references/intake-lifecycle.md` 维护；本文件只是示例。

## 实时 URL 入口

提交的实时 URL 会在普通 intake 之前被固化：

```text
submitted URL
`-- Defuddle structured Markdown
    `-- inbox/web/<页面标题>--<URL 哈希>.md
        `-- intake/tmp/web/<页面标题>--<URL 哈希>/source.md
```

`inbox/web/` 下的捕获文件是生命周期来源工件。它会在同一轮处理内离开 `inbox/`，并移动到唯一的 `raw/<state>/web/` 目标。Defuddle 不会再次处理这个捕获文件。

## 初始状态

```text
.
`-- inbox/
    |-- paper.pdf
    |-- notes.md
    |-- bundle/
    |   `-- report.pdf
    |-- slides.pptx
    |-- duplicate.html
    `-- corrupted.pdf
```

## 临时提取

Intake 先暂存 Markdown 文件，或将非 Markdown 原始文件提取为临时 Markdown。提供方返回的附件保存在同一临时来源目录中，并随该目录推进、保留待审或在终态清理：

```text
.
|-- inbox/
|   |-- paper.pdf
|   |-- notes.md
|   |-- bundle/
|   |   `-- report.pdf
|   |-- slides.pptx
|   |-- duplicate.html
|   `-- corrupted.pdf
`-- intake/
    `-- tmp/
        |-- paper/
        |   |-- source.md
        |   |-- digest.md
        |   `-- chunks/
        |       |-- index.md
        |       |-- 01-概述.md
        |       `-- 02-方法.md
        |-- notes/
        |   `-- source.md
        |-- bundle/
        |   `-- report/
        |       `-- source.md
        |-- slides/
        |   |-- source.md
        |   `-- digest.md
        `-- duplicate/
            `-- source.md
```

每个 `source.md` 创建后，对该文件运行 source-extraction 的 intake file audit。正常文件在人类输出模式下保持安静，JSON 模式始终返回 schema 2。空白、占位、导航 stub 和无可评审文本会在 Source Review Gate 前停止。若审计报告 `large_source`，并且来源中存在可靠语义边界，则在 Source Review Gate 前创建语义化 `chunks/`，保留 canonical `source.md` 的正文与顺序；显式授权的图片标记调整遵循 `intake-lifecycle.md`。新 Chunk 路径使用 `01-概述.md` 这样的稳定序号与语义标题；就近索引决定阅读顺序，并保留来源原文标题和顺序标记。既有数字路径仍可读取；插入块不强制改名其他块。每个非空 leaf 低于 2000 单位都提示，脚本不判断是否适合合并；高于 10000 单位则 hard fail。评审者可在就近 index 行直接写入 `accepted-under — 理由` 或 `accepted-over — 理由`，并把状态标为 `reviewed`；审计每次扫描都会重算单位与类别。创建 chunks 后，对临时 intake 文件夹运行 chunk audit；推进前先解决 hard errors，将未解决 warnings 带入审查记录。

`digested` 文件夹到达最终 `intake/processed/` 路径后，对该文件夹或每个最终改动的 Markdown 文件运行聚焦 Obsidian lint，并在 ingest 前解决断链。只有显式目标目录内唯一的文件名前缀截断可以在审核 dry-run 后机械修复；歧义和模糊候选继续报告。

如果 `corrupted.pdf` 无法提取，应立即停止处理该文件：

```text
.
|-- inbox/
|   |-- paper.pdf
|   |-- notes.md
|   |-- bundle/
|   |   `-- report.pdf
|   |-- slides.pptx
|   `-- duplicate.html
|-- raw/
|   `-- unsupported/
|       `-- corrupted.pdf
`-- intake/
    `-- logs/
        `-- YYYY-MM-DD.md
```

## 来源审查门

然后基于临时 Markdown 和可选 digest 执行 Source Review Gate：

| 文件 | 审查输入 | 结果 | 后续处理 |
| --- | --- | --- | --- |
| `paper.pdf` | `intake/tmp/paper/source.md`, chunks, digest | `digested` | 推进到 `intake/processed/`，原件移动到 `raw/digested/`，清理 `intake/tmp/`，更新 wiki |
| `notes.md` | `intake/tmp/notes/source.md` | `digested` | 推进到 `intake/processed/`，原件移动到 `raw/digested/`，清理 `intake/tmp/`，更新 wiki |
| `bundle/report.pdf` | `intake/tmp/bundle/report/source.md` | `digested` | 推进到 `intake/processed/bundle/report/`，原件移动到 `raw/digested/bundle/report.pdf`，创建 `wiki/sources/bundle/report.md` |
| `slides.pptx` | `intake/tmp/slides/source.md`, digest | `needs-review` | 原件移动到 `raw/needs-review/`，记录待审问题，保留有用的 `intake/tmp/` 输出 |
| `duplicate.html` | `intake/tmp/duplicate/source.md` | `ignored` | 原件移动到 `raw/ignored/`，记录忽略理由，清理 `intake/tmp/` |
| `corrupted.pdf` | extraction failure | `unsupported` | 原件移动到 `raw/unsupported/`，记录阻碍原因 |

## 最终状态

已接受文件完成 ingest 后：

```text
.
|-- inbox/
|-- raw/
|   |-- digested/
|   |   |-- paper.pdf
|   |   |-- notes.md
|   |   `-- bundle/
|   |       `-- report.pdf
|   |-- needs-review/
|   |   `-- slides.pptx
|   |-- ignored/
|   |   `-- duplicate.html
|   `-- unsupported/
|       `-- corrupted.pdf
|-- intake/
|   |-- tmp/
|   |   `-- slides/
|   |       |-- source.md
|   |       `-- digest.md
|   |-- processed/
|   |   |-- paper/
|   |   |   |-- source.md
|   |   |   |-- summary.md
|   |   |   |-- manifest.md
|   |   |   |-- digest.md
|   |   |   `-- chunks/
|   |   |       |-- index.md
|   |   |       |-- 01-概述.md
|   |   |       `-- 02-方法.md
|   |   |-- notes/
|   |   |   |-- source.md
|   |   |   |-- summary.md
|   |   |   `-- manifest.md
|   |   `-- bundle/
|   |       `-- report/
|   |           |-- source.md
|   |           |-- summary.md
|   |           `-- manifest.md
|   `-- logs/
|       `-- YYYY-MM-DD.md
|-- reviews/
|   `-- source-review/
|       `-- YYYY-MM-DD.md
|-- logs/
|   `-- wiki.md
`-- wiki/
    |-- home.md
    |-- index.md
    |-- overview.md
    |-- sources/
    |   |-- paper.md
    |   |-- notes.md
    |   `-- bundle/
    |       `-- report.md
    `-- concepts/
        `-- relevant-concept.md
```

关键不变量是：来源审查发生在提取之后，因为审查对象应当是可读 Markdown 或 digest 输出。原始文件只在提取和审查产生最终决定后移动。

`raw/needs-review/` 中的文件会保持待处理状态，直到对应审查问题被解决。有用的提取结果和附件可保留在对应 `intake/tmp/` 目录中，确认其属于当前原件后继续使用；没有可用提取结果时不要求存在临时目录。它们不会更新 wiki 页面，也不会作为已接受来源出现，直到后续审查将其标记为 `digested`。

## 检查一个已完成来源

来源处理完成后，以最终 raw 路径运行只读收尾检查：

```powershell
uv run --no-project .agents/skills/source-extraction/scripts/audit_source_closeout.py raw/digested/manual.pdf --vault . --json
```

保留 ingest 前的局部 intake lint 和 ingest 后的收尾检查。两者统一的是页面规则边界：保留来源原文语法，对编写的 intake 维护记录应用页面规则。收尾检查还会核对 frontmatter 中的 intake 溯源链接；局部 lint 的导航诊断会排除这些链接。

检查组合来源状态、已有 intake 与 chunk 审计和相关链接，不修复文件，也不因其他来源尚未完成而阻塞当前来源。通过只说明结构检查没有发现错误，不代表提取完整性或知识质量已获确认。收尾检查的边界与按来源、章节委托的写入责任，见 source-extraction 的 `references/intake-lifecycle.md`。

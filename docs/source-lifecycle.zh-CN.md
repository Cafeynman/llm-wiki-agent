# 来源生命周期示例

这个示例说明 `inbox/` 中一批文件的预期生命周期。规范性规则仍以 `WIKI.md` 为准；本文件只是示例。

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

Intake 先暂存 Markdown 文件，或将非 Markdown 原始文件提取为临时 Markdown：

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
        |       |-- 01.md
        |       `-- 02.md
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
| `slides.pptx` | `intake/tmp/slides/source.md`, digest | `needs-review` | 原件移动到 `raw/needs-review/`，记录待审问题，清理 `intake/tmp/` |
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
|   |-- processed/
|   |   |-- paper/
|   |   |   |-- source.md
|   |   |   |-- summary.md
|   |   |   |-- manifest.md
|   |   |   |-- digest.md
|   |   |   `-- chunks/
|   |   |       |-- index.md
|   |   |       |-- 01.md
|   |   |       `-- 02.md
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

`raw/needs-review/` 中的文件会保持待处理状态，直到对应审查问题被解决。它们不会更新 wiki 页面，也不会作为已接受来源出现，直到后续审查将其标记为 `digested`。

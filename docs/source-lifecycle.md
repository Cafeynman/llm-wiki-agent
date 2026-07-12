# Source Lifecycle Example

This example shows the intended lifecycle for a batch of files in `inbox/`. The normative rules remain in `WIKI.md`; this file is only an example.

## Live URL Entry

A submitted live URL is materialized before ordinary intake:

```text
submitted URL
`-- Defuddle structured Markdown
    `-- inbox/web/<page-title>--<url-hash>.md
        `-- intake/tmp/web/<page-title>--<url-hash>/source.md
```

The capture under `inbox/web/` is the lifecycle source artifact. It leaves `inbox/` in the same pass and moves to one `raw/<state>/web/` destination. Defuddle is not run against the capture a second time.

## Initial State

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

## Temporary Extraction

Intake first stages Markdown files or extracts non-Markdown originals into temporary Markdown. Provider-returned attachments stay under the same temporary source folder and are promoted or deleted with it:

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

After each `source.md` is created, run the source-extraction intake file audit on that file. Normal files produce no output. If the audit reports `large_source`, create semantic `chunks/` before Source Review Gate when reliable source boundaries exist. Chunk paths use numeric components such as `01.md`; exact source titles and order tokens remain in headings and local indexes. When chunks are created, run the chunk audit on the temporary intake folder; resolve hard errors before promotion and carry warnings into review notes.

If `corrupted.pdf` cannot be extracted, stop handling that file immediately:

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

## Source Review Gate

Then run Source Review Gate on the temporary Markdown and optional digests:

| File | Review input | Outcome | Result |
| --- | --- | --- | --- |
| `paper.pdf` | `intake/tmp/paper/source.md`, chunks, digest | `digested` | Promote to `intake/processed/`, move original to `raw/digested/`, clean `intake/tmp/`, update wiki |
| `notes.md` | `intake/tmp/notes/source.md` | `digested` | Promote to `intake/processed/`, move original to `raw/digested/`, clean `intake/tmp/`, update wiki |
| `bundle/report.pdf` | `intake/tmp/bundle/report/source.md` | `digested` | Promote to `intake/processed/bundle/report/`, move original to `raw/digested/bundle/report.pdf`, create `wiki/sources/bundle/report.md` |
| `slides.pptx` | `intake/tmp/slides/source.md`, digest | `needs-review` | Move original to `raw/needs-review/`, record the question, clean `intake/tmp/` |
| `duplicate.html` | `intake/tmp/duplicate/source.md` | `ignored` | Move original to `raw/ignored/`, log the reason, clean `intake/tmp/` |
| `corrupted.pdf` | extraction failure | `unsupported` | Move original to `raw/unsupported/`, log the blocker |

## Final State

After accepted files are ingested:

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

The important invariant is that source review happens after extraction, because review should judge readable Markdown or digest output. Original files are moved only after extraction and review produce a final decision.

Files in `raw/needs-review/` remain pending until their review question is resolved. They do not update wiki pages, appear as accepted sources, or move to `intake/processed/` until a later review marks them `digested`.

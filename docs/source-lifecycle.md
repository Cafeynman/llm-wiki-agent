# Source Lifecycle Example

This example shows the intended lifecycle for a batch of files in `inbox/`. The core contract remains in `WIKI.md`, detailed mechanics live in `.agents/skills/source-extraction/references/intake-lifecycle.md`, and this file is only an example.

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

Intake first stages Markdown files or extracts non-Markdown originals into temporary Markdown. Provider-returned attachments stay under the same temporary source folder and follow its promotion, pending-review retention, or terminal cleanup:

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

After each `source.md` is created, run the source-extraction intake file audit on that file. Human output is quiet for normal files; JSON mode always returns schema 2. Empty, placeholder, navigation-stub, and no-reviewable-text inputs stop before Source Review Gate. If the audit reports `large_source`, create semantic `chunks/` before Source Review Gate when reliable source boundaries exist, while preserving canonical `source.md` prose and order; explicitly authorized image-markup changes follow `intake-lifecycle.md`. New chunk paths use stable order-and-title names such as `01-概述.md`; indexes own reading order and preserve exact source titles and order tokens. Existing numeric paths remain readable; inserting a chunk does not force renaming unrelated chunks. Every non-empty leaf below 2000 units warns, without an automated mergeability decision; every leaf above 10000 is a hard error. A reviewer may persist a decision directly in the nearest index row as `accepted-under — reason` or `accepted-over — reason` with status `reviewed`; the audit recomputes the units and category on every scan. When chunks are created, run the chunk audit on the temporary intake folder; resolve hard errors before promotion and carry unresolved warnings into review notes.

After a `digested` folder reaches its final `intake/processed/` path, run focused Obsidian lint on that folder or on each final changed Markdown file. Resolve broken links there before ingest. A unique truncated filename prefix may be repaired with the reviewed dry-run fixer; ambiguous or fuzzy candidates stay reported.

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
| `slides.pptx` | `intake/tmp/slides/source.md`, digest | `needs-review` | Move original to `raw/needs-review/`, record the question, retain useful `intake/tmp/` output |
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

The important invariant is that source review happens after extraction, because review should judge readable Markdown or digest output. Original files are moved only after extraction and review produce a final decision.

Files in `raw/needs-review/` remain pending until their review question is resolved. Useful extraction and side outputs may remain in the matching `intake/tmp/` folder and be reused after confirming they belong to the current original. A pending source need not have temporary output. They do not update wiki pages, appear as accepted sources, or move to `intake/processed/` until a later review marks them `digested`.

## Check one completed source

After source handling is complete, run the scoped read-only check with the final raw path:

```powershell
uv run --no-project .agents/skills/source-extraction/scripts/audit_source_closeout.py raw/digested/manual.pdf --vault . --json
```

Keep the focused intake lint before ingest and this closeout after ingest. They share the page-rule boundary: preserve source syntax and apply page rules to authored intake records. Closeout additionally verifies frontmatter intake traceability links that focused lint excludes from navigation diagnostics.

The check combines lifecycle structure, existing intake and chunk audits, and relevant links without repairing files or blocking on another source's unfinished work. A pass is structural evidence, not a judgment of extraction completeness or knowledge quality. See source-extraction's `references/intake-lifecycle.md` for closeout limits and source/chapter delegation ownership.

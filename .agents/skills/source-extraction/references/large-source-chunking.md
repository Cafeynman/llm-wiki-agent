# Large Source Chunking

Use this reference when a source is too large to review, ingest, or retrieve as one Markdown file. The stable lifecycle remains in `WIKI.md`; this file gives the detailed chunking procedure.

## Intake File Audit

Before chunking, run the bundled intake file audit helper against the current temporary `source.md`. The helper owns the size calculation and reports `large_source` only when a semantic chunking decision is needed.

Allow oversized chunks when splitting would break a table, formula group, legal clause, continuous argument, long quotation, or source region without a clear semantic boundary.

If a leaf chunk remains oversized, record the reason in the nearest `index.md` that lists that leaf chunk. After acceptance, also record it in `manifest.md` when it affects traceability or review.

## Chunk Audit

After creating `chunks/`, run the bundled chunk audit helper against the current intake folder:

```powershell
uv run --no-project .agents/skills/source-extraction/scripts/audit_chunks.py <intake-folder>
```

Run this on the temporary intake folder before Source Review Gate assigns `digested`. Hard errors must be resolved before promoting the chunked source to `intake/processed/`.

Use `--json` when another script needs structured output. The JSON output uses this stable shape:

```json
{
  "schema": 1,
  "path": "intake/tmp/source/source-name",
  "content_unit_threshold": 10000,
  "status": "pass | warn | fail",
  "errors": [],
  "warnings": []
}
```

Each error or warning has `code`, `path`, and `message`. Exit code `0` means no hard errors were found, even if warnings exist. Exit code `1` means hard errors were found. Exit code `2` means the input path could not be read.

Hard errors are limited to deterministic structure problems: missing `chunks/` or `chunks/index.md`, index entries that point outside `chunks/` or to missing files, leaf chunks not listed by their nearest `index.md`, nested chunk directories without local `index.md`, invalid or non-sequential numeric chunk paths, oversized leaf chunks without a recorded reason, or final `summary.md`/`manifest.md` existing while hard chunk errors remain.

Warnings are review cues, not automatic blockers. They include unresolved local image references, possible table-of-contents-like repeated headings, and possible missing numbered parents such as a `4.1` heading without an observed `4` parent. Source Review Gate still decides whether warnings make the source `digested` or `needs-review`.

## Directory Shape

For books, standards, manuals, long reports, and other sources with meaningful hierarchy, preserve the source structure under `chunks/`. During temporary extraction, keep chunks under `intake/tmp/source-relative-parent/original-source-base-filename/`, omitting `source-relative-parent/` only when the source is directly under the intake root. After Source Review Gate accepts the source, promote the same structure to `intake/processed/source-relative-parent/original-source-base-filename/` and write `summary.md` and `manifest.md` there.

```text
intake/processed/source-relative-parent/original-source-base-filename/
├── source.md
├── summary.md
├── manifest.md
└── chunks/
    ├── index.md
    ├── 01/
    │   ├── index.md
    │   ├── 01/
    │   │   ├── index.md
    │   │   ├── 01.md
    │   │   └── 02.md
    │   └── 02.md
    └── 02/
        └── index.md
```

Use one numeric sequence for the direct chunk files and chunk directories at each level. Use `01.md` for a leaf file and `01/` for a nested directory. Start at `01`, continue without gaps, and use the same sequence whether a child is a leaf file or a nested directory. Use at least two digits; after `99`, continue with `100`. A source-provided order token never replaces the numeric path component.

The paths and their display labels are separate:

```text
chunks/
├── index.md
├── 01/
│   ├── index.md
│   ├── 01.md
│   └── 02.md
└── 02.md
```

Numeric components are filesystem keys only. Preserve each exact source-language title and any source-provided order token in the chunk's first heading and in the nearest `index.md` entry. Do not translate, romanize, convert to pinyin, slugify, case-normalize, simplify, or remove characters from those display values. Characters that are invalid in filenames, such as `:`, `/`, `?`, or `*` on Windows, remain unchanged in headings and index labels because they are not part of the path.

When a chunk generation or restructuring script moves Markdown into the final `chunks/` tree, keep existing Markdown image references resolvable from the moved chunk. The chunk audit can warn about unresolved local image references, but the generator owns path preservation or path rewriting.

## Chunk Index Requirements

`chunks/index.md` is the navigation surface for the complete extracted source. It must include:

1. The source title and original path.
2. The chunking rule used for this source.
3. A table or list of chunk paths in source order.
4. For each chunk: title, source page or section range when known, approximate size, extraction caveats, and review or ingest status.
5. Links to nested `index.md` files when the source has chapter directories.

Each nested directory `index.md` should list only its local child chunks and child directories.

## Splitting Rules

Prefer semantic boundaries in this order:

1. Source-defined parts, major sections, standards chapters, manual modules, or equivalent top-level divisions.
2. Source-defined chapters and subchapters.
3. Source-defined headed sections and subsections.
4. Page ranges only when headings are absent or unreliable.
5. Tables, figures, appendices, and archive members as standalone chunks when they are independent units.

Do not split:

- A table across multiple files unless the source table itself is paginated and each part remains readable with headers.
- A continuous argument or legal clause where the later text depends on the earlier text.
- A formula group, example, or proof whose meaning depends on staying together.
- Isolated keyword hits, naked table rows, or reordered snippets.

## Source Entry Point

`source.md` remains the canonical intake entrypoint. For chunked sources, it should either contain the full extracted text when practical or clearly state that the complete review surface is split under `chunks/` and link to `chunks/index.md`.

Do not move agent-generated chunks into `raw/`. Temporary chunks stay under `intake/tmp/.../chunks/` until accepted, then the same structure is promoted to `intake/processed/.../chunks/`.

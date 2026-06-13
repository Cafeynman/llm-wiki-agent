# Large Source Chunking

Use this reference when a source is too large to review, ingest, or retrieve as one Markdown file. The stable lifecycle remains in `WIKI.md`; this file gives the detailed chunking procedure.

## Default Thresholds

Use these as working targets, not hard limits:

- Measure extracted Markdown with language-neutral content units. A content unit is `ceil(utf8_byte_length / 3)` for the text being evaluated.
- Target leaf chunk size: 4,000-8,000 content units.
- Recommend further semantic splitting above about 10,000 content units.
- Allow oversized chunks when splitting would break a table, formula group, legal clause, continuous argument, long quotation, or source region without a clear semantic boundary.

If a chunk remains oversized, record the reason in `chunks/index.md`; after acceptance, also record it in `manifest.md` when it affects traceability or review.

## Directory Shape

For books, standards, manuals, long reports, and other sources with meaningful hierarchy, preserve the source structure under `chunks/`. During temporary extraction, keep chunks under `intake/tmp/source-relative-parent/original-source-base-filename/`, omitting `source-relative-parent/` only when the source is directly under the intake root. After Source Review Gate accepts the source, promote the same structure to `intake/processed/source-relative-parent/original-source-base-filename/` and write `summary.md` and `manifest.md` there.

```text
intake/processed/source-relative-parent/original-source-base-filename/
├── source.md
├── summary.md
├── manifest.md
└── chunks/
    ├── index.md
    ├── 01-major-section/
    │   ├── index.md
    │   ├── 01-chapter/
    │   │   ├── index.md
    │   │   ├── 01-section.md
    │   │   └── 02-section.md
    │   └── 02-chapter.md
    └── 02-major-section/
        └── index.md
```

Use stable numeric prefixes to preserve source order. Preserve source-derived titles in headings and index entries; use filenames that are readable and stable without translating or romanizing the source title.

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

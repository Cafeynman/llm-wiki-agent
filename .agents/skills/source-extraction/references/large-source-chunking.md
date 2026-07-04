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

Hard errors are limited to deterministic structure problems: missing `chunks/` or `chunks/index.md`, index entries that point outside `chunks/` or to missing files, leaf chunks not listed by their nearest `index.md`, nested chunk directories without local `index.md`, inconsistent direct-child chunk naming, oversized leaf chunks without a recorded reason, or final `summary.md`/`manifest.md` existing while hard chunk errors remain.

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
    ├── 1-actual-top-level-heading/
    │   ├── index.md
    │   ├── 1.1-actual-child-heading/
    │   │   ├── index.md
    │   │   ├── 1.1.1-actual-leaf-heading.md
    │   │   └── 1.1.2-actual-leaf-heading.md
    │   └── 1.2-actual-child-heading.md
    └── 2-actual-top-level-heading/
        └── index.md
```

Use one naming strategy for each directory's direct child chunks. If every direct child title starts with a source-provided order token, keep the source title without adding an agent-generated prefix. If no direct child title starts with a source-provided order token, use generated numeric prefixes such as `01-` for every direct child in that directory. A sibling group that mixes source-ordered names and plain names is inconsistent; fix the split boundaries or names instead of adding generated prefixes in front of source-provided order tokens. Do not mix prefixed and unprefixed names in the same directory.

When direct child titles do not provide their own order, use this generated-prefix shape:

```text
chunks/
├── index.md
├── 01-actual-top-level-heading-without-source-order/
│   ├── index.md
│   ├── 01-actual-child-heading-without-source-order.md
│   └── 02-another-child-heading-without-source-order.md
└── 02-another-top-level-heading-without-source-order/
    └── index.md
```

The generated prefix is only an order key. Preserve source-derived titles in headings and index entries; use filenames that are readable and stable without translating, romanizing, converting to pinyin, slugifying, forcing lowercase, case-normalizing, or simplifying the source title. Source-provided order tokens are detected from generic leading ordinal or list markers, not from words such as chapter, section, part, module, clause, or their translations.

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

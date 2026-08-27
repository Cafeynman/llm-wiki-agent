# Large Source Chunking

Use this reference when a source is too large to review, ingest, or retrieve as one Markdown file. `intake-lifecycle.md` owns the detailed source movement and outcome; this file owns chunking mechanics.

## Intake File Audit

Before chunking, run the bundled intake file audit helper against the current temporary `source.md`. It rejects empty, known placeholder, known chunk-navigation-stub, and no-reviewable-text inputs; Markdown, Wikilink, reference-style, and HTML image markup do not count as body text, while actual table, code, mathematics, and prose do. Sparse text and `large_source` are warnings for Source Review Gate. The helper owns normalized content units: remove one leading UTF-8 BOM, convert CRLF and CR to LF, encode as UTF-8, divide the byte count by three, and round up. The algorithm identifier is `utf8-normalized-ceil-div3-v1`.

`source.md` is the canonical reviewable extraction accepted by Source Review Gate. Chunk generation, index generation, promotion, and rebuilding do not overwrite, truncate, or reorder it. Ordinary extraction and provider-part assembly keep the complete extracted text there. Only the explicit Excerpt-Type contract in `intake-lifecycle.md` permits a narrower review surface. `chunks/` is a derived navigation copy, not the source of truth.

Generate one source's proposed `chunks/` under a sibling staging directory. Validate the proposed tree, then replace only that source's derived chunk tree. Do not include `source.md` in the replacement. A failed or interrupted build leaves the accepted source and previous accepted chunk tree intact. One writer owns a source at a time; different sources may stage independently.

## Chunk Audit

After creating `chunks/`, run the bundled chunk audit helper against the current intake folder:

```powershell
uv run --no-project .agents/skills/source-extraction/scripts/audit_chunks.py <intake-folder>
```

Run this on the temporary intake folder before Source Review Gate assigns `digested`. The audit rechecks the current canonical `source.md` for hard reviewability failures as well as the derived chunk tree. Hard errors must be resolved before promoting the chunked source to `intake/processed/`.

The default soft minimum is 2000 content units and the hard maximum is 10000. The minimum is independent of the maximum. The audit reports every non-empty leaf below the minimum; it does not decide whether adjacent chunks can merge or whether merging would cross a semantic boundary. A reviewer either improves the split or accepts a visible reason. Every leaf above the maximum is a hard error until it is split or has a valid accepted reason. Empty leaves are always hard errors and cannot be excepted.

Use `--min-threshold` and `--threshold` to override the minimum and maximum for one run. Use `--json` when another script needs structured output. JSON schema 2 has this stable top-level shape:

```json
{
  "schema": 2,
  "path": "intake/tmp/source/source-name",
  "thresholds": {
    "min": 2000,
    "max": 10000,
    "units_algo": "utf8-normalized-ceil-div3-v1"
  },
  "status": "pass | warn | fail",
  "errors": [],
  "warnings": [],
  "accepted_exceptions": [],
  "summary": {}
}
```

Each error or warning has `code`, `path`, and `message`. Diagnostics sort by path and code; accepted exceptions sort by path and kind. Exit code `0` means no hard errors were found, even if warnings exist. Exit code `1` means deterministic hard errors were found. Exit code `2` means parameters, paths, or UTF-8 inputs could not be read. JSON mode always emits valid JSON for these states.

Primary hard errors include a missing or no-longer-reviewable canonical `source.md`, a missing chunk directory or root index, a zero-leaf tree, an empty or image-only leaf without reviewable text, a non-canonical index, missing or outside targets, unlisted leaves or nested indexes, invalid numeric paths or non-lowercase `.md` suffixes, missing descriptive headings, an invalid accepted-size row, an oversized leaf without a current acceptance, and final metadata written while hard failures remain. When the root structure is absent, the audit suppresses dependent per-leaf cascades.

Warnings include every undersized leaf without a current acceptance, exact index-size drift on ordinary rows, unresolved local images, possible table-of-contents-like repeated headings, and possible missing numbered parents such as `4.1` without an observed `4` parent. Source Review Gate judges warnings; the script never infers semantic mergeability.

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

The sequence includes only Markdown leaf files and directories that contain Markdown chunks or an `index.md`. Asset-only directories containing images or other non-Markdown side outputs are not chunk nodes and do not enter the numeric sequence. Keep them only when needed to preserve resolvable references; prefer the lifecycle's sibling `images/` location when the provider already supplied one.

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

`chunks/index.md` is the navigation surface for the complete extracted source. It includes the source title and original path, the chunking rule, and one canonical five-column table. Each nested directory `index.md` uses the same table and lists only its local child chunks and child directories.

| 块 | 标题与覆盖范围 | 内容说明 | 规模与尺寸裁决 | 内容评审 |
| --- | --- | --- | --- | --- |
| [01](01.md) | 第1章 范围 | — | 4200 · normal | reviewed |
| [02](02.md) | 第2章 术语 | — | 760 · accepted-under — 本章虽短但语义独立；并入第3章会破坏章节边界 | reviewed |
| [03](03.md) | 第3章 表3-1至表3-8 | 连续表格共用表头和脚注 | 12640 · accepted-over — 拆分后各块无法独立解释 | reviewed |

Use Markdown links in the `块` cell. The `标题与覆盖范围` cell preserves the source-language title and supplies source pages, sections, or another stable locator when known. `内容说明` may be `—` for one clearly named heading; it is required when a chunk spans multiple headings, uses a fallback split, or its title cannot explain the contents. A fallback split records a continuous page range, line range, or another stable locator. Numeric filenames are keys only. The leaf's first heading and the index title must be descriptive; a bare number, filename, or continuation label is insufficient.

The `规模与尺寸裁决` grammar is exact:

```text
<non-negative integer> · normal
<non-negative integer> · undersized
<non-negative integer> · oversized
<non-negative integer> · accepted-under — <single-line reason>
<non-negative integer> · accepted-over — <single-line reason>
— · group
```

The first exact ` — ` separates an accepted token from its reason. Audit recomputes the integer exactly and reports any mismatch. `— · group` is only for a row that links to the `index.md` of one direct child directory; self-links and skipped hierarchy levels are invalid. `内容评审` is `pending` or `reviewed`; whole-source `digested` and ingest status belong to the lifecycle and manifest.

### Accepted size decisions

The nearest index row is the only persistent record for a size decision. Use `accepted-under — <reason>` or `accepted-over — <reason>` in that row and set `内容评审` to `reviewed`. A health scan accepts the decision only when all four facts are current: the audit-recomputed integer equals the visible integer, the recomputed size category matches the accepted token, the visible reason is non-empty, and the row is `reviewed`. A valid row enters JSON `accepted_exceptions` with its path, kind, content units, and reason, and suppresses the corresponding threshold diagnostic.

There is no parallel registry, hash, review reference, or writer command. If an edit changes the measured units or moves the chunk into another category, update the row and review the decision again. If content or reason changes while the measured units, category, non-empty reason, and `reviewed` state remain valid, the visible decision remains accepted; this is the deliberate lightweight contract. Empty chunks can never be accepted.

Old list indexes and free-text `oversized: ...` reasons are migration candidates. They do not count as accepted and receive `legacy_chunk_index_format`; rewrite the five-column table and re-review each exception rather than preserving a permanent legacy branch.

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

`source.md` remains the canonical accepted extraction and is not a chunk-navigation stub. For ordinary extraction and provider-part assembly, it contains the complete extracted text. The narrow Excerpt-Type path remains governed by `intake-lifecycle.md`. Add navigation to `chunks/index.md` without replacing or shrinking the accepted text.

Do not move agent-generated chunks into `raw/`. Temporary chunks stay under `intake/tmp/.../chunks/` until accepted, then the same structure is promoted to `intake/processed/.../chunks/`.

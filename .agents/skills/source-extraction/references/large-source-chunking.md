# Large Source Chunking

Use this reference when a source is too large to review, ingest, or retrieve as one Markdown file. `intake-lifecycle.md` owns the detailed source movement and outcome; this file owns chunking mechanics.

## Intake File Audit

Before chunking, run the bundled intake file audit helper against the current temporary `source.md`. It rejects empty, known placeholder, known chunk-navigation-stub, and no-reviewable-text inputs; Markdown, Wikilink, reference-style, and HTML image markup do not count as body text, while actual table, code, mathematics, and prose do. Sparse text and `large_source` are warnings for Source Review Gate. The helper owns normalized content units: remove one leading UTF-8 BOM, convert CRLF and CR to LF, encode as UTF-8, divide the byte count by three, and round up. The algorithm identifier is `utf8-normalized-ceil-div3-v1`.

`source.md` is the canonical reviewable extraction accepted by Source Review Gate. Chunk generation, index generation, promotion, and rebuilding preserve its prose and order. Explicitly authorized image renaming or decorative-image removal may change only the affected image markup; preserve the lifecycle original. Ordinary extraction and provider-part assembly keep the complete extracted text there. Only the explicit Excerpt-Type contract in `intake-lifecycle.md` permits a narrower review surface. `chunks/` is a derived navigation copy, not the source of truth.

Build one source in a unique sibling staging directory, validate it, then publish with a recoverable replacement. One writer owns a source; different sources may stage independently. A failed build leaves previous results intact. An interrupted two-rename publication leaves an explicitly reported previous-directory recovery copy; restore it before retrying. Never clear neighboring sources or infer ownership from directory names.

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

Primary hard errors include a missing or no-longer-reviewable canonical `source.md`, a missing chunk directory or root index, a zero-leaf tree, an empty or image-only leaf without reviewable text, a non-canonical index, missing or outside targets, unlisted leaves or nested indexes, invalid chunk paths or non-lowercase `.md` suffixes, missing descriptive headings, an invalid accepted-size row, an oversized leaf without a current acceptance, and final metadata written while hard failures remain. When the root structure is absent, the audit suppresses dependent per-leaf cascades.

Warnings include every undersized leaf without a current acceptance, index-size drift on ordinary or accepted-under rows, stale under-size acceptance on now-normal chunks, unresolved local images, possible table-of-contents-like repeated headings, and possible missing numbered parents such as `4.1` without an observed `4` parent. Source Review Gate judges warnings; the script never infers semantic mergeability.

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

New leaf and group names use a numeric order hint plus a brief source-language semantic title, for example `10-基本原理.md` and `20-操作流程/`. Use canonical positive numbers with at least two digits (`01`, `99`, `100`), a hyphen, and a legal readable title. Replace only filesystem-invalid characters in the path; preserve exact source titles in headings and index labels. Paths are stable keys: inserting a block does not renumber existing blocks. Index row order is the reading order; gaps are valid.

Existing numeric names remain readable and auditable through the same parser. Package upgrades do not rename user sources. New builds use semantic names. Asset-only directories are not chunk nodes. A file and group cannot share the same component name.

For example, `chunks/10-基本原理/20-术语说明.md` contains a descriptive first heading and has a row in `chunks/10-基本原理/index.md`. Title characters invalid in filenames remain intact in headings and index labels. Do not translate or romanize source-language labels.

When a chunk generation or restructuring script moves Markdown into the final `chunks/` tree, keep existing Markdown image references resolvable from the moved chunk. The chunk audit can warn about unresolved local image references, but the generator owns path preservation or path rewriting.

## Chunk Index Requirements

`chunks/index.md` is the navigation surface for the complete extracted source. It includes the source title and original path, the chunking rule, and one canonical five-column table. Each nested directory `index.md` uses the same table and lists only its local child chunks and child directories.

```markdown
| 块 | 标题与覆盖范围 | 内容说明 | 规模与尺寸裁决 | 内容评审 |
| --- | --- | --- | --- | --- |
| [01](01.md) | 第1章 范围 | — | 4200 · normal | reviewed |
| [02](02.md) | 第2章 术语 | — | 760 · accepted-under — 本章虽短但语义独立；并入第3章会破坏章节边界 | reviewed |
| [03](03.md) | 第3章 表3-1至表3-8 | 连续表格共用表头和脚注 | 12640 · accepted-over — 拆分后各块无法独立解释 | reviewed |
```

Use Markdown links in the `块` cell. The `标题与覆盖范围` cell preserves the source-language title and supplies source pages, sections, or another stable locator when known. `内容说明` may be `—` for one clearly named heading; it is required when a chunk spans multiple headings, uses a fallback split, or its title cannot explain the contents. A fallback split records a continuous page range, line range, or another stable locator. Chunk paths are stable keys. The leaf's first heading and the index title must be descriptive; a bare number, filename, or continuation label is insufficient.

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

The nearest index row is the only persistent record for a size decision. Use `accepted-under — <reason>` or `accepted-over — <reason>` in that row and set `内容评审` to `reviewed`. A health scan requires a non-empty reason and `reviewed` status. For `accepted-over`, the audit-recomputed integer and size category must match the row exactly. For `accepted-under`, changed units remain a warning with the current measured count; a now-normal chunk reports a stale under-size decision, while a now-oversized chunk still requires a valid over-size acceptance. A valid row enters JSON `accepted_exceptions` with its path, kind, content units, and reason, and suppresses the corresponding threshold diagnostic.

The index row remains the sole persistent size decision; no exception registry or permanent hash is needed. During a rebuild, carry a decision forward only when the source range and generated body are unchanged. Changed content still outside the thresholds needs a new review and reason, even when its measured size is identical. Static audits validate the visible row; they do not infer whether an earlier review covered subsequent edits. Normal-sized changed content needs no size exception. Empty chunks can never be accepted.

Old list indexes and free-text `oversized: ...` reasons are migration candidates. They do not count as accepted and receive `legacy_chunk_index_format`; rewrite the five-column table and re-review each exception rather than preserving a permanent legacy branch.

## Splitting Rules

Keep a function, continuous process, or argument independently understandable. Review tiny and trailing blocks within the existing semantic review; the soft minimum never triggers automatic splitting. Prefer semantic boundaries in this order:

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

## Deterministic Build and Image Decisions

Use `scripts/build_chunks.py` after the agent has read the source and chosen complete semantic ranges. This tool performs no visual recognition or semantic boundary inference. Prefer merging related small sections when they form one intelligible unit.

```powershell
uv run --no-project .agents/skills/source-extraction/scripts/build_chunks.py intake/tmp/example --vault . --plan tmp/example-plan.json
```

The JSON plan is temporary, not a registry. `source_sha256` is the SHA256 of current `source.md` bytes and prevents applying stale ranges. `start` and `end` are inclusive one-based source lines. Every line must appear exactly once, in order. Paths are relative to `chunks/`; groups must occupy contiguous source ranges. Optional `description` supplies a single-line content explanation; otherwise the index records the complete source-line range. The builder uses the shared default size thresholds (2000 and 10000 content units). It generates the five-column indexes in plan order and checks the tree before publication. It replaces generated Markdown only, preserves chunk-local attachments and other non-Markdown files, and rejects unknown Markdown rather than deleting it. Unresolved local images block publication.

```json
{
  "source_sha256": "<current source.md SHA256>",
  "chunks": [
    {"path": "10-原理.md", "title": "原理", "start": 1, "end": 40},
    {"path": "20-流程.md", "title": "流程", "start": 41, "end": 90,
     "reviewed": true, "size_reason": "独立流程，合并会混淆操作范围"}
  ],
  "images": [
    {"file": "source.md", "occurrence": 1, "expected": "images/icon.png",
     "action": "delete", "authorized": true, "reason": "仅装饰，无状态或内容含义"},
    {"file": "source.md", "occurrence": 2, "expected": "images/figure.png",
     "action": "rename", "to": "images/操作流程.png"}
  ]
}
```

Use `size_reason` only for a reviewed under/oversized block. Unchanged generated body and range can inherit the existing nearest-index decision; changed ones cannot. New blocks default to pending review. This range check proves the transformation from extracted Markdown, not the completeness of PDF extraction.

Image `occurrence` counts simple non-code inline Markdown images in the named source-relative file, including angle-bracket paths. Each action verifies the exact expected target. External Markdown links, including optional titles, and location-independent HTML image `src` values remain verbatim. Local HTML `<img src=...>` references are checked against the source folder and rebased in each chunk; only the `src` value changes, preserving other attributes and table markup. Checking and rebasing use the same entity-decoded value with surrounding HTML ASCII whitespace removed; rewritten values escape HTML characters and whitespace so unquoted attributes remain valid. HTML images do not participate in Markdown image occurrence numbering or image actions, but their references protect shared attachments from deletion. Simple local inline links and Markdown images are also rebased. Reference-style link definitions, local titled inline links, `srcset`, `picture`, and other unrecognized image forms stop with an actionable diagnostic before moving text. Missing or ambiguous HTML `src` values and unresolved local files identify the affected file and line. HTML anchor links are not automatically relocated by this builder. Standard footnotes work when their references and definitions stay in the same chunk; adjust a range that separates them. This builder does not normalize source syntax or implement a general HTML rewriter.

Reuse project or batch image authorization. Remove only confirmed non-informative decorative icons. Preserve status, warning, operation, legend, and other informative icons; retain uncertain images and report the question. The tool applies explicit decisions only, preserves surrounding prose, and creates or appends the manifest with affected file/occurrence/target/reason details after validation. Renaming creates the named copy and updates specified occurrences. Original attachments remain by default. Set `delete_file: true` and `authorized: true` on a delete or rename decision to request physical removal of its old image asset. Only changed or removed old chunks and explicit physical attachment deletion require reading Markdown across the vault. First builds and byte-identical rebuilds without physical deletion stay source-local. Generated titles may be heading-anchor targets, so title changes retain the same reference protection as other chunk changes. The read-only scan uses the shared Markdown resolver, including optional link titles; the chunk text rewriter retains the narrower syntax described above. The tool resolves retained Markdown and Obsidian references across the vault, including basename aliases, and deletes only an unreferenced image in the staged source folder. Shared references, incomplete or unreadable scans, unsupported reference syntax, or a matching attachment reference in a `.canvas` or `.base` file retain the attachment with a reason in `attachment_actions`; raw originals are untouched.

Builds are limited to one folder under `intake/tmp/` or `intake/processed/`. They retain the lifecycle original. An ephemeral exclusive lock rejects a second writer; a crash leaves the lock for inspection before retrying. The source-folder snapshot is rechecked before publication. A successful publication removes only its exact previous-folder recovery copy; cleanup failures report that path for follow-up. An interruption retains recovery material. A disk-full or publication failure is an error, never success. Do not run multiple writers for the same source.

Before replacing changed or removed old chunks, locate their inbound references and map their source ranges. The builder conservatively rejects a resolved external reference to a changed old block and identifies the note; it does not rewrite external knowledge pages or guess semantic correspondence. Resolve those references in the authorized migration before retrying, preserving old results until the mapping is reviewable. Numeric-name legacy chunks follow this same rule. Cross-extraction semantic migration is outside this tool.

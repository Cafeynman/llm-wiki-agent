# Source Extraction Provider Contract

Source extraction providers produce reviewable Markdown from original source material. They are not ingestion engines and do not own wiki judgment.

## Terms

- `source kind`: What the original material is, such as `document`, `webpage`, `image`, `audio`, or `video`.
- `provider`: The concrete tool or method used to extract reviewable text, such as `markitdown`, `mineru`, or `defuddle`.
- `policy`: A project preference that controls whether a source kind is supported, unsupported, or requires explicit user approval before extraction.

## Provider Input

A provider receives:

- Original source path or source URL.
- Source kind.
- Temporary output directory under `intake/tmp/source-relative-parent/original-source-base-filename/`, omitting `source-relative-parent` when the source is directly under the intake root.
- Project preferences from `PROJECT.md`.
- Provider-specific options approved for the current task.

## Provider Output

A successful provider run must produce:

- `source.md` with reviewable Markdown.
- Provider metadata for the intake manifest or review notes:
  - provider name
  - provider mode when relevant
  - source kind
  - OCR/transcription flags when relevant
  - warnings
  - missing content
  - links to generated side outputs when they are necessary for traceability

Providers must preserve source-derived text as content. Do not remove or normalize punctuation, YAML indicator characters, Markdown control characters, or filename characters from extracted titles, headings, paths, or body text. When provider metadata or source-derived strings are later written into YAML frontmatter, Markdown tables, wikilinks, or command examples, the writer must quote, escape, or encode them for that target syntax without changing the underlying value.

## Provider Limits

A provider must not:

- Modify original files under `inbox/` or `raw/`.
- Write directly to `wiki/`.
- Promote files to `intake/processed/`.
- Decide Source Review Gate outcomes.
- Convert one provider's Markdown output through another provider.
- Add unrequested compatibility, fallback, or secondary extraction passes.
- Store or display secrets.

## Reprocessing

When switching providers, restart from the original source file or URL. The previous provider output may be cited as comparison material, but it is not source truth and must not become the new provider input.

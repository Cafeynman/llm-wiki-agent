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

The `original-source-base-filename` segment is the original source file's base filename after removing only the extension. Preserve language, case, whitespace, punctuation, and special characters; do not translate, romanize, URL encode, slugify, lowercase, or simplify it.

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

When a large original file is split for provider limits, the provider workflow must merge part outputs back into one `source.md` for the original source before Source Review Gate. Part files may be kept only as traceability side outputs with recorded page ranges, provider modes, and merge order.

## Provider Credentials and Local Service Configuration

Service-backed providers may require local credentials, tokens, API keys, or deployment-specific endpoints. The provider setup document must name the required environment variables and the provider mode that needs them. It must not contain real secret values or private endpoint values.

Secret values and private service URLs belong only in the project-root `.env` file, which is local runtime configuration and not wiki content. Provider commands that run through `uv` and depend on those variables must be run from the project root with `uv run --env-file .env ...`, or with `UV_ENV_FILE=.env` set in the current shell for repeated `uv run` commands.

Agents may verify that a required variable is present, but must report only present or missing status. If `.env` or a required variable is missing, stop before extraction and ask the user to configure it. Do not invent fallback credentials, paste secrets or private service URLs into commands, or write those values into manifests, logs, review notes, wiki pages, source cards, `PROJECT.md`, `WIKI.md`, `AGENTS.md`, or `CLAUDE.md`.

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

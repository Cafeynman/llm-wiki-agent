# Source Extraction Provider Contract

Source extraction providers produce reviewable Markdown from original source material. They are not ingestion engines and do not own wiki judgment.

## Terms

- `source kind`: What the original material is, such as `document`, `webpage`, `image`, `audio`, or `video`.
- `provider`: The concrete tool or method used to extract reviewable text, such as `markitdown`, `mineru`, or `defuddle`.
- `policy`: A project preference that controls whether a source kind is supported, unsupported, or requires explicit user approval before extraction.

## Provider Input

A provider receives:

- Original source path, or the submitted source URL when creating the first live-URL capture.
- Source kind.
- Caller-selected output role: a deterministic Markdown source capture under `inbox/web/` for an initial live URL, or a temporary output directory under `intake/tmp/source-relative-parent/original-source-base-filename/` for ordinary extraction.
- Project preferences from `PROJECT.md`.
- Provider-specific options approved for the current task.

The `original-source-base-filename` segment is the original source file's base filename after removing only the extension. Preserve language, case, whitespace, punctuation, and special characters; do not translate, romanize, convert to pinyin, URL encode, slugify, force lowercase, case-normalize, or simplify it. Generated live-URL captures use the one deterministic title-and-hash filename defined in `WIKI.md`; do not apply that naming rule to submitted files.

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

For the initial live-URL flow, Defuddle instead returns structured Markdown and page metadata to the caller, which serializes the lifecycle source capture under `inbox/web/`. Intake then stages that capture unchanged as `source.md`; it does not run Defuddle a second time.

Provider-returned images and attachments may be stored under the same intake folder as `source.md`, normally under `images/`. They are passive source side outputs, not first-class wiki knowledge. Promote them with an accepted intake folder or delete them with temporary output for every other outcome. Record accepted paths in `manifest.md`; record relevant disposition in source review or intake logs before deleting non-accepted output.

Providers must preserve source-derived text and labels as content. Do not remove or normalize punctuation, YAML indicator characters, Markdown control characters, or filename characters from extracted titles, headings, paths, or body text. When provider metadata or source-derived strings are later written into YAML frontmatter, Markdown tables, wikilinks, or command examples, the writer must quote, escape, or encode them for that target syntax without changing the underlying value.

When a large original file is split for provider limits, the provider workflow must merge part outputs back into one `source.md` for the original source before Source Review Gate. Part files may be kept only as traceability side outputs with recorded page ranges, provider modes, and merge order.

## Provider Credentials and Local Service Configuration

Service-backed providers may require local credentials, tokens, API keys, or deployment-specific endpoints. The provider setup document must name the required environment variables and the provider mode that needs them. It must not contain real secret values or private endpoint values.

Secret values and private service URLs belong only in the project-root `.env` file, which is local runtime configuration and not wiki content. Provider commands that run through `uv` and depend on those variables must be run from the project root with `uv run --env-file .env ...`, or with `UV_ENV_FILE=.env` set in the current shell for repeated `uv run` commands.

Agents may verify that a required variable is present, but must report only present or missing status. If `.env` or a required variable is missing, stop before extraction and ask the user to configure it. Do not invent fallback credentials, paste secrets or private service URLs into commands, or write those values into manifests, logs, review notes, wiki pages, source cards, `PROJECT.md`, `WIKI.md`, or agent entrypoint files.

## Provider Limits

A provider must not:

- Modify lifecycle source artifacts after they have entered `inbox/` or `raw/`. Creating the initial Defuddle URL capture is the scoped non-file-source exception.
- Write directly to `wiki/`.
- Promote files to `intake/processed/`.
- Decide Source Review Gate outcomes.
- Convert one provider's Markdown output through another provider.
- Add unrequested compatibility, fallback, or secondary extraction passes.
- Store or display secrets.

## Reprocessing

When switching providers, restart from the lifecycle source artifact. For a submitted file, that is the preserved original file. For a live URL that has entered the lifecycle, that is the stored Defuddle source capture; fetching the current live page again is a new capture action, not ordinary reprocessing. Other provider output may be cited as comparison material, but it is not source truth and must not become the new provider input.

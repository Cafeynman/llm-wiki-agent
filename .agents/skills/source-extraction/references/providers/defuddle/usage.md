# Defuddle Usage

Use Defuddle as the default webpage provider when `PROJECT.md` selects `defuddle`.

## Supported Source Kinds

- `webpage`

## Wiki Capture Pattern

Run Defuddle once against the exact submitted URL and request structured Markdown output:

```bash
defuddle parse <url> --json --md
```

Parse the JSON structurally. Serialize a Markdown source capture at:

```text
inbox/web/<source-language-page-title>--<url-hash>.md
```

Follow the exact title encoding and SHA-256 hash rule in `WIKI.md`. Use a YAML serializer for available metadata such as the exact submitted URL, capture timestamp, provider, title, author, domain, and publication date. Write Defuddle's clean Markdown as the body. If the title is missing, use the returned domain as the filename title segment.

The capture is the lifecycle source artifact for the live URL. Stage it unchanged at `intake/tmp/web/<capture-base-name>/source.md`, run Source Review Gate once, and move the capture to one `raw/<state>/web/` destination. A digested source card cites both the raw capture wikilink and the quoted external URL.

If Defuddle cannot produce usable Markdown or metadata, record the exact submitted URL and blocker in source review or the intake log and stop; do not create an empty source capture. If the deterministic path already belongs to the same URL, reprocess the existing lifecycle source. If it identifies a distinct URL, record a naming-collision question and wait for user judgment.

## Output Review

- Record paywalls, login requirements, scripts, dynamic state, missing content, and extraction warnings.
- Defuddle output is not final wiki knowledge and must not bypass Source Review Gate.
- Do not send a live URL directly to `intake/tmp/` and do not run another provider against the generated capture.

---
name: defuddle
description: Run the Defuddle CLI as the webpage source-capture provider after source-extraction selects `defuddle`, or for non-wiki webpage cleanup when no intake lifecycle applies. For wiki source material, use source-extraction first so PROJECT.md provider policy, Source Review Gate, and the WIKI.md output contract remain in control.
---

# Defuddle

Use Defuddle to extract clean Markdown and metadata from a webpage. For wiki intake, Defuddle materializes a submitted live URL as a lifecycle source capture; it does not write final wiki content or decide review outcomes.

If the CLI is missing, follow `.agents/skills/source-extraction/references/providers/defuddle/setup.md`.

## Wiki URL Capture

Run once against the submitted URL:

```bash
defuddle parse <url> --json --md
```

Parse the JSON structurally. Use the returned Markdown and metadata to serialize the deterministic source capture under `inbox/web/` according to `WIKI.md`. Stage that capture unchanged under `intake/tmp/`; do not run Defuddle against the capture again.

For quick non-wiki cleanup, Markdown may be written directly to a caller-selected output:

```bash
defuddle parse <url> --md -o <output.md>
```

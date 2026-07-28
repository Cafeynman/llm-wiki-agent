---
name: defuddle
description: Run the Defuddle CLI as the webpage source-capture provider after source-extraction selects `defuddle`, or for non-wiki webpage cleanup when no intake lifecycle applies. For wiki source material, use source-extraction first so PROJECT.md provider policy, Source Review Gate, and the WIKI.md output contract remain in control.
---

# Defuddle

Use Defuddle to extract clean Markdown and metadata from a webpage. For wiki intake, Defuddle materializes a submitted live URL as a lifecycle source capture; it does not write final wiki content or decide review outcomes.

## Runtime Preflight

Before either workflow, run:

```bash
defuddle --version
```

If the CLI is missing, follow `.agents/skills/source-extraction/references/providers/defuddle/setup.md`. Tell the user before changing global npm packages, request approval, then perform the approved installation and verification yourself; do not ask the user to run the commands manually.

## Wiki URL Capture

Run once against the submitted URL:

```bash
defuddle parse <url> --json
```

Parse the JSON structurally. Require `contentMarkdown` to be a non-empty string and use that field as the capture body; `content` contains HTML. Do not add `--md` to structured mode: in Defuddle `0.19.2`, that combination changes `content` to Markdown and omits `contentMarkdown`. Use the returned metadata to serialize the deterministic source capture under `inbox/web/` according to `WIKI.md`. Stage that capture unchanged under `intake/tmp/`; do not run Defuddle against the capture again.

## General Webpage Cleanup

When no wiki intake lifecycle applies, write Markdown directly to a caller-selected output:

```bash
defuddle parse <url> --md -o <output.md>
```

Confirm the output is non-empty and contains the requested page content. This route does not use `PROJECT.md` provider selection, create an `inbox/web/` capture, or enter Source Review Gate.

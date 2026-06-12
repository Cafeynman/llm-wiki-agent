---
name: defuddle
description: Run the Defuddle CLI as the webpage extraction provider after source-extraction selects `defuddle`, or for non-wiki webpage cleanup when no intake lifecycle applies. For wiki source material, use source-extraction first so PROJECT.md provider policy, Source Review Gate, and the WIKI.md output contract remain in control.
---

# Defuddle

Use Defuddle CLI to extract clean readable Markdown from web pages. In this package, Defuddle is a provider tool; it does not decide whether a source enters `intake/tmp/`, `intake/processed/`, or `wiki/`.

For wiki intake, start with `source-extraction`. Use this skill only after that workflow selects `defuddle` for a webpage source.

If not installed: `npm install -g defuddle`

## Usage

Always use `--md` for markdown output:

```bash
defuddle parse <url> --md
```

For wiki intake, write to the output path chosen by `source-extraction`:

```bash
defuddle parse <url> --md -o intake/tmp/source-relative-parent/original-source-base-filename/source.md
```

Extract specific metadata:

```bash
defuddle parse <url> -p title
defuddle parse <url> -p description
defuddle parse <url> -p domain
```

## Output formats

| Flag        | Format                           |
| ----------- | -------------------------------- |
| `--md`      | Markdown (default choice)        |
| `--json`    | JSON with both HTML and markdown |
| (none)      | HTML                             |
| `-p <name>` | Specific metadata property       |

# Defuddle Usage

Use Defuddle as the default webpage provider when `PROJECT.md` selects `defuddle`.

## Supported Source Kinds

- `webpage`

## Command Pattern

Extract clean Markdown:

```bash
defuddle parse <url> --md -o <intake-tmp-dir>/source.md
```

For quick inspection without saving:

```bash
defuddle parse <url> --md
```

## Output Handling

- Preserve the original URL in manifest or review notes.
- Record extraction warnings, missing content, paywalls, scripts, or dynamic content that Defuddle could not access.
- If the page requires browser interaction, login, or JavaScript-rendered state that Defuddle cannot extract reliably, move the source through `needs-review` unless another approved provider is selected.

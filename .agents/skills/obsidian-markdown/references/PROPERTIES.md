# Properties (Frontmatter) Reference

Properties use YAML frontmatter at the start of a note:

```yaml
---
title: "My Note Title"
date: 2024-01-15
tags:
  - project
  - important
aliases:
  - "My Note"
  - "Alternative Name"
cssclasses:
  - custom-class
status: draft
rating: 4.5
completed: false
due: 2024-02-01T14:30:00
---
```

Quote free-text values that come from users, sources, filenames, titles, aliases, paths, URLs, or descriptions, or emit frontmatter with a YAML serializer. Fixed safe tokens such as dates, booleans, numbers, and controlled status values may stay unquoted.

For source traceability, vault-internal `sources:` entries must be quoted wikilink strings. External URLs remain quoted plain strings:

```yaml
sources:
  - "[[raw/digested/source-relative-parent/original-filename.ext]]"
  - "[[intake/processed/source-relative-parent/original-source-base-filename/source.md]]"
  - "https://example.com/source"
```

Omit `source-relative-parent/` only when the source is directly under the intake root.

## Property Types

| Type | Example |
|------|---------|
| Text | `title: "My Title"` |
| Number | `rating: 4.5` |
| Checkbox | `completed: true` |
| Date | `date: 2024-01-15` |
| Date & Time | `due: 2024-01-15T14:30:00` |
| List | `tags: [one, two]` or YAML list |
| Links | `related: "[[Other Note]]"` |

## Default Properties

- `tags` - Note tags (searchable, shown in graph view)
- `aliases` - Alternative names for the note (used in link suggestions)
- `cssclasses` - CSS classes applied to the note in reading/editing view

## Tags

```markdown
#tag
#nested/tag
#tag-with-dashes
#tag_with_underscores
```

Tags can contain: letters (any language), numbers (not first character), underscores `_`, hyphens `-`, forward slashes `/` (for nesting). Tags must not contain spaces or other whitespace. Use `energy-policy` or `energy/policy`, not `energy policy`.

In frontmatter:

```yaml
---
tags:
  - tag1
  - nested/tag2
---
```

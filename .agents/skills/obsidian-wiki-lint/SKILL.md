---
name: obsidian-wiki-lint
description: Foundational Obsidian wiki static linting tool for broken wikilinks, missing standard footnote definitions, orphan pages, and shared Markdown parsing. Use the full wiki scope for health reviews and focused scopes for ordinary writes. Project validators may reuse its parser without running an unrelated whole-wiki audit.
---

# Obsidian Wiki Lint

Maintain an Obsidian wiki with deterministic checks before judgment-heavy cleanup. Prefer this skill for `Maintain Wiki` work in an LLM Wiki package.

## Runtime

Run scripts from the vault or package root with `uv run --no-project`. The scripts use only Python standard library modules and require no Node.js or npm dependencies. `--no-project` avoids installing unrelated project dependencies just to run lint utilities.

```powershell
uv run --no-project .agents/skills/obsidian-wiki-lint/scripts/lint_wiki.py --vault . --scope wiki
```

## Verification Architecture

For wiki health reviews, run `lint_wiki.py` first and add a focused project layer only for business rules the standard lint does not own. For a narrow project validator, reuse `obsidian_links.py`, the existing code masking, and wikilink resolution functions when they are relevant; run the full lint when its diagnostics affect the requested result or the active `WIKI.md` requires it. Keep foundational Markdown parsing here rather than duplicating it in each validator.

Keep executable Obsidian Markdown checks owned here. `WIKI.md` may require this lint layer as a gate, but should not duplicate the detailed list of individual checks. General syntax guidance belongs in `obsidian-markdown`; deterministic checks and their test coverage belong in this skill.

## Core Workflow

1. Run `lint_wiki.py` on the requested file or smallest affected scope. Use `--scope wiki` for a whole-wiki health baseline.
2. For broken links caused by uniquely truncated source filenames, run `fix_truncated_links.py` without `--write` and inspect the proposed changes.
3. For missing concept cross-links, run `crosslink_concepts.py` without `--write` and inspect the proposed changes.
4. Add `--write` only when the original request asks for fixes or the user has
   approved the specific finding, and the fix is mechanical with the correct
   target scope. Diagnostics alone never authorize a write.
5. After writes, rerun `lint_wiki.py` on the affected scope.

`lint_wiki.py` ignores link and footnote examples inside fenced or inline code. `obsidian_links.py` scans a wikilink through its paired `]]`; a single `]` inside a source-derived filename remains part of the target. This matches the verified Obsidian metadata-cache behavior for raw links, aliases, and headings. Do not insert a backslash before that `]`: Obsidian treats the backslash as part of an unresolved target. The scanner preserves target spans, heading or block fragments, and aliases for lint, repair, and downstream validators.

The linter resolves ordinary Markdown links relative to the containing note, while a leading `/` starts from the vault root and Obsidian wikilinks retain vault semantics. Links that resolve outside the vault are reported as broken. Links ending in `/` or `\` are explicit directory links. Existing directory links are checked for directory existence and do not count as page incoming links. Internal vault paths in frontmatter `sources:` must be complete quoted wikilinks. `intake/` wikilinks in frontmatter `sources:` are source traceability and are excluded from navigation broken-link reporting; body links to `intake/` remain checked. Every standard footnote reference must have a matching definition in the same note; repeated references may share one definition.

Orphan diagnostics run only for `--scope wiki`, where the complete canonical navigation scope is available. Narrower scopes check outbound links and apply page-level frontmatter, table, traceability-path, and footnote rules to maintained pages without producing local orphan reports. The shared `uses_page_contract` classification used by lint and source closeout recognizes an accepted intake source folder by its nearest `source.md` within the processed-intake boundary: preserved source text, chunk leaves, and provider text receive link checks; authored `summary.md`, `manifest.md`, `digest.md`, and chunk indexes also receive page-level checks. Unrecognized intake folders retain ordinary page checks. The CLI skips temporary directories; the pre-ingest focused check runs on the promoted intake folder.

If the requested `--scope` contains no Markdown pages, `lint_wiki.py` exits with code `2`. Treat that as a wrong vault root or scope, not a clean wiki.

## Scripts

| Script | Purpose | Writes by default |
| --- | --- | --- |
| `obsidian_links.py` | Provides the single span-preserving Obsidian wikilink scanner and target/fragment/alias parser reused by lint, repair, and project validators. | No |
| `lint_wiki.py` | Reports broken wikilinks, standard footnote references without same-note definitions, orphan pages under a scope, frontmatter `sources:` entries that should be wikilinks, frontmatter `tags:` values that contain whitespace, unescaped wikilink alias separators in Markdown tables, bare internal traceability paths in body text, exact known source-card template placeholders, and page counts. | No |
| `fix_truncated_links.py` | Expands wikilinks whose target filename is a unique prefix of an existing Markdown file. | No |
| `crosslink_concepts.py` | Adds limited links from concept names or aliases to concept notes recursively under the configured concepts directory. | No |

## Common Commands

Check wiki pages:

```powershell
uv run --no-project .agents/skills/obsidian-wiki-lint/scripts/lint_wiki.py --vault . --scope wiki
```

Preview truncated link fixes:

```powershell
uv run --no-project .agents/skills/obsidian-wiki-lint/scripts/fix_truncated_links.py --vault . --source-file wiki/sources/example.md --target-dir intake/processed/example
```

Apply reviewed truncated link fixes:

```powershell
uv run --no-project .agents/skills/obsidian-wiki-lint/scripts/fix_truncated_links.py --vault . --source-file wiki/sources/example.md --target-dir intake/processed/example --write
```

Preview conservative concept cross-links:

```powershell
uv run --no-project .agents/skills/obsidian-wiki-lint/scripts/crosslink_concepts.py --vault . --concepts-dir wiki/concepts --alias-file tmp/concept-aliases.json
```

## Guardrails

- Do not use link repair to guess between multiple candidates. Leave ambiguous links unchanged and report them.
- `fix_truncated_links.py` only expands a unique filename prefix inside the explicitly supplied target directory. It preserves an existing `.md` suffix, fragment, alias, and table-escaped alias separator, writes atomically, and is idempotent. Do not add whitespace deletion, fullwidth conversion, Unicode or case folding, punctuation normalization, or cross-directory suffix guessing as automatic repairs.
- Do not cross-link every occurrence. Keep `--max-per-concept` low; the default is 2 per source page.
- Do not add cross-links inside frontmatter, code blocks, inline code, Markdown links, existing wikilinks, or URLs. Table rows are supported and alias separators will be automatically escaped.
- Keep project-specific aliases in a JSON alias file instead of hard-coding them into the script.
- When `lint_wiki.py` finds orphans, distinguish true orphan pages from intentional entry pages such as `wiki/home.md`, `wiki/index.md`, and `wiki/overview.md`.

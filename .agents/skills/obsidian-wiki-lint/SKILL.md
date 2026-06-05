---
name: obsidian-wiki-lint
description: Foundational Obsidian wiki static linting tool. Use as the FIRST standard layer for checking broken wikilinks and orphan pages. For project-specific business logic validations (e.g. counting files, checking specific metadata), ALWAYS run this skill first to establish a baseline, then write custom scripts for the rest. Do not write custom scripts to replace this skill's basic link parsing.
---

# Obsidian Wiki Lint

Maintain an Obsidian wiki with deterministic checks before judgment-heavy cleanup. Prefer this skill for `Maintain Wiki` work in an LLM Wiki package.

## Runtime

Run scripts from the vault or package root with `uv run --no-project`. The scripts use only Python standard library modules and require no Node.js or npm dependencies. `--no-project` avoids installing unrelated project dependencies just to run lint utilities.

```powershell
uv run --no-project .agents/skills/obsidian-wiki-lint/scripts/lint_wiki.py --vault . --scope wiki
```

## Verification Architecture

When users request complex health checks or business logic validation, follow a two-layer approach:
1. **Standard Layer (Foundation)**: Always run `lint_wiki.py` first to establish a reliable baseline of structural integrity (broken links and orphans).
2. **Project Layer (Custom)**: Write custom one-off scripts to verify project-specific states (e.g., source card counts, synthesis completion, metadata values). Do not mix foundational wiki link parsing with custom business logic.

## Core Workflow

1. Run `lint_wiki.py` first. Treat its output as diagnostics, not as permission to rewrite pages.
2. For broken links caused by uniquely truncated source filenames, run `fix_truncated_links.py` without `--write` and inspect the proposed changes.
3. For missing concept cross-links, run `crosslink_concepts.py` without `--write` and inspect the proposed changes.
4. Add `--write` only when the fix is mechanical and the target scope is correct.
5. After writes, rerun `lint_wiki.py`.

## Scripts

| Script | Purpose | Writes by default |
| --- | --- | --- |
| `lint_wiki.py` | Reports broken wikilinks, orphan pages under a scope, and page counts. | No |
| `fix_truncated_links.py` | Expands wikilinks whose target filename is a unique prefix of an existing Markdown file. | No |
| `crosslink_concepts.py` | Adds limited links from concept names or aliases to concept notes. | No |

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
- Do not cross-link every occurrence. Keep `--max-per-concept` low; the default is 2 per source page.
- Do not add cross-links inside frontmatter, code blocks, inline code, Markdown links, existing wikilinks, or URLs. Table rows are supported and alias separators will be automatically escaped.
- Keep project-specific aliases in a JSON alias file instead of hard-coding them into the script.
- When `lint_wiki.py` finds orphans, distinguish true orphan pages from intentional entry pages such as `wiki/home.md`, `wiki/index.md`, and `wiki/overview.md`.

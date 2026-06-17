---
name: wiki-contract-review
description: Use when reviewing this LLM Wiki development package or an initialized vault for script migration correctness, init/upgrade path drift, full local skill consistency, hidden or untracked local residue, redundant wiki structure, conflicting agent instructions, stale workflow residue, multilingual doc drift, or knowledge-base cleanup risks.
---

# Wiki Contract Review

Use this skill for Maintain Wiki or package-maintenance reviews where the risk is contract drift across scripts, entrypoint docs, local skills, human docs, and runtime wiki folders.

When the target is this development package root, this is a full package contract review skill. Do not sample local skills. Enumerate and inspect every local skill under `.agents/skills/`, including untracked local review skills, then classify whether each one belongs in the package, is local-only, or needs cleanup.

The goal is to find whether the current implementation matches the wiki contract and whether the knowledge base contains redundant, obsolete, or conflicting structure. Do not treat one file as authoritative until you have identified the current source of truth.

## Required Reading

From the working root under review, read these files when they exist:

1. `AGENTS.md` and adapter entrypoints such as `CLAUDE.md` for repository workflow, runtime, skill-source, precedence, and ownership rules.
2. `WIKI.md` for the stable wiki directory contract and Add Knowledge, Use Knowledge, and Maintain Wiki workflows.
3. `PROJECT.md` only for project-specific preferences; do not use it as a stable package contract.
4. `scripts/upgrade-manifest.txt`, `scripts/init.ps1`, `scripts/init.sh`, `scripts/upgrade.ps1`, and `scripts/upgrade.sh` when reviewing migration, initialization, or upgrade behavior.
5. For package-root reviews, every local skill under `.agents/skills/`, not global skill copies. For initialized-vault reviews, inspect the target vault's `.agents/skills/` first, then compare with the package root only when migration or package-source drift is in scope.
6. `README.md`, `README.zh-CN.md`, and `docs/` only when user-facing setup or usage wording may conflict with the entrypoint and wiki contracts.
7. `.gitignore`, `git ls-files`, and `git status --ignored --short` when reviewing package boundaries, local residue, or migration risk.
8. `pyproject.toml`, `.env.example`, and provider setup references when reviewing runtime, dependency, or environment-variable contracts.

If the user gives a separate vault root, inspect that initialized vault as the working root for runtime structure, and inspect the package root only for package source files and scripts.

## Review Plan

Start every review by stating the target root, whether it is a package root or initialized vault, and the specific surfaces in scope. Use at least three independent repository scans before concluding:

1. **Contract scan:** inventory tracked files, hidden files, manifest entries, scripts, entrypoint docs, and package-managed skills.
2. **Residue scan:** search for stale paths, conflicting wording, duplicated rules, obsolete workflow terms, local runtime artifacts, and generated files that should not be treated as package source.
3. **Full local skill scan:** enumerate all `.agents/skills/*/SKILL.md` files, validate each skill, inspect auxiliary files, and compare trigger/ownership boundaries across skills.

Do not stop after a single broad grep. Hidden directories are part of the review surface because `.agents/`, `.claude/`, `.obsidian/`, and tool workspaces can change how agents interpret the repository.

### 1. Script and Migration Fit

Check whether scripts and package-managed files match the current wiki structure.

1. Derive the expected runtime directories from `WIKI.md` and the initialization rules in `AGENTS.md`.
2. Confirm `init` and `upgrade` scripts create the same required runtime directories and seed files.
3. Confirm `upgrade-manifest.txt` includes stable package files and directories that must migrate, including `.agents/skills`, `docs`, `scripts`, `AGENTS.md`, `CLAUDE.md`, and `WIKI.md` when present.
4. Confirm package-managed files are copied from the package root and workspace-specific context stays in `PROJECT.md`.
5. Compare `git ls-files`, `git status --ignored --short`, and the manifest so untracked archives, ignored vault folders, adapter directories, caches, and runtime folders are not mistaken for package source. Treat untracked files inside manifest-managed directories as pending local changes, not package source, until they are deliberately tracked.
6. Search scripts and skills for stale path contracts such as dated intake directories, old skill paths, missing `.agents/skills` prefixes, unsupported runtime folders, or hardcoded scenario-specific paths.
7. Verify script examples in skills and docs are executable from the documented root and use `uv run` where the project contract requires it.
8. If both English and translated docs exist, check that setup commands, script parameter names, root semantics, and package/runtime boundaries are aligned across languages.
9. Check provider/helper skills against the owning workflow contract. Extraction helpers must not bypass `source-extraction`, `PROJECT.md` provider policy, Source Review Gate, or the text-first wiki lifecycle.
10. Check `pyproject.toml`, lockfiles when present, `.env.example`, provider setup docs, and runtime commands for dependency or environment drift.

### 2. Full Local Skill Review

When reviewing this development package root, review every local skill under `.agents/skills/`. This is not optional and is not limited to the skills that broad searches happen to match.

For each skill:

1. Record directory name, `name` frontmatter, trigger description, tracked/untracked status, and whether it is package-managed or local-only.
2. Read `SKILL.md` and list directly owned scripts, references, assets, agents metadata, tests, README-like files, setup notes, package manifests, hooks, and other auxiliary files.
3. Run structural validation:

   ```powershell
   uv run --no-project .agents/skills/skill-creator/scripts/quick_validate.py .agents/skills/<skill-name>
   ```

4. Check whether the trigger description overlaps another local skill or bypasses the owner of a workflow. Provider/helper skills must point back to their router; router skills must not hide provider-specific secrets or scenario-specific behavior.
5. Check runtime portability. Flag active instructions that assume a non-current runtime, stale user-level paths, direct `python`/`pip` where this package requires `uv run`, `.claude` paths that conflict with `.agents/skills`, or hidden local service assumptions.
6. Check package suitability. Flag skill-specific README, `POST_INSTALL.md`, `_meta.json`, `package.json`, hooks, copied upstream docs, or examples when they are stale, redundant, or not needed for the package contract.
7. Check source-control status. A skill inside a manifest-managed directory but untracked is pending local state, not confirmed package source, until the user decides to add it.

Build a skill boundary matrix before reporting:

| Skill | Role | Trigger owner | Depends on | Must not bypass | Status |
| --- | --- | --- | --- | --- | --- |

Use this matrix to find duplicated triggers, missing routers, stale provider claims, and local-only tools that should not be committed.

Useful checks:

```powershell
Get-ChildItem -LiteralPath .agents/skills -Directory | Sort-Object Name
Get-ChildItem -LiteralPath .agents/skills -Recurse -Filter SKILL.md -File
git ls-files .agents/skills
git status --short -- .agents/skills
rg -n --hidden "OpenClaw|Claude|Cowork|\.claude|skills/|python |pip |intake/tmp/[0-9]{4}|fallback|legacy|deprecated|TODO|TBD" .agents/skills
```

Treat broad-search output as a queue for inspection, not as findings by itself. Some terms are valid in examples, search commands, or compatibility notes; classify each match by active behavior and ownership.

Useful checks:

These examples use PowerShell. Adapt the path list, quoting, and conditional lint command to the current shell.

```powershell
rg --files --hidden -g "!**/.git/**" -g "!**/.venv/**" -g "!**/__pycache__/**" -g "!**/.pytest_cache/**"
rg --files --hidden --no-ignore -g "!**/.git/**" -g "!**/.venv/**" -g "!**/__pycache__/**" -g "!**/.pytest_cache/**" -g "!**/node_modules/**"
git ls-files
git status --ignored --short
$reviewPaths = @("AGENTS.md","CLAUDE.md","WIKI.md","PROJECT.md","README.md","README.zh-CN.md","pyproject.toml",".env.example","docs","scripts",".agents/skills") | Where-Object { Test-Path $_ }
rg -n --hidden "intake/tmp/[0-9]{4}|intake/processed/[0-9]{4}|skills/obsidian-wiki-lint|TODO|TBD|legacy|deprecated|fallback" $reviewPaths
if (Test-Path wiki) { uv run --no-project .agents/skills/obsidian-wiki-lint/scripts/lint_wiki.py --vault . --scope wiki }
```

Treat command output as evidence. A matching string is not automatically a bug; decide whether the surrounding rule still matches the current contract.
Expect some benign matches from templates, tests, compatibility metadata, variable names, and this skill's own search examples. Classify each match by ownership and active behavior before reporting it.

### 3. Redundancy and Conflict Review

Classify every issue by ownership before proposing changes:

| Surface | Owns |
| --- | --- |
| `WIKI.md` | Stable wiki operating contract, directory lifecycle, source traceability, workflow rules |
| `AGENTS.md` / `CLAUDE.md` | Agent entrypoint behavior, runtime command rules, initialization rules, package workflow |
| `PROJECT.md` | Vault-specific subject, structure preferences, provider choices, naming preferences, project-specific rules |
| `.agents/skills/` | Reusable local procedures and deterministic tool guidance |
| `scripts/` | Package installation, upgrade, and repeatable automation |
| `README*` and `docs/` | Human-facing setup and usage explanation |
| Runtime folders | Actual wiki knowledge, intake state, logs, questions, artifacts |

Look for:

- The same rule stated differently across surfaces.
- Runtime paths that conflict with `WIKI.md`.
- Project-specific preferences stored in package-level files.
- Package-level rules hidden only in human docs.
- Old workflow names, compatibility branches, fallback language, deprecated aliases, or migration notes that now act as instructions.
- Local-only or ignored root artifacts such as vault settings, adapter workspaces, attachment folders, archives, caches, temporary outputs, or generated lockfiles that could be copied, committed, or mistaken for package source.
- Skill auxiliary files such as `README.md`, `POST_INSTALL.md`, `_meta.json`, `package.json`, `assets/`, tests, hooks, or copied upstream references that are stale, redundant, or inconsistent with the package-local contract.
- Provider/helper skill descriptions or examples that imply direct source processing without the wiki router, `source-extraction`, `PROJECT.md` policy, or Source Review Gate.
- Runtime dependency files and environment templates that disagree with documented setup, provider setup references, or script behavior.
- English and translated docs that disagree on commands, required files, script parameters, provider setup, or working-root semantics.
- Intake, source-card, log, or question folders that duplicate each other instead of linking to one source of truth.
- Accepted sources represented in multiple raw states.
- Intake outputs without required `source.md`, `summary.md`, or `manifest.md`.
- Source cards that are only receipts instead of content-rich wiki summaries.

For review-only requests, report cleanup opportunities, deletion candidates, source-interpretation conflicts, category redesign needs, and substantive contradictions as findings only. Do not ask for editing confirmation, start edits, or convert the review into a fix task. If the user later asks for fixes, treat that as a new fix task.

If the user explicitly requested fixes, mechanical cleanup can be done directly when the correct fix is uniquely determined. For page deletion, source interpretation, category redesign, or resolving substantive contradictions during a fix task, report the conflict and ask for confirmation before editing.

## Output Format

Return a concise engineering review:

```markdown
## Conclusion
[Conforming / Non-conforming / Needs decision]

## Findings
- [Severity] [File/path] [Issue] [Why it conflicts with the current contract] [Recommended fix]

## Script Migration Check
[What was verified about init/upgrade/manifest behavior.]

## Redundancy and Conflict Check
[What was verified across docs, skills, runtime folders, and wiki pages.]

## Full Local Skill Check
[Per-skill summary plus the skill boundary matrix. State which skills were validated, which are package-managed, which are local-only, and which need decisions.]

## Verification
[Commands or inspections run, with outcome.]

## Decisions Needed
[Only unresolved user decisions.]
```

Use exact file paths and line references when possible. Do not bury blockers in a general summary.

## Guardrails

- Do not create a new canonical contract when `WIKI.md`, `AGENTS.md`, or `PROJECT.md` already owns the rule.
- Do not preserve rejected or obsolete behavior as a compatibility layer unless the user explicitly asks for migration support.
- Do not fix unrelated style, formatting, or prose while reviewing contract drift.
- Do not assume `PROJECT.md` template blanks authorize invented project preferences.
- Do not move, rename, delete, or rewrite original source files under `raw/` unless the user explicitly asks.
- Do not use custom parsing scripts to replace the basic Obsidian link checks provided by `obsidian-wiki-lint`; run that skill first for link and orphan baselines when reviewing wiki content.

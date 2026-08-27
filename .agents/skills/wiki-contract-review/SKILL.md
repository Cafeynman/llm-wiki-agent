---
name: wiki-contract-review
description: Use when reviewing this LLM Wiki package or an initialized vault for workflow, script, skill, runtime-structure, init/upgrade, or documentation contract drift. Use wiki-quality-review for page-level knowledge content quality.
---

# Wiki Contract Review

Use this skill for Maintain Wiki or package-maintenance reviews where the risk is contract drift across scripts, entrypoint docs, local skills, human docs, and runtime wiki folders. It checks whether required knowledge surfaces and lifecycle records satisfy the contract; it does not judge the factual, interpretive, or epistemic quality of page content.

When the user requests a full package contract review of this development
package root, do not sample local skills. Enumerate and inspect every universal
skill matching `.agents/skills/*/SKILL.md` and every scenario skill matching
`scenarios/*/skills/*/SKILL.md`, including untracked local review skills, then
classify whether each one belongs in the package, is local-only, or needs
cleanup. For scoped reviews, inspect only the surfaces needed to answer the
confirmed scope and state what was not reviewed.

The goal is to find whether the current implementation matches the wiki contract, whether each process has a clear closed loop from input to recorded outcome, and whether runtime structure follows its declared ownership. Do not treat one file as authoritative until you have identified the current source of truth.

## Review Fit

Before scanning, state the original need, confirmed scope, expected or candidate source-of-truth surfaces, expected target state, and success criteria. If those are unclear and the answer would change the review, ask before expanding scope.

Use the smallest review intensity that can answer the request:

- **Scoped review:** inspect only the directly affected contract, files, scripts, docs, skills, or runtime folders.
- **Contract review:** compare all surfaces that claim ownership of the same workflow, command, path, or state transition.
- **Full package review:** inspect package-managed files, scripts, docs, runtime boundaries, and every local skill.

Apply first-principles and assumption-minimal reasoning. Prefer the explanation or correction that accounts for the evidence with the fewest unsupported assumptions, but do not choose a simpler explanation that leaves material evidence unexplained.

Treat extra process as a risk until justified. Compatibility layers, fallback routes, duplicate workflows, optional side paths, dual implementations, extra configuration switches, and defensive safeguards are findings when they are not required by `WIKI.md`, `AGENTS.md`, `PROJECT.md`, a script contract, or the user's explicit request.

## Required Reading

Begin after the working root's complete `WIKI.md` and `PROJECT.md` have been read at conversation start and `AGENTS.md` has been read on first entry. Read the remaining files when they are relevant to the confirmed scope; for a full package contract review, read all applicable files in this list.

1. `AGENTS.md` and any optional adapter entrypoints for repository workflow, runtime, skill-source, precedence, and ownership rules.
2. `WIKI.md` for the stable wiki directory contract and Add Knowledge, Use Knowledge, and Maintain Wiki workflows.
3. `PROJECT.md` only for project-specific preferences; do not use it as a stable package contract.
4. `scripts/package-files.txt`, `scripts/init.ps1`, `scripts/init.sh`, `scripts/upgrade.ps1`, and `scripts/upgrade.sh` when reviewing migration, initialization, or upgrade behavior.
5. For full package reviews or local skill consistency reviews, inspect every
   universal skill under `.agents/skills/` and every scenario skill under
   `scenarios/*/skills/`, not global skill copies. For scoped package-root
   reviews, inspect only the skills directly connected to the confirmed scope.
   For initialized-vault reviews, inspect the target vault's universal skills
   plus only the active scenario recorded in `PROJECT.md`; do not load inactive
   scenario skills. Compare with the package root only when migration or
   package-source drift is in scope.
6. `README.md`, `README.zh-CN.md`, and `docs/` only when user-facing setup or usage wording may conflict with the entrypoint and wiki contracts.
7. `.gitignore`, `git ls-files`, and `git status --ignored --short` when reviewing package boundaries, local residue, or migration risk.
8. `pyproject.toml`, `.env.example`, and provider setup references when reviewing runtime, dependency, or environment-variable contracts.
9. Target-only skills and competing persistence surfaces such as `.learnings/`,
   memory files, or skill-driven edits to entrypoint contracts when reviewing an
   initialized vault. Check tracked project files for private service locations;
   non-secret provider choices belong in `PROJECT.md`, while values belong only
   in `.env`.

If the user gives a separate vault root, inspect that initialized vault as the working root for runtime structure, and inspect the package root only for package source files and scripts.

## Review Plan

Start every review by stating the target root, whether it is a package root or initialized vault, and the specific surfaces in scope. For full package reviews, use at least three independent repository scans before concluding. For scoped reviews, run the smallest set of scans that can prove or disprove the scoped risk and name any excluded surfaces.

1. **Flow and simplicity scan:** trace input, owner, decision gates, state transitions, outputs, logs, cleanup, and next action. Flag unclosed states, duplicate routes, hidden side paths, and branches that exist only as speculative safety or historical residue.
2. **Contract scan:** inventory package source files, hidden files, the current package inventory, a target's prior 1.0+ inventory when present, scripts, entrypoint docs, and package-managed skills.
3. **Full local skill scan:** enumerate all `.agents/skills/*/SKILL.md` and
   `scenarios/*/skills/*/SKILL.md` files, validate each skill, inspect auxiliary
   files, and compare trigger and ownership boundaries across universal and
   scenario scopes.
4. **Residue scan:** search for stale paths, conflicting wording, duplicated rules, obsolete workflow terms, local runtime artifacts, and generated files that should not be treated as package source.

Do not stop after a single broad grep. Hidden directories are part of the review surface because `.agents/`, editor configuration, and tool workspaces can change how agents interpret the repository.

### 1. Flow and Simplicity Fit

Check whether each reviewed workflow has one clear canonical route for the confirmed task type.

1. Identify the initiating input, owning contract, required decision gates, state changes, and final recorded outcome.
2. Verify closure: accepted, rejected, blocked, or deferred items must end in a documented state with the required log, question, artifact, cleanup, or next action.
3. Compare English docs, translated docs, scripts, and skills for the same user action. They should describe the same root semantics, generated files, cleanup behavior, and stopping conditions.
4. Flag unnecessary branches such as duplicate commands, hidden fallbacks, compatibility routes, optional modes, speculative safeguards, or alternate output locations that are not contract-owned.
5. Check process weight. The workflow should ask for only the review depth, delegation, external review, tests, or reports justified by the user's scope and the risk.
6. Recommend the smallest correction that closes the loop: delete, narrow, merge, reroute to the owner, or clarify the canonical path. Do not add a new option or fallback to avoid a direct decision.
7. Verify that every conversation begins by reading the active root's complete
   `WIKI.md` and `PROJECT.md` before planning, searching, answering, delegating,
   or writing. Programming, resumed conversations, and delegated conversations
   use the same gate. Wording that limits it to apparent wiki work or to only
   the files thought relevant is contract drift.

### 2. Script and Migration Fit

Check whether scripts and package-managed files match the current wiki structure.

1. Derive the expected runtime directories from `WIKI.md` and the initialization rules in `AGENTS.md`.
2. Confirm `init` and `upgrade` scripts create the same required runtime directories and seed files.
3. Confirm `scripts/package-files.txt` is the single complete list of stable package files and future retired paths, including `.agents/skills`, `docs`, `scripts`, `AGENTS.md`, and `WIKI.md` when present. It must declare the supported schema once, use only `active <path>` and `remove <path>`, and own itself as an active path. A `remove` record persists through later inventories until that path explicitly returns as `active`; silently dropping it would break direct updates from an earlier 1.0+ generation. Optional runtime adapters may remain user-owned instead of package-owned.
4. Confirm initialization and upgrade derive target ownership only from the target's prior valid inventory and the current package inventory. They must not use target Git state, version numbers, or persisted or guessed content hashes as ownership metadata; a transient byte-equivalence check may decide whether an existing path is safe to adopt during first adoption. A missing target inventory is first adoption; an existing malformed or unsupported inventory blocks before writes. Check create, byte-identical adoption, replace, explicit remove, conflict, future tombstone, and inventory-last paths. The current inventory is committed atomically only after dependency synchronization, leaving it absent or at the previous complete generation after interruption. Verify first-adoption reruns from the original package root and conflicting edits to newly copied paths remain conservative. Do not require or preserve pre-1.0 readers, normalization passes, paired metadata, or checkpoint inventories.
5. Confirm package-owned files are copied from the package root and workspace-specific context stays in `PROJECT.md`.
6. Compare `git ls-files`, `git status --ignored --short`, and the current package inventory so untracked archives, ignored vault folders, adapter directories, caches, and runtime folders are not mistaken for publishable package source. This source-package integrity check does not define ownership in an initialized target.
7. Verify that initialization and upgrade preserve an existing target-owned
   `.gitignore` domain policy. They may add required secret and technical-cache
   rules, but must not infer a private or versioned wiki-runtime policy from an
   unrecognized existing file. If `.gitignore` is absent, they install the
   package's default private runtime policy without consulting target Git state.
8. Search scripts and skills for stale path contracts such as dated intake directories, old skill paths, missing `.agents/skills` prefixes, unsupported runtime folders, or hardcoded scenario-specific paths.
9. Verify script examples in skills and docs are executable from the documented root and use `uv run` where the project contract requires it.
10. If both English and translated docs exist, check that setup commands, script parameter names, root semantics, and package/runtime boundaries are aligned across languages.
11. Check provider/helper skills against the owning workflow contract. Extraction helpers must not bypass `source-extraction`, `PROJECT.md` provider policy, Source Review Gate, or the text-first wiki lifecycle.
12. Check `pyproject.toml`, lockfiles when present, `.env.example`, provider setup docs, and runtime commands for dependency or environment drift.

### 3. Full Local Skill Review

When full package review or local skill consistency review is in scope, review
every universal skill under `.agents/skills/` and every scenario skill under
`scenarios/*/skills/`. This is not optional within that scope and is not limited
to the skills that broad searches happen to match. In an initialized vault,
review only the active scenario recorded in `PROJECT.md` unless package-source
drift across inactive scenarios is explicitly in scope.

For each skill:

1. Record directory name, `name` frontmatter, trigger description, tracked/untracked status, and whether it is package-managed or local-only.
2. Read `SKILL.md` and list directly owned scripts, references, assets, agents metadata, tests, README-like files, setup notes, package manifests, hooks, and other auxiliary files.
3. Run structural validation:

   ```powershell
   uv run --no-project python .agents/skills/skill-creator/scripts/quick_validate.py <skill-directory>
   ```

4. Check whether the trigger description overlaps another local skill or bypasses the owner of a workflow. Provider/helper skills must point back to their router; router skills must not hide provider-specific secrets or scenario-specific behavior.
5. Check runtime portability. Flag active instructions that assume a specific runtime, stale user-level paths, direct `python`/`pip` where this package requires `uv run`, runtime-specific skill paths that conflict with `.agents/skills`, or hidden local service assumptions.
6. Check package suitability. Flag skill-specific README, `POST_INSTALL.md`, `_meta.json`, `package.json`, hooks, copied upstream docs, or examples when they are stale, redundant, or not needed for the package contract.
7. Check source-control status. A skill inside an inventory-managed directory but untracked is pending local state, not confirmed package source, until the user decides to add it.

Build a skill boundary matrix before reporting:

| Skill | Role | Trigger owner | Depends on | Must not bypass | Status |
| --- | --- | --- | --- | --- | --- |

Use this matrix to find duplicated triggers, missing routers, stale provider claims, and local-only tools that should not be committed.

Useful full-skill checks:

```powershell
Get-ChildItem -LiteralPath .agents/skills -Directory | Sort-Object Name
Get-ChildItem -LiteralPath .agents/skills -Recurse -Filter SKILL.md -File
Get-ChildItem -LiteralPath scenarios -Recurse -Filter SKILL.md -File
git ls-files .agents/skills
git ls-files scenarios
git status --short -- .agents/skills
git status --short -- scenarios
rg -n --hidden "skills/|python |pip |intake/tmp/[0-9]{4}|fallback|legacy|deprecated|TODO|TBD" .agents/skills scenarios
```

Treat broad-search output as a queue for inspection, not as findings by itself. Some terms are valid in examples, search commands, or compatibility notes; classify each match by active behavior and ownership.

Useful package checks:

These examples use PowerShell. Adapt the path list, quoting, and conditional lint command to the current shell.

```powershell
rg --files --hidden -g "!**/.git/**" -g "!**/.venv/**" -g "!**/__pycache__/**" -g "!**/.pytest_cache/**"
rg --files --hidden --no-ignore -g "!**/.git/**" -g "!**/.venv/**" -g "!**/__pycache__/**" -g "!**/.pytest_cache/**" -g "!**/node_modules/**"
git ls-files
git status --ignored --short
$reviewPaths = @("AGENTS.md","WIKI.md","PROJECT.md","README.md","README.zh-CN.md","pyproject.toml",".env.example","docs","scripts",".agents/skills","scenarios") | Where-Object { Test-Path $_ }
rg -n --hidden "intake/tmp/[0-9]{4}|intake/processed/[0-9]{4}|skills/obsidian-wiki-lint|TODO|TBD|legacy|deprecated|fallback" $reviewPaths
if (Test-Path wiki) { uv run --no-project .agents/skills/obsidian-wiki-lint/scripts/lint_wiki.py --vault . --scope wiki }
```

Treat command output as evidence. A matching string is not automatically a bug; decide whether the surrounding rule still matches the current contract.
Expect some benign matches from templates, tests, compatibility metadata, variable names, and this skill's own search examples. Classify each match by ownership and active behavior before reporting it.

### 4. Redundancy and Conflict Review

Classify every issue by ownership before proposing changes:

| Surface | Owns |
| --- | --- |
| `WIKI.md` | Stable wiki operating contract, directory lifecycle, source traceability, workflow rules |
| `AGENTS.md` / optional adapter entrypoints | Agent entrypoint behavior, runtime command rules, initialization rules, package workflow |
| `PROJECT.md` | Vault-specific subject, structure preferences, provider choices, naming preferences, project-specific rules |
| `.agents/skills/` | Universal reusable procedures and deterministic tool guidance |
| `scenarios/<name>/skills/` | Scenario-only procedures loaded only for the active relevant scenario |
| `scripts/` | Package installation, upgrade, and repeatable automation |
| `README*` and `docs/` | Human-facing setup and usage explanation |
| Runtime folders | Actual wiki knowledge, intake state, logs, questions, artifacts |

Look for:

- The same rule stated differently across surfaces.
- Runtime paths that conflict with `WIKI.md`.
- Project-specific preferences stored in package-level files.
- Package-level rules hidden only in human docs.
- Old workflow names, compatibility branches, fallback language, deprecated aliases, or migration notes that now act as instructions.
- Workflows that branch without a contract-owned decision point, require more process than the current risk justifies, or fail to close each state with a log, artifact, question, cleanup step, or documented next action.
- Local-only or ignored root artifacts such as vault settings, adapter workspaces, attachment folders, archives, caches, temporary outputs, or generated lockfiles that could be copied, committed, or mistaken for package source.
- Target-only skills or learning and memory files that auto-trigger writes,
  compete with `WIKI.md` runtime ownership, or promote rules into `AGENTS.md`,
  `WIKI.md`, or `PROJECT.md` without an explicit user request.
- Private service locations or credentials stored in `PROJECT.md`, tracked
  documentation, manifests, logs, source cards, or skills instead of `.env`.
- Skill auxiliary files such as `README.md`, `POST_INSTALL.md`, `_meta.json`, `package.json`, `assets/`, tests, hooks, or copied upstream references that are stale, redundant, or inconsistent with the package-local contract.
- Provider/helper skill descriptions or examples that imply direct source processing without the wiki router, `source-extraction`, `PROJECT.md` policy, or Source Review Gate.
- Runtime dependency files and environment templates that disagree with documented setup, provider setup references, or script behavior.
- English and translated docs that disagree on commands, required files, script parameters, provider setup, or working-root semantics.
- Intake, source-card, log, or question folders that duplicate each other instead of linking to one source of truth.
- Accepted sources represented in multiple raw states.
- Intake outputs without required `source.md`, `summary.md`, or `manifest.md`.
- Source cards that lack contract-required sections or traceability links.

For review-only requests, report contract cleanup opportunities, package deletion candidates, workflow ownership conflicts, and directory or category redesign needs as findings only. Do not ask for editing confirmation, start edits, or convert the review into a fix task. If the user later asks for fixes, treat that as a new fix task.

If the user explicitly requested fixes, mechanical cleanup can be done directly when the correct fix is uniquely determined. For package-managed deletion, category or directory redesign, workflow ownership changes, or other contract decisions, report the conflict and ask for confirmation before editing.

## Output Format

Return a concise engineering review:

```markdown
## Conclusion
[Conforming / Non-conforming / Needs decision]

## Findings
- [Severity] [File/path] [Issue] [Why it conflicts with the current contract] [Recommended fix]

## Flow and Simplicity Check
[Whether the process has a clear canonical route, closed states, proportionate review depth, and no unjustified branches or fallback paths.]

## Script Migration Check
[What was verified about init/upgrade/inventory behavior.]

## Full Local Skill Check
[When in scope, per-skill summary plus the skill boundary matrix. State which skills were validated, which are package-managed, which are local-only, and which need decisions.]

## Redundancy and Conflict Check
[What was verified across docs, skills, runtime folders, and wiki pages.]

## Verification
[Commands or inspections run, with outcome.]

## Decisions Needed
[Only unresolved user decisions.]
```

For scoped reviews, omit sections that are not in scope, but state inspected surfaces, excluded surfaces, verification, and residual risk.

Use exact file paths and line references when possible. Do not bury blockers in a general summary.

## Guardrails

- Do not create a new canonical contract when `WIKI.md`, `AGENTS.md`, or `PROJECT.md` already owns the rule.
- Do not preserve rejected or obsolete behavior as a compatibility layer unless the user explicitly asks for migration support.
- Do not call a branch, fallback, duplicate route, or extra review step "safer" unless a named contract, concrete risk, or user requirement justifies it.
- Do not require full-audit ceremony, subagents, or external model review for a scoped review when the evidence can be checked directly.
- Do not fix unrelated style, formatting, or prose while reviewing contract drift.
- Do not use this skill to judge page-level factual accuracy, source interpretation, argument quality, counterevidence, or semantic completeness; use `wiki-quality-review` for those tasks.
- Do not assume `PROJECT.md` template blanks authorize invented project preferences.
- Do not move, rename, delete, or rewrite original source files under `raw/` unless the user explicitly asks.
- Do not use custom parsing scripts to replace the basic Obsidian link checks provided by `obsidian-wiki-lint`; run that skill first for link and orphan baselines when reviewing wiki content.

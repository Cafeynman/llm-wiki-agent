---
name: skill-creator
description: Create, update, simplify, or review reusable agent skills. Use when a user wants a new skill, wants an existing skill generalized, asks whether skills are stale or overlapping, needs skill metadata/frontmatter fixed, or wants a skill packaged for reuse across Codex, LMVT, or other agent runtimes.
---

# Skill Creator

Use this skill to create or maintain reusable skills for agent workflows. A good skill captures durable procedure, tool routing, file contracts, and judgment patterns that an agent cannot reliably infer from the user prompt alone.

Keep skills portable. Do not write the skill as if one runtime, one project, one conversation, or one incident is the whole world unless that runtime or project is the explicit target.

## Core Workflow

1. Confirm the target behavior.
2. Decide whether this is a new skill, a rewrite of an existing skill, or a cleanup of overlapping skills.
3. Inspect the current skill directory before editing.
4. Write the smallest skill body that makes the reusable workflow clear.
5. Keep runtime-specific instructions conditional.
6. Validate the skill structure and the changed behavior.
7. Package or commit the result only after reviewing the final diff.

If the user has already confirmed the direction, implement it. Ask only when the intended trigger, output contract, runtime target, or compatibility boundary is unclear.

## Skill Shape

A skill is a directory with one required file:

```text
skill-name/
├── SKILL.md
├── agents/        optional UI metadata
├── scripts/       optional deterministic helpers
├── references/    optional context loaded only when needed
└── assets/        optional output resources
```

`SKILL.md` must contain YAML frontmatter with:

```yaml
---
name: skill-name
description: When to use this skill and what it does.
---
```

The `description` is the trigger surface. Put trigger conditions there, not only in the body. Make it specific enough to distinguish the skill from nearby skills, but not so narrow that it only fires for one phrase.

## Writing Rules

Write reusable judgment patterns, not incident notes.

Good skill content:

- States when the skill applies.
- Defines the required reading or input inspection.
- Gives a short execution workflow.
- Routes to scripts or references instead of embedding large material.
- Names output files, formats, and verification commands when those are part of the contract.
- Explains runtime-specific behavior as conditional guidance.

Avoid:

- One-off project names, current conversation details, temporary paths, or personal examples unless they are stable interfaces.
- Tool commands that assume one runtime when the skill is meant to be portable.
- README, changelog, install notes, or history files inside a skill unless a consuming runtime requires them.
- Compatibility layers, fallback behavior, or old workflow names unless the user explicitly asks to preserve them.
- Long narrative explanations that duplicate what a script or reference file already provides.

## Runtime Portability

Write for the current repository's agent contract first. In this repository, local package skills live under `.agents/skills/` and package commands should be executable from the package root.

When a step depends on a runtime capability, phrase it conditionally:

- If subagents are available, use them for independent validation.
- If a browser or reviewer UI is available, use the bundled viewer.
- If only shell commands are available, use deterministic scripts and direct file inspection.
- If a command is runtime-specific, name the runtime and keep the command out of the generic path.

Do not mention a specific agent runtime as the default unless the skill is explicitly for that runtime.

## Creating A Skill

Capture these facts before drafting:

1. Purpose: what the skill helps the agent do.
2. Trigger: what task shapes should load it.
3. Inputs: files, prompts, tools, credentials, or project state it depends on.
4. Outputs: final files, comments, reports, edits, or decisions.
5. Verification: commands, inspections, or examples that prove it works.
6. Boundaries: what the skill must not do.

Then create the minimal directory and `SKILL.md`. Add `scripts/` only for repeated deterministic work. Add `references/` only when the body would otherwise become too long or variant-specific.

## Updating A Skill

Preserve the existing skill name unless the user explicitly asks for a rename.

Before editing:

1. Read `SKILL.md`.
2. Inventory scripts, references, agents metadata, assets, and auxiliary files.
3. Search for stale names, runtime assumptions, old commands, fallback paths, and duplicated instructions.
4. Identify nearby skills that overlap in trigger or responsibility.

During editing:

- Update frontmatter and body together.
- Keep the canonical route clear when multiple skills are involved.
- Move stable shared rules into the owning skill, not into every provider/helper skill.
- Delete stale wording that keeps rejected behavior alive.
- Keep provider/helper skills narrow when another skill owns routing or policy.

After editing, search again for old trigger words, obsolete paths, platform-specific commands, and stale auxiliary files.

## Progressive Disclosure

Keep `SKILL.md` short enough that loading it is useful, not expensive. Put only the core workflow in the body.

Use this split:

| Location | Use for |
| --- | --- |
| `SKILL.md` | Trigger, routing, core workflow, guardrails, verification |
| `references/` | Long docs, schemas, variant-specific instructions |
| `scripts/` | Deterministic conversion, linting, validation, packaging |
| `assets/` | Templates or resources used in final outputs |
| `agents/openai.yaml` | UI metadata when the runtime supports it |

Reference files should be discoverable from `SKILL.md` and loaded only when relevant.

## Validation

Use the narrowest validation that proves the changed skill is usable.

Minimum checks:

```powershell
uv run --no-project .agents/skills/skill-creator/scripts/quick_validate.py .agents/skills/<skill-name>
```

Also inspect:

```powershell
rg -n "old-name|old-command|old-path|old-runtime|TODO|TBD" .agents/skills/<skill-name>
git diff -- .agents/skills/<skill-name>
```

Adjust the residue search terms to the actual old concept. A match is not automatically a bug; inspect context before changing it.

For behavior-heavy skills, add realistic prompt checks. If the current runtime supports independent agents, run one or two independent validation prompts against the revised skill. If it does not, do a manual dry run against a small representative task and record what was checked.

## Packaging

Package only after the skill validates and the diff is clean.

If a packaging script exists in this skill directory, prefer it:

```powershell
uv run --no-project .agents/skills/skill-creator/scripts/package_skill.py .agents/skills/<skill-name>
```

If the skill is package-managed by this repository, commit the skill directory through Git rather than copying it into a user-level skills folder.

## Review Checklist

Before finishing, confirm:

- The trigger description matches the current target behavior.
- The body is runtime-portable unless a runtime-specific target was requested.
- The skill does not duplicate a nearby skill's policy ownership.
- Provider/helper skills do not bypass their router or owning workflow.
- Scripts and references are still reachable and accurately described.
- No stale names, old commands, or rejected concepts remain in active instructions.
- Validation was run against the changed skill.

For review-only requests, report findings by severity with file references. For implementation requests, make the smallest direct change and commit only the intended skill files when the user asks for Git history.

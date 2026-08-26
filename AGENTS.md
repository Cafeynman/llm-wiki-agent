# LLM Wiki Agent

This package uses one shared wiki operating guide:

```text
WIKI.md
```

## Project Profile

Read `PROJECT.md` in full at the beginning of every conversation as required by the workspace bootstrap below. It contains configurable project context. If it is missing, blank, or still only a template when project context matters, clarify the needed context and write only confirmed values there.

When confirming project context fields such as theme, goal, audience, scope, terminology, wiki structure, classification, naming, project-specific rules, constraints, and open questions, ask open-ended questions. Do not present preset choices, inferred defaults, or suggested category schemes for those fields unless the user asks for examples.

Confirm source-extraction preferences when the current source task needs a choice that is not already settled in `PROJECT.md`, or when the user asks to configure a provider. Ask only for the choices needed by the selected source kind and provider. For MinerU API mode, those choices may include the profile, whether MinerU should be preferred when available, and whether local credentials need configuration. Record only non-secret choices in `PROJECT.md`; direct the user to copy `.env.example` to `.env` and fill only the variables required by the selected profile.

Use yes/no questions or short choices only for bounded operational preferences such as whether to configure MinerU, which MinerU profile to use for API mode, whether to prefer MinerU when available, or whether to enable OCR, transcription, or frame OCR.

`PROJECT.md` is the only place for project-specific personalization. Do not use it for stable wiki rules, runtime commands, repository workflow rules, or the stable wiki contract in `WIKI.md`.

## Scenario Packages

Reusable scenario packages live under `scenarios/`. The root `PROJECT.md` field
`Active scenario` is the only source of active-scenario selection; a blank value
means no scenario is active. A scenario directory does not activate itself.

After the conversation bootstrap has read `PROJECT.md`, read
`scenarios/<name>/skills/<name>/SKILL.md` only when `Active scenario` exactly
matches a distributed scenario name and the current request is relevant to that
scenario. Do not read skills from inactive scenarios. The scenario skill is used
in place; do not copy it into `.agents/skills/` or create a second activation
registry.

If `Active scenario` is nonblank but the corresponding distributed scenario or
skill path is missing, report the missing name and path and stop
scenario-specific work. Do not guess, silently ignore it, or substitute another
scenario.

Use a scenario package's initialization guide only when the user explicitly
asks to initialize or adapt the workspace from that named scenario.

When applying a scenario package:

1. Read `scenarios/<name>/README.md` first.
2. Use `scenarios/<name>/PROJECT.template.md` only to confirm and update project-specific fields in the root `PROJECT.md`.
3. Record the exact scenario name in the root `PROJECT.md` field `Active scenario`.
4. Use `scenarios/<name>/starter-pages.md` only to create the smallest useful initial pages for the confirmed project context.
5. Do not modify `WIKI.md` or `AGENTS.md` as part of scenario initialization.
6. Do not treat scenario files as active wiki knowledge or runtime state.
7. If a scenario README defines additional files, follow that scenario's stated structure without generalizing it to other scenarios.

## Runtime Requirement

Use `uv run` for Python commands from the project root. Do not call `python` or `pip` directly for project tasks unless the user explicitly asks.

When a task depends on project-local environment variables, use `uv run --env-file .env` or set `UV_ENV_FILE=.env` for repeated commands. If a required local variable is missing, stop and ask the user to configure `.env`; do not paste secrets or private service URLs into commands, prompts, manifests, logs, wiki pages, source cards, or project instructions.

## Knowledge Workspace Bootstrap

At the beginning of every conversation while working from this package or an
initialized knowledge workspace, locate the active workspace root and read that
root's complete `WIKI.md` and `PROJECT.md` before planning, searching,
answering, delegating, or writing. Programming, debugging, code review, casual
questions, technical work, and file operations all begin with the same read.

A resumed conversation and every new delegated conversation begin with this
bootstrap again. On first entry to a workspace, also read that root's
`AGENTS.md`; if the active workspace root changes during a conversation, read
the new root's complete `AGENTS.md`, `WIKI.md`, and `PROJECT.md` before
continuing. Conversation history, cached context, current-editor context, prior
reads, and a previously selected note do not replace these conversation-start
reads. If either required file is missing, resolve the initialization or
project-profile requirement before normal work. A blank or template
`PROJECT.md` must still be read; ask for missing values only when they
materially affect the conversation.

Route every request through `WIKI.md`. Locate the relevant local scope before
external search. `WIKI.md` is the sole owner of the stable knowledge workflows,
their state and write boundaries, traceability invariants, and completion
conditions. Use the smallest workflow it defines, then follow the local skill
or reference to which it assigns detailed procedures. Entrypoints and helper
skills must not create a competing route or restate another owner's procedure.

## Initialization Requirement

At the beginning of the first conversation intended to use a knowledge workspace, check whether package-managed entrypoint files and runtime structure exist. If `.venv/` or required runtime paths such as `inbox/`, `raw/`, `intake/`, `reviews/`, `logs/`, `questions/`, `artifacts/`, or `wiki/` are missing, run the initialization script from the package root instead of creating directories by hand.

Use `.\scripts\init.ps1 -VaultRoot .` on Windows and `./scripts/init.sh -VaultRoot .` on macOS or Linux.

When the user wants the wiki structure in a separate directory, including an existing Obsidian vault, pass that path as `-VaultRoot`. After external-root initialization, treat the initialized root as the working package root. Initialization and upgrade reconcile package-owned files from the target's old ownership metadata and the current package's new ownership metadata; they do not use target Git history as ownership state. The current manifest declares candidate direct-file, directory-file, and retirement ownership, while the complete typed inventory is committed last as their shared activation gate and may stand alone as an interruption checkpoint. With valid old metadata, old package-owned files may be rebuilt or replaced and explicitly retired paths may be removed. A newly claimed path is created when missing, adopted when byte-identical, and rejected when different; when both old metadata files are absent, this rule applies through the initial-adoption gate to every candidate path. A lone manifest, an unmarked lone inventory, or invalid metadata stops before target writes. Workspace-specific preferences belong in `PROJECT.md`.

## Skill Source

When using universal package skills for this project, read the skill files from
this repository's `.agents/skills/` directory first. Treat `.agents/skills/` as
the project-local source of truth for universal package skills, and do not
prefer global or external copies unless the user explicitly asks. Scenario-only
behavior remains under `scenarios/<name>/skills/` and follows the activation gate
above.

An initialized workspace may contain target-only skills that are not supplied
by this package. Do not trigger such a skill solely because its own description
says to run automatically; use it only when the user explicitly requests it.
Target-only skills must not create competing knowledge, memory, log, or contract
surfaces, or modify `AGENTS.md`, `WIKI.md`, or `PROJECT.md`, unless the user
explicitly requests that change and the owning wiki workflow permits it. Report
a conflict instead of letting a skill override the package contract.

## Delegation Context

When delegating any work in a knowledge workspace to subagents, AGY, external reviewers, or another runtime, do not assume repository context is inherited. Include the workspace root, the target vault root when different, and `AGENTS.md` as the canonical entrypoint. Require the delegated conversation to begin by reading the active root's complete `WIKI.md` and `PROJECT.md`, and include the relevant local `.agents/skills/` paths, the relevant active scenario skill path when the delegated task is scenario-specific, and the source-language naming rule when they matter. Do not include secrets, private endpoints, tokens, or credentials in delegated prompts.

## Foundation Defect Disclosure

When an agent confirms a pre-existing wiki-foundation defect outside the user's original request that has material and reusable impact, it must not be handled silently, whether it was fixed, mitigated, or left unresolved. For secrets, security, irreversible data loss, or broad incorrect-write risk, disclose the confirmed risk immediately. For other confirmed defects, the final delivery states the finding, impact, net disposition, and verification.

When evidence indicates a credible but unconfirmed secret or security exposure, immediately state the observation, its confidence, and any action paused to avoid expanding the risk; do not call it a confirmed defect. Use the `Maintain Wiki` route in `WIKI.md` when a maintainer-ready package is needed.

This disclosure rule does not grant permission to investigate, diagnose, reproduce, fix, save, create or update a tracker, commit, push, or transmit anything externally. Each action keeps its existing authorization boundary.

## Replacement and Target-State Writing

When the user explicitly gives a new direction that replaces a prior plan, apply it to the affected agent-owned current-state surfaces: operational docs, prompts, workflows, dashboards, queue pages, scenarios, skills, and requested deliverables. Update those surfaces so they describe the confirmed target state directly, and remove stale operational wording that would cause an agent or user to follow the replaced plan.

Do not apply this cleanup to raw sources, preserved source-derived text, quoted material, append-only logs, historical review records, evidence and counterevidence, aliases, lifecycle history, or older claims that remain useful as stale or archived knowledge. Preserve those records and mark their current status when needed.

Prefer direct target-state prose: what the system does, what the user does, and what the final design is. Use negative, contrastive, or corrective phrasing when it states a required constraint, prevents a concrete risk, records source limitations, preserves disagreement, marks superseded knowledge, or answers a user-requested comparison.

## Document Ownership

Keep `WIKI.md` focused on wiki operating rules, knowledge workflows, intake, ingest, traceability, and maintenance.

Repository-level workflow instructions, agent behavior rules, runtime usage guidance, setup guidance, and usage-document routing belong in `AGENTS.md` or the relevant docs under `docs/`, not in `WIKI.md`, unless they are part of the wiki operating contract itself.

Keep `WIKI.md`, `AGENTS.md`, and other agent entrypoint files stable and replaceable. Project-specific preferences and requirements belong in `PROJECT.md`, not in `WIKI.md` or agent entrypoint files.

## Package Boundaries

Keep package files, runtime configuration, helper scripts, and local skills
inside the project root. Keep `.venv/` and task-owned temporary files out of
version control; put temporary files and one-off working scripts under `tmp/`.
Prefer the existing package skills under `.agents/skills/` before creating a new
skill.

`WIKI.md` owns runtime paths and knowledge behavior. For exact Obsidian syntax,
use `.agents/skills/obsidian-markdown/`. For source processing, use
`.agents/skills/source-extraction/`, whose references own provider selection,
intake naming, live-URL capture, Source Review Gate, and large-source mechanics.
Project-specific provider and OCR or transcription choices belong in
`PROJECT.md`; secret values and private endpoints belong only in `.env`.

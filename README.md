# LLM Wiki Agent Best Practices

LLM Wiki Agent is a best-practice workflow package for building and maintaining a persistent, traceable Obsidian-style Markdown knowledge base with an LLM agent.

The package gives the agent a clear operating contract: source files enter through `inbox/`, original files are preserved under `raw/`, reviewable Markdown is produced under `intake/`, durable knowledge is written into `wiki/`, and user-facing deliverables are saved under `artifacts/`.

## What This Is

This repository is not a full application server or a replacement for Obsidian. It is a portable workflow package for agents that can read repository instructions such as Codex, Claude Code, Gemini CLI, OpenCode, or similar tools.

The core idea is simple:

1. Put source material into `inbox/`.
2. Ask your agent to process the source according to `AGENTS.md` and `WIKI.md`.
3. The agent converts useful source material into reviewable Markdown.
4. The agent reviews the converted material before writing wiki knowledge.
5. Accepted knowledge becomes linked Markdown pages under `wiki/`.

## Package Contents

```text
.
├── AGENTS.md        Agent entrypoint and workflow routing rules.
├── WIKI.md          Complete operating guide for the LLM Wiki workflow.
├── USAGE.md         Installation, first run, and daily operating guide.
├── pyproject.toml   uv-managed Python dependencies for conversion workflows.
├── scripts/
│   └── init.ps1     PowerShell initializer for dependencies and wiki folders.
├── skills/          Local skills used by the agent package.
├── docs/
│   ├── references.md
│   └── acknowledgements.md
└── LICENSE
```

## Quick Start

Clone or download this repository, then enter the package directory:

```powershell
cd llm-wiki-agent
```

Initialize the Python environment and create the wiki folder structure:

```powershell
.\scripts\init.ps1 -VaultRoot .
```

For a separate Obsidian vault, pass the vault path:

```powershell
.\scripts\init.ps1 -VaultRoot "C:\path\to\your\vault"
```

Then open the folder or vault with your agent and ask it to use `AGENTS.md` as the instruction entrypoint. For wiki tasks, the agent should read `WIKI.md` before acting.

## Minimal First Run

After initialization, place a source file in `inbox/`:

```text
inbox/
└── example.md
```

Ask the agent:

```text
Process the files in inbox/ according to AGENTS.md and WIKI.md.
```

The expected lifecycle is:

```text
inbox/ -> intake/tmp/ -> source review -> raw/<state>/ + intake/processed/ + wiki/
```

The original source file is moved to exactly one raw state:

```text
raw/digested/
raw/needs-review/
raw/ignored/
raw/unsupported/
```

Only `digested` sources are promoted into `intake/processed/` and used to update `wiki/`.

## Core Workflow

The package keeps the agent on three workflows:

| Workflow | Use When |
| --- | --- |
| Add Knowledge | Add files, review sources, convert material, ingest accepted knowledge, or reflect confirmed discussion insights. |
| Use Knowledge | Answer questions from the wiki, synthesize pages, or create deliverables under `artifacts/`. |
| Maintain Wiki | Check broken links, missing sources, stale claims, contradictions, duplicate pages, and log gaps. |

The agent should choose the shortest workflow that fully satisfies the current request.

## Design Boundaries

- The workflow is text-first. Attachments, scans, screenshots, images, and audio may remain part of preserved original sources, but they are not first-class wiki content unless you explicitly add image or audio handling.
- Source review happens before wiki updates. A successful file conversion is not enough to accept a source.
- Original source files are preserved. Generated Markdown belongs under `intake/`, not `raw/`.
- User-facing reports, briefs, outlines, drafts, and templates belong under `artifacts/`, not `wiki/`.
- The package favors explicit traceability over hidden memory. Durable claims should cite source cards, intake output, raw files, or confirmed discussion records.

## Documentation

Read these files in order:

1. `README.md` for the project overview.
2. `USAGE.md` for installation and daily operation.
3. `AGENTS.md` for agent routing behavior.
4. `WIKI.md` for the full operating contract.
5. `docs/references.md` for idea references.
6. `docs/acknowledgements.md` for credits and thanks.

## References and Credits

This package builds on the LLM Wiki pattern and related public work. See `docs/references.md` for the reference list and `docs/acknowledgements.md` for acknowledgements.

## License

MIT License. See `LICENSE`.

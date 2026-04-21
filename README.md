# LLM Wiki Agent Best Practices

[Chinese version](README.zh-CN.md)

LLM Wiki Agent is a best-practice workflow package for building and maintaining a persistent, traceable Obsidian-style Markdown knowledge base with an LLM agent.

The package gives the agent a clear operating contract: source files enter through `inbox/`, original files are preserved under `raw/`, reviewable Markdown is produced under `intake/`, durable knowledge is written into `wiki/`, and user-facing deliverables are saved under `artifacts/`.

## What This Is

This repository is not a full application server or a replacement for Obsidian. It is a portable workflow package for agents that can read repository instructions such as Codex, Claude Code, Gemini CLI, OpenCode, or similar tools.

The core idea is simple:

1. Put source material into `inbox/`.
2. Ask your agent to process the source according to [AGENTS.md](AGENTS.md) and [WIKI.md](WIKI.md).
3. The agent converts useful source material into reviewable Markdown.
4. The agent reviews the converted material before writing wiki knowledge.
5. Accepted knowledge becomes linked Markdown pages under `wiki/`.

## Quick Start

Clone or download this repository, then enter the package directory:

```sh
cd llm-wiki-agent
```

Install or make available [uv](https://docs.astral.sh/uv/) first. The initialization scripts use `uv sync` to create the local Python environment.

Initialize the Python environment and create the wiki folder structure on Windows:

```powershell
.\scripts\init.ps1 -VaultRoot .
```

On macOS or Linux:

```sh
./scripts/init.sh -VaultRoot .
```

For a separate Obsidian vault, pass the vault path:

```powershell
.\scripts\init.ps1 -VaultRoot "C:\path\to\your\vault"
```

```sh
./scripts/init.sh -VaultRoot "/path/to/your/vault"
```

For full setup and operating details, read [docs/usage.md](docs/usage.md).

## Recommended Setup

- [Claudian](https://github.com/YishenTu/claudian): recommended if you want an Obsidian-oriented local agent environment.
- [Obsidian Web Clipper](https://github.com/obsidianmd/obsidian-clipper): recommended for collecting web pages into Markdown source material.

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

## Core Workflows

The package keeps the agent on three workflows:

| Workflow | Use When |
| --- | --- |
| Add Knowledge | Add files, review sources, convert material, ingest accepted knowledge, or reflect confirmed discussion insights. |
| Use Knowledge | Answer questions from the wiki, synthesize pages, or create deliverables under `artifacts/`. |
| Maintain Wiki | Check broken links, missing sources, stale claims, contradictions, duplicate pages, and log gaps. |

The agent should choose the shortest workflow that fully satisfies the current request.

## Package Contents

```text
.
├── README.md
├── README.zh-CN.md
├── AGENTS.md
├── WIKI.md
├── LICENSE
├── pyproject.toml
├── scripts/
│   ├── init.ps1
│   └── init.sh
├── skills/
└── docs/
    ├── usage.md
    ├── usage.zh-CN.md
    ├── references.md
    ├── references.zh-CN.md
    ├── acknowledgements.md
    └── acknowledgements.zh-CN.md
```

## Design Boundaries

- The workflow is text-first. Attachments, scans, screenshots, images, and audio may remain part of preserved original sources, but they are not first-class wiki content unless you explicitly add image or audio handling.
- Source review happens before wiki updates. A successful file conversion is not enough to accept a source.
- Original source files are preserved. Generated Markdown belongs under `intake/`, not `raw/`.
- User-facing reports, briefs, outlines, drafts, and templates belong under `artifacts/`, not `wiki/`.
- The package favors explicit traceability over hidden memory. Durable claims should cite source cards, intake output, raw files, or confirmed discussion records.

## Documentation

- [docs/usage.md](docs/usage.md): English usage guide.
- [AGENTS.md](AGENTS.md): Agent entrypoint and workflow routing.
- [WIKI.md](WIKI.md): Canonical agent operating guide.
- [docs/references.md](docs/references.md): English references.
- [docs/acknowledgements.md](docs/acknowledgements.md): English acknowledgements.

## References and Credits

This package builds on the LLM Wiki pattern and related public work. See [docs/references.md](docs/references.md) and [docs/acknowledgements.md](docs/acknowledgements.md).

## License

MIT License. See [LICENSE](LICENSE).

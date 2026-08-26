# Scenario Packages

Scenario packages adapt an initialized wiki to a specialized workspace without
changing the universal wiki contract. They do not activate during base
initialization, and directory presence alone is not activation.

## How to Initialize One

After normal package initialization, explicitly ask the agent to apply a named
scenario, for example:

```text
Initialize this workspace according to scenarios/exam-study/.
Read the scenario README first, then ask only for PROJECT.md fields needed by
the requested starter pages.
```

The agent then:

1. Reads `scenarios/<name>/README.md`.
2. Uses `PROJECT.template.md` only to confirm project-specific context.
3. Writes the exact name to the root `PROJECT.md` field `Active scenario`.
4. Uses `starter-pages.md` only to create the smallest useful initial pages.
5. Leaves `WIKI.md` and `AGENTS.md` unchanged and preserves the core source
   lifecycle.

The root `PROJECT.md` is the sole activation state. Initialization and upgrade
commands have no scenario parameter.

## Directory Contract

```text
scenarios/<name>/
├── README.md
├── PROJECT.template.md
├── starter-pages.md
└── skills/<name>/          optional durable scenario workflow
    ├── SKILL.md
    ├── references/         optional detailed contracts
    └── scripts/            optional deterministic helpers
```

A scenario-local skill stays in this directory. `AGENTS.md` may load it only
when the root `PROJECT.md` activates the exact scenario and the current request
is relevant. It is not copied into the universal `.agents/skills/` directory,
and inactive scenario skills are not read.

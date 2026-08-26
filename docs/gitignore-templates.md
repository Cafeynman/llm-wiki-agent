# Git Ignore Templates

The repository default protects local workspace data. Refer to the versioned
wiki template only when this checkout is the user's own wiki project and the
user intends to commit wiki content.

In both templates, keep `.env`, `.venv/`, caches, and local tool state such as
`.claude/`, `.claudian/`, `.codex/`, and `.obsidian/` ignored. Only replace the
`# Local wiki runtime content.` block in `.gitignore`.
Init and upgrade scripts preserve an existing `.gitignore` domain policy and
append only missing secret and technical-cache baseline lines. They do not infer
or append a wiki runtime policy to an existing file. When `.gitignore` is
missing, they seed the default private template without consulting target Git
state. Choose and save the versioned template before initialization when that is
the intended target-owned policy.

## Private Local Runtime

This is the package default. It keeps source files, extracted material, wiki
pages, questions, logs, reviews, and artifacts local.

```gitignore
# Required local baseline.
.env
**/.env
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/
tmp/
.claude/
.claudian/
.codex/
.obsidian/

# Local wiki runtime content.
/inbox/*
!/inbox/.gitkeep
/raw/
/intake/
/reviews/
/logs/
/questions/
/artifacts/
/wiki/
```

## Versioned Wiki Project

Use this when the repository is a personal or team wiki project and durable
wiki content should be tracked. This template still keeps the transient inbox,
preserved original files, and temporary extraction output local by default.

```gitignore
# Required local baseline.
.env
**/.env
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/
tmp/
.claude/
.claudian/
.codex/
.obsidian/

# Local source intake and temporary extraction state.
/inbox/*
!/inbox/.gitkeep
/raw/
/intake/tmp/
```

This version tracks `intake/processed/`, `intake/logs/`, `reviews/`, `logs/`,
`questions/`, `artifacts/`, and `wiki/`. If original source files under `raw/`
also need to be versioned, remove `/raw/` only after reviewing privacy, size,
copyright, and licensing constraints. Use `/intake/` in place of `/intake/tmp/`
when all intake output should remain local. Init and upgrade preserve either
target-owned form and add only missing secret and technical-cache baseline
rules.

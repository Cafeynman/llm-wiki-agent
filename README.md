<h1 align="center"><b>LLM Wiki Agent</b></h1>

<h2 align="center"><b>Build and maintain a persistent, traceable Obsidian-style Markdown knowledge base with an LLM agent.</b></h2>

<p align="center">
  <b><i><font size="4">Just drop your files in the inbox, and let your agent build the wiki.</font></i></b>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="https://docs.astral.sh/uv/"><img src="https://img.shields.io/badge/Package_Manager-uv-blue?logo=python&logoColor=white" alt="uv Package Manager"></a>
  <a href="https://obsidian.md/"><img src="https://img.shields.io/badge/Optimized_for-Obsidian-483699?logo=obsidian&logoColor=white" alt="Optimized for Obsidian"></a>
  <a href="#%EF%B8%8F-key-features--design-boundaries"><img src="https://img.shields.io/badge/⚠️_Rules-Text_First-orange" alt="Text-First Boundaries"></a>
</p>

<p align="center">
  <a href="README.zh-CN.md">🇨🇳 中文</a> ·
  <a href="README.md">🇬🇧 English</a>
</p>

<p align="center">
  <a href="docs/usage.md">📖 Usage Guide</a> · <a href="AGENTS.md">🤖 Agent Rules</a> · <a href="WIKI.md">🧠 Wiki Rules</a> · <a href="PROJECT.md">⚙️ Project Context</a>
</p>

---

## ⚡ Quick Start: Zero to Wiki

Clone or download this repository, then initialize the environment:

```bash
cd llm-wiki-agent

# Windows
.\scripts\init.ps1 -VaultRoot .

# macOS / Linux
./scripts/init.sh -VaultRoot .
```

*Note: For a separate Obsidian vault, pass the vault path like `.\scripts\init.ps1 -VaultRoot "C:\path\to\your\vault"`.*

Default source extraction preferences are recorded in `PROJECT.md`. On the first source intake, the agent confirms any preference that matters for the task.
For package upgrades, use the manifest-driven scripts documented in [Usage Guide](docs/usage.md#upgrade-package-files).

**Your Minimal First Run:**
1. Drop a source file in `inbox/example.md`.
2. Ask your agent: *"Process the files in inbox/ according to AGENTS.md, PROJECT.md, and WIKI.md."*
3. Watch the agent process your file into the `wiki/` directory!

---

## 🤔 What Is This?

**You drop the files. The agent organizes the knowledge. You get a traceable wiki.**

This repository is **not** a full application server or a replacement for Obsidian. It is a **portable workflow package** for agents that can read repository instructions (like Codex, Claude Code, Gemini CLI, OpenCode, etc.). 

The package gives your agent a strict, clear operating contract: 
<table>
<tr><td>📥</td><td><code>inbox/</code></td><td>Where source files enter</td></tr>
<tr><td>🗄️</td><td><code>raw/</code></td><td>Where original files are preserved</td></tr>
<tr><td>⚙️</td><td><code>intake/</code></td><td>Where reviewable Markdown is produced</td></tr>
<tr><td>🧠</td><td><code>wiki/</code></td><td>Where durable knowledge is written</td></tr>
<tr><td>📦</td><td><code>artifacts/</code></td><td>Where user-facing deliverables are saved</td></tr>
</table>

---

## 🔬 Core Workflows

The package keeps the agent strictly on three major workflows. The agent will always choose the shortest workflow that satisfies your request:

| Workflow | When to Use | What it Does |
|-----------|-------------|--------------|
| **➕ Add Knowledge** | Add files, review sources, convert material. | Promotes files from `inbox/` ➡️ `intake/` ➡️ `wiki/`, and reflects on confirmed discussion insights. |
| **💡 Use Knowledge** | Answer questions, synthesize pages, create deliverables. | Searches the wiki to create reports, briefs, drafts, or comparison tables under `artifacts/`. |
| **🧹 Maintain Wiki** | Check health, broken links, stale claims. | Finds contradictions, detects duplicates, logs gaps, and ensures traceability. |

---

## ✨ Key Features & Design Boundaries

| Feature | Description |
|---------|------------|
| **📜 Text-First Workflow** | Extraction results in Markdown. Attachments/images stay in `raw/` as preserved sources. |
| **🔍 Source Review Gate** | A successful extraction isn't enough. The agent reviews sources before accepting them into the wiki. |
| **🔗 Explicit Traceability** | The package favors explicit links over hidden memory. Claims cite source cards, raw files, or discussion records. |
| **📂 Original Preservation** | Original files are preserved. Generated Markdown lands in `intake/`, never mixing with `raw/`. |
| **⚙️ Replaceable Context** | `PROJECT.md` holds your specific preferences. `WIKI.md` and `AGENTS.md` remain stable workflow rules. |
| **🛡️ Safe Artifacts** | User-facing reports, briefs, outlines, and drafts go to `artifacts/`, keeping the `wiki/` clean. |

---

## 🛠️ Recommended Setup

To get the most out of LLM Wiki Agent, we recommend pairing it with:
- **[Claudian](https://github.com/YishenTu/claudian)**: Recommended if you want an Obsidian-oriented local agent environment.
- **[Obsidian Web Clipper](https://github.com/obsidianmd/obsidian-clipper)**: Recommended for seamlessly collecting web pages into Markdown source material.

---

## 🧩 Package Contents

<details>
<summary>Click to view full directory structure</summary>

```text
.
├── README.md
├── README.zh-CN.md
├── AGENTS.md
├── PROJECT.md
├── WIKI.md
├── LICENSE
├── pyproject.toml
├── scripts/
│   ├── init.ps1
│   ├── init.sh
│   ├── upgrade-manifest.txt
│   ├── upgrade.ps1
│   └── upgrade.sh
├── .agents/
│   └── skills/
└── docs/
    ├── usage.md
    ├── usage.zh-CN.md
    ├── references.md
    ├── references.zh-CN.md
    ├── acknowledgements.md
    └── acknowledgements.zh-CN.md
```

</details>

---

## 🙏 Acknowledgements & References

This package builds on the LLM Wiki pattern and related public work. See [References](docs/references.md) and [Acknowledgements](docs/acknowledgements.md) for details.

---

## 📄 License

MIT License. See [LICENSE](LICENSE).

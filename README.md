<h1 align="center"><b>LLM Wiki Agent</b></h1>

<h2 align="center"><b>Build and maintain a persistent, traceable Markdown knowledge base with an LLM agent.</b></h2>

<p align="center">
  <b><i><font size="4">Just drop your files in the inbox, and let your agent build the wiki.</font></i></b>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12"></a>
  <a href="https://docs.astral.sh/uv/"><img src="https://img.shields.io/badge/Package_Manager-uv-blue?logo=python&logoColor=white" alt="uv Package Manager"></a>
  <a href="https://obsidian.md/"><img src="https://img.shields.io/badge/Obsidian-Compatible-483699?logo=obsidian&logoColor=white" alt="Obsidian Compatible"></a>
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

*Note: For a separate working directory, including an existing Obsidian vault, pass that path like `.\scripts\init.ps1 -VaultRoot "C:\path\to\your\workspace"`. The target becomes the working root and receives the package-managed agent files, local skills, scripts, docs, and runtime structure. Initialization skips identical managed files and stops before writing when a differing existing file has no clean Git baseline. Workspace-specific preferences belong in `PROJECT.md`.*

Every conversation in the initialized workspace begins with the agent reading that workspace's complete `WIKI.md` and `PROJECT.md`. Programming, debugging, questions, technical work, and file operations all use this same automatic start; resumed conversations read them again, and conversation history is not a substitute.

Default source extraction preferences are recorded in `PROJECT.md`. The agent confirms only the provider choices needed by the current source task. When MinerU API mode is selected, this may include its profile, local credential setup, and whether MinerU should be preferred when available.
For service-backed providers and OCR backends, copy `.env.example` to `.env` in the initialized working root and fill only the variables required by the selected provider profile. The real `.env` file is ignored by Git; agents should load it with `uv run --env-file .env` when running provider commands.
For package upgrades, use the manifest-driven scripts documented in [Usage Guide](docs/usage.md#upgrade-package-files).
The default `.gitignore` keeps local wiki runtime content private; refer to [Git Ignore Templates](docs/gitignore-templates.md) when this checkout is a versioned wiki project.

Optional scenario packages under `scenarios/` can adapt an initialized workspace for specialized uses such as exam study; see [Optional Scenario Packages](docs/usage.md#optional-scenario-packages).

**Your Minimal First Run:**
1. Drop source files into `inbox/`, or give the agent a live URL as source material.
2. Ask your agent: *"Process these sources according to AGENTS.md, PROJECT.md, and WIKI.md."*
3. The agent materializes any URL through Defuddle, reviews the sources, and updates the wiki only after acceptance.

---

## 🤔 What Is This?

**You provide files or links. The agent organizes the knowledge. You get a traceable wiki.**

This repository is **not** a full application server or tied to a specific agent platform. It is a **portable workflow package** for any agent that can read repository instructions, edit files, and run the required commands. Obsidian and Claudian are optional interfaces, not runtime requirements.

The package gives your agent a strict, clear operating contract: 
<table>
<tr><td>📥</td><td><code>inbox/</code></td><td>Where submitted files and generated URL source captures enter</td></tr>
<tr><td>🗄️</td><td><code>raw/</code></td><td>Where lifecycle source artifacts are preserved</td></tr>
<tr><td>⚙️</td><td><code>intake/</code></td><td>Where reviewable Markdown is produced</td></tr>
<tr><td>📝</td><td><code>reviews/</code></td><td>Where review decisions and reflections are recorded</td></tr>
<tr><td>⏱️</td><td><code>logs/</code></td><td>Where wiki operation history is tracked</td></tr>
<tr><td>❓</td><td><code>questions/</code></td><td>Where unresolved investigation threads live</td></tr>
<tr><td>🧠</td><td><code>wiki/</code></td><td>Where durable knowledge is written</td></tr>
<tr><td>📦</td><td><code>artifacts/</code></td><td>Where user-facing deliverables are saved</td></tr>
</table>

---

## 🔬 Core Workflows

The package keeps the agent strictly on three major workflows. The agent will always choose the shortest workflow that satisfies your request:

| Workflow | When to Use | What it Does |
|-----------|-------------|--------------|
| **➕ Add Knowledge** | Add files or URLs, review sources, convert material. | Promotes source artifacts from `inbox/` ➡️ `intake/` ➡️ `wiki/`, and reflects on confirmed discussion insights. |
| **💡 Use Knowledge** | Answer questions, synthesize pages, create deliverables. | Searches the wiki to create reports, briefs, drafts, or comparison tables under `artifacts/`. |
| **🧹 Maintain Wiki** | Check health, broken links, stale claims. | Finds contradictions, detects duplicates, logs gaps, and ensures traceability. |

---

## ✨ Key Features & Design Boundaries

| Feature | Description |
|---------|------------|
| **📜 Text-First Workflow** | Extraction results in Markdown. Provider-returned attachments may be preserved beside `source.md`, but are not interpreted automatically. |
| **🔍 Source Review Gate** | A successful extraction isn't enough. The agent reviews sources before accepting them into the wiki. |
| **🔗 Explicit Traceability** | The package favors explicit links over hidden memory. Claims cite source cards, raw files, or discussion records. |
| **📂 Source Preservation** | Submitted files are preserved. A Defuddle capture is the lifecycle original for a live URL; other generated Markdown remains in `intake/`. |
| **⚙️ Replaceable Context** | `PROJECT.md` holds your specific preferences. `WIKI.md` and `AGENTS.md` remain stable workflow rules. |
| **🛡️ Safe Artifacts** | User-facing reports, briefs, outlines, and drafts go to `artifacts/`, keeping the `wiki/` clean. |

---

## 🛠️ Optional Interfaces

LLM Wiki Agent works directly from the filesystem without Obsidian or Claudian. If you prefer an Obsidian interface:

- **Claudian** embeds supported agent runtimes in an Obsidian vault. Follow the current installation guidance in the [YishenTu/claudian repository](https://github.com/YishenTu/claudian) or on the [Claudian website](https://claudian.xyz/zh/), then consult the [provider documentation](https://claudian.xyz/zh/docs/providers/). See the [Usage Guide](docs/usage.md#optional-obsidian-and-claudian-interface) for this package's setup recommendation.
- **[Obsidian Web Clipper](https://github.com/obsidianmd/obsidian-clipper)** can collect web pages as Markdown source material.

---

## 🧩 Package And Runtime Structure

<details>
<summary>Click to view package-managed files and initialized runtime directories</summary>

```text
.
├── README.md
├── README.zh-CN.md
├── AGENTS.md
├── PROJECT.md
├── WIKI.md
├── LICENSE
├── pyproject.toml
├── .env.example
├── scripts/
│   ├── init.ps1
│   ├── init.sh
│   ├── package-files.txt
│   ├── upgrade-manifest.txt
│   ├── upgrade.ps1
│   └── upgrade.sh
├── scenarios/
│   ├── README.md
│   └── exam-study/
├── .agents/
│   └── skills/
└── docs/
    ├── usage.md
    ├── usage.zh-CN.md
    ├── gitignore-templates.md
    ├── gitignore-templates.zh-CN.md
    ├── source-lifecycle.md
    ├── source-lifecycle.zh-CN.md
    ├── wiki-page-templates.md
    ├── wiki-page-templates.zh-CN.md
    ├── references.md
    ├── references.zh-CN.md
    ├── acknowledgements.md
    └── acknowledgements.zh-CN.md
```

After initialization, the working root also contains local runtime directories
created by the init or upgrade scripts. These directories hold workspace data
and are ignored by Git by default. To track durable wiki content in Git, refer to
[Git Ignore Templates](docs/gitignore-templates.md).

```text
.
├── inbox/             Submitted-file and live-URL capture entry point
├── raw/               Preserved lifecycle source artifacts by review state
├── intake/            Temporary and accepted Markdown extraction output
├── reviews/           Source review and reflection records
├── logs/              Wiki operation history
├── questions/         Open questions and investigation trails
├── artifacts/         User-facing deliverables
└── wiki/              Durable knowledge pages
```

</details>

---

## 🙏 Acknowledgements & References

This package builds on the LLM Wiki pattern and related public work. See [References](docs/references.md) and [Acknowledgements](docs/acknowledgements.md) for details.

---

## 📄 License

MIT License. See [LICENSE](LICENSE).

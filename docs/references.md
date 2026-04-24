# References

[中文版](references.zh-CN.md)

This project is based on the public LLM Wiki pattern and related community implementations. The references below are idea sources and prior art, not bundled source material.

## Core Idea Sources

1. Andrej Karpathy, [LLM Wiki idea file](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
2. Antigravity, [Karpathy's LLM Wiki: The Complete Guide to His Idea File](https://antigravity.codes/blog/karpathy-llm-wiki-idea-file), published 2026-04-04.
3. Tahir Balarabe, [What is LLM Wiki Pattern? Persistent Knowledge with LLM Wikis](https://medium.com/@tahirbalarabe2/what-is-llm-wiki-pattern-persistent-knowledge-with-llm-wikis-3227f561abc1), published 2026-04-08.
4. rohitg00, [LLM Wiki v2: extending Karpathy's LLM Wiki pattern with lessons from building agentmemory](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2).

## Related Implementations

1. Pratiyush, [llm-wiki](https://github.com/Pratiyush/llm-wiki).
2. SamurAIGPT, [llm-wiki-agent](https://github.com/SamurAIGPT/llm-wiki-agent/tree/main).

## Ideas Carried Forward

The references above shaped these design choices:

- A persistent Markdown wiki should accumulate knowledge instead of repeatedly retrieving and discarding context.
- Original source material should remain traceable.
- Wiki pages should be maintained incrementally by an agent.
- Cross-links, summaries, contradictions, and open questions are part of the knowledge base, not afterthoughts.
- Obsidian is a practical human-facing interface for reading and navigating the resulting Markdown graph.

## Project-Specific Improvements

This package turns the pattern into a stricter operating contract:

- `inbox/` is the only entry point for user-submitted original files.
- `raw/` is a state area with `digested`, `needs-review`, `ignored`, and `unsupported` outcomes.
- Source review happens after conversion and before wiki updates.
- Accepted sources get content-rich source cards under `wiki/sources/`.
- Discussion-derived knowledge is recorded separately from source-derived knowledge.
- The workflow is text-first, so images, scans, screenshots, and audio remain preserved source material unless image or audio handling is explicitly added.
- Agent behavior is reduced to three workflows: Add Knowledge, Use Knowledge, and Maintain Wiki.

These choices are intended to make the package easier to run, easier to audit, and safer to share as a public starter repository.

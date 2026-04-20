# 引用

本项目基于公开的 LLM Wiki pattern 及相关社区实现整理而成。以下内容是思想来源和先行实践，不是本仓库打包的源文件。

## 核心思想来源

1. Andrej Karpathy，[LLM Wiki idea file](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)。
2. Antigravity，[Karpathy's LLM Wiki: The Complete Guide to His Idea File](https://antigravity.codes/blog/karpathy-llm-wiki-idea-file)，发表于 2026-04-04。
3. Tahir Balarabe，[What is LLM Wiki Pattern? Persistent Knowledge with LLM Wikis](https://medium.com/@tahirbalarabe2/what-is-llm-wiki-pattern-persistent-knowledge-with-llm-wikis-3227f561abc1)，发表于 2026-04-08。
4. rohitg00，[LLM Wiki v2: extending Karpathy's LLM Wiki pattern with lessons from building agentmemory](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2)。

## 相关实现

1. Pratiyush，[llm-wiki](https://github.com/Pratiyush/llm-wiki)。
2. SamurAIGPT，[llm-wiki-agent](https://github.com/SamurAIGPT/llm-wiki-agent/tree/main)。

## 继承的思想

这些来源影响了本项目的核心设计：

- 持久 Markdown wiki 应积累知识，而不是反复检索再丢弃上下文。
- 原始 source 应保持可追溯。
- wiki 页面应由 agent 持续增量维护。
- 交叉链接、摘要、矛盾和开放问题都是知识库的一部分。
- Obsidian 是阅读和浏览 Markdown 知识图谱的实用界面。

## 本项目的改进

本包把这些思想收束为更明确的操作契约：

- `inbox/` 是用户投递原始文件的唯一入口。
- `raw/` 是状态区，包含 `digested`、`needs-review`、`ignored`、`unsupported` 四种结果。
- source review 发生在转换之后、wiki 更新之前。
- 被接受的 source 会在 `wiki/sources/` 下生成内容充实的 source card。
- discussion-derived knowledge 与 source-derived knowledge 分开记录。
- 工作流是 text-first，图片、扫描件、截图和音频默认只作为保留的原始 source，除非明确添加处理能力。
- agent 行为被收束为三种工作流：Add Knowledge、Use Knowledge、Maintain Wiki。

这些选择的目标是让这个包更容易运行、更容易审计，也更适合作为公开 starter repository 分享。

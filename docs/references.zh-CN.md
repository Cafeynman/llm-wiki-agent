<h1 align="center"><b>📚 参考资料</b></h1>

<p align="center">
  <b><i><font size="4">LLM Wiki 模式的先驱探索与基础理念。</font></i></b>
</p>

<p align="center">
  <a href="references.zh-CN.md">🇨🇳 中文</a> ·
  <a href="references.md">🇬🇧 English</a>
</p>

<p align="center">
  <a href="../README.zh-CN.md">🏠 返回首页</a>
</p>

---

本项目基于开源的 LLM Wiki 模式及其社区实现。以下参考资料为我们的设计提供了核心灵感，并非项目自带的源代码。

## 💡 核心理念来源

| 参考来源 | 链接 |
|-----------|------|
| **Andrej Karpathy** | [LLM Wiki idea file](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) |
| **Antigravity** | [Karpathy's LLM Wiki: The Complete Guide to His Idea File](https://antigravity.codes/blog/karpathy-llm-wiki-idea-file) (发布于 2026-04-04) |
| **Tahir Balarabe** | [What is LLM Wiki Pattern? Persistent Knowledge with LLM Wikis](https://medium.com/@tahirbalarabe2/what-is-llm-wiki-pattern-persistent-knowledge-with-llm-wikis-3227f561abc1) (发布于 2026-04-08) |
| **rohitg00** | [LLM Wiki v2: extending Karpathy's LLM Wiki pattern with lessons from building agentmemory](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2) |

---

## 🛠️ 相关实现

| 项目 | 仓库地址 |
|---------|------------|
| **Pratiyush** | [llm-wiki](https://github.com/Pratiyush/llm-wiki) |
| **SamurAIGPT** | [llm-wiki-agent](https://github.com/SamurAIGPT/llm-wiki-agent/tree/main) |

---

## 🧩 继承的核心思想

上述参考资料塑造了以下关键的设计选择：

- 一个持久化的 Markdown wiki 应该持续积累知识，而不是反复执行检索后又将上下文丢弃。
- 原始源材料应该保持可溯源状态。
- Wiki 页面应当由智能体以增量方式维护。
- 交叉链接、总结归纳、矛盾点以及未决问题是知识库的一部分，而非事后补救。
- Obsidian 是一个非常实用、面向人类的界面，非常适合阅读和导航生成的 Markdown 图谱。

---

## ✨ 项目特有的改进

此项目将理论模式转化为了一份更加严格、生产可用的操作契约：

- `inbox/` 是用户提交原始文件的**唯一入口**。
- `raw/` 设立了严格的状态分区，分为 `digested`, `needs-review`, `ignored`, 和 `unsupported`。
- 来源审查门被设置在格式转换**之后**、wiki 更新**之前**。
- 被接受的来源会在 `wiki/sources/` 目录下生成内容丰富的来源卡片。
- 基于讨论得出的知识会与基于来源材料得出的知识分开独立记录。
- 工作流采用**文本优先 (text-first)**。这意味着图片、扫描件、截图和音频仅作为原始材料保存，除非主动开启相应的处理能力。
- 智能体的行为被限定在三个核心工作流内：**添加知识 (Add Knowledge)**、**使用知识 (Use Knowledge)** 和 **维护 Wiki (Maintain Wiki)**。

这些选择使这个工具包更易于运行、更便于审计，作为公开模板项目分享也更加安全。

# Git Ignore 模板

仓库默认配置用于保护本地工作区数据。只有当这个 checkout 本身就是用户自己的
wiki 项目，并且用户明确希望提交 wiki 内容时，才参考“可版本化 wiki 项目”模板。

两个模板都应继续忽略 `.env`, `.venv/`, 缓存，以及 `.claude/`, `.claudian/`,
`.codex/` 等本地工具状态。只替换 `.gitignore` 中的 `# Local wiki runtime content.`
这一段。
初始化和升级脚本会在 `.gitignore` 缺失时写入默认模板。如果已有 `.gitignore`
没有 wiki 运行目录策略，它们会追加默认私有运行目录段落，不会覆盖文件中已有内容。

## 私有本地运行模式

这是包默认配置。它会让源文件、提取材料、wiki 页面、问题记录、日志、审查记录和
交付物都保留在本地。

```gitignore
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

## 可版本化 Wiki 项目

当仓库是个人或团队 wiki 项目，并且持久化 wiki 内容需要进入 Git 时，使用这个模板。
它仍然默认保留临时 inbox、原始来源文件和临时提取输出为本地内容。

```gitignore
# Local source intake and temporary extraction state.
/inbox/*
!/inbox/.gitkeep
/raw/
/intake/tmp/
```

这个版本会跟踪 `intake/processed/`, `intake/logs/`, `reviews/`, `logs/`,
`questions/`, `artifacts/` 和 `wiki/`。如果 `raw/` 下的原始来源文件也需要进入
版本库，请只在检查隐私、文件大小、版权和许可约束后移除 `/raw/`。初始化和升级
脚本仍会把已移除 `/raw/` 的配置识别为可版本化 wiki 策略。若所有 intake 输出都应
保留在本地，也会识别用 `/intake/` 替代 `/intake/tmp/` 的配置。

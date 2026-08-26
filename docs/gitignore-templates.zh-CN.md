# Git Ignore 模板

仓库默认配置用于保护本地工作区数据。只有当这个 checkout 本身就是用户自己的
wiki 项目，并且用户明确希望提交 wiki 内容时，才参考“可版本化 wiki 项目”模板。

两个模板都应继续忽略 `.env`, `.venv/`, 缓存，以及 `.claude/`, `.claudian/`,
`.codex/`, `.obsidian/` 等本地工具状态。只替换 `.gitignore` 中的 `# Local wiki runtime content.`
这一段。
初始化和升级脚本会保留已有 `.gitignore` 的领域策略，只补齐缺失的密钥和技术缓存
基线规则，不会推断或追加 wiki 运行目录策略。若 `.gitignore` 缺失，脚本直接写入
默认私有模板，不读取目标 Git 状态。若目标需要可版本化策略，应在初始化前创建并
保存相应的目标自有 `.gitignore`。

## 私有本地运行模式

这是包默认配置。它会让源文件、提取材料、wiki 页面、问题记录、日志、审查记录和
交付物都保留在本地。

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

## 可版本化 Wiki 项目

当仓库是个人或团队 wiki 项目，并且持久化 wiki 内容需要进入 Git 时，使用这个模板。
它仍然默认保留临时 inbox、原始来源文件和临时提取输出为本地内容。

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

这个版本会跟踪 `intake/processed/`, `intake/logs/`, `reviews/`, `logs/`,
`questions/`, `artifacts/` 和 `wiki/`。如果 `raw/` 下的原始来源文件也需要进入
版本库，请只在检查隐私、文件大小、版权和许可约束后移除 `/raw/`。若所有 intake
输出都应保留在本地，可用 `/intake/` 替代 `/intake/tmp/`。初始化和升级会保留这类
目标自有配置，只补齐缺失的密钥和技术缓存基线规则。

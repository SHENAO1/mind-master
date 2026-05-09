# 02 · 代码与协作约定

<!-- 静态文档。团队约定变更时更新。 -->

## 代码风格
- Python 脚本使用类型标注、`pathlib.Path`、`argparse` 和小函数分解。
- 文件读写显式使用 UTF-8；需要在 Windows 控制台输出符号时保留 `sys.stdout.reconfigure(encoding="utf-8")` 保护。
- CLI 输出必须列出具体交付物路径，阶段性命令以 `GATE` checkpoint 结束。
- 复杂逻辑可以加短注释；不要为显而易见的赋值写空泛注释。

## 命名约定
- 脚本文件使用 snake_case，如 `project_manager.py`、`doc_to_md.py`。
- CLI 子命令使用 kebab-case，如 `import-sources`。
- 项目目录默认为 `projects/<project_name>/`，产物文件名优先与项目名一致。
- 图片 ID 使用 `fig_<anchor>_<index>`，公式 ID 使用 `eq_<anchor>_<index>`。

## 目录约定
- Skill 入口和角色规范只放在 `skills/mind-master/` 下。
- 可重复执行的流水线步骤放在 `skills/mind-master/scripts/` 下。
- 源文档导入后进入 `projects/<project_name>/sources/`；生成资产进入 `assets/`；中间文件进入 `intermediate/`；最终导出进入 `exports/`。
- `projects/*` 默认不提交，除非明确需要提交样例项目时再调整忽略规则。
- 新测试应放在未来的 `tests/` 目录；测试样例要避免提交用户私有文档。

## 提交与分支
- 当前主分支为 `master`，远端为 `origin git@github.com:SHENAO1/mind-master.git`。
- 提交消息使用简短英文 conventional 风格，例如 `chore: initialize ai handoff context`。
- 提交前检查 `git status --short`，只暂存本任务相关文件。
- 不自动推送远端，除非用户明确要求。

## 测试策略
- 当前最低验证为 `python -m compileall skills\mind-master\scripts`。
- 每新增一个流水线脚本，应至少提供 CLI 参数校验、缺文件错误路径和成功输出路径的测试。
- DOCX/OMML 相关能力需要小型合成样例，覆盖标题、列表、表格、图片、行内公式和块级公式。
- 渲染和导出脚本补齐后，需要用 Playwright 截图或导出物存在性检查验证 HTML、SVG、PNG、PDF。

## AI 助手协作约定
- 进入会话先读 `.ai-context/05-current-state.md` 和 `.ai-context/06-session-log.md` 最上面一条。
- 结束会话更新 `.ai-context/05-current-state.md`，并在 `.ai-context/06-session-log.md` 顶部追加新条目。
- 架构、依赖、技术选型写入 `.ai-context/04-decisions.md`，带日期与理由。
- 新增依赖前先检查 `01-architecture.md` 和 `requirements.txt` 是否已有同类项。
- 遇到阻塞写进 `07-known-issues.md`，不要悄悄绕过。
- 不确定的事实必须从仓库文件或命令输出查证后再写进代码或回复。

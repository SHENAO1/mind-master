# 05 · 当前状态

<!-- 动态文档。每次会话结束前都要更新。保持短小。 -->

**最近更新**: 2026-05-09

> Mind-Master 已完成第一批骨架和部分核心脚本；当前重点是把八步流水线缺失脚本补齐，并添加可复现测试样例。

## ✅ Done
- 仓库基础文件已建立：`README.md`、`README_CN.md`、`.env.example`、`.gitignore`、`requirements.txt`。
- Skill 入口已建立：`skills/mind-master/SKILL.md`，包含触发词、八步流水线、GATE 规则、路径契约和命令样例。
- Reference 规范已建立：shared standards、strategist、executor base/classic/logic/org、mindmap formats、math rendering、image policy。
- 项目管理脚本已实现：`project_manager.py` 支持 `init`、`import-sources`、`validate`。
- 章节拆分脚本已实现：`split_sections.py` 可按 H1 将 `intermediate/source.md` 拆成 `intermediate/sections/<section_id>.md`，并创建 `maps/<section_id>/` 导图子工作区。
- DOCX 转 Markdown 脚本已实现初版：`doc_to_md.py` 支持标题、列表、表格、图片抽取、OMML 公式转换和资产报告。
- OMML 到 LaTeX 转换脚本已实现：`omml_to_latex.py` 支持常见分式、根式、上下标、n-ary、矩阵、重音等结构。
- 已用 `ai-handoff-init` 初始化跨助手上下文：`.ai-context/`、`AGENTS.md`、`CLAUDE.md`、`.github/copilot-instructions.md`。

## 🚧 In Progress
- 已为真实课程笔记 DOCX 创建脱敏测试项目 `projects/ml_theory2_test/`；脱敏后的源文件为 `sources/ml_theory2_notes.docx`，可作为后续导图生成测试基线。
- 该测试项目已按 H1 拆分为 4 个章节导图单元：`lesson_05`、`lesson_06`、`lesson_07`、`lesson_08`。生成文件在 `projects/ml_theory2_test/intermediate/sections/` 和 `projects/ml_theory2_test/maps/`，当前按项目规则被 git 忽略。
- 已生成第 5、6 节导图：`projects/ml_theory2_test/maps/lesson_05/` 与 `projects/ml_theory2_test/maps/lesson_06/` 下包含 `outline.json`、`mindmap.json`、`mindmap.md`、`validation.json`、`self_check.md` 和 HTML/SVG/PNG/PDF 导出。

## ⏭️ Next
- 复核第 5、6 节 HTML 的浏览器 KaTeX 渲染效果；当前 PNG/PDF 由 SVG 渲染链路生成，未用 Playwright 做 DOM 级公式检查。
- 继续用同一方式生成 `lesson_07`、`lesson_08`；每节课输出到 `projects/ml_theory2_test/maps/<section_id>/exports/`。
- 公式初筛发现 14 条可能需要清洗，主要是希腊字母/算子 Unicode 和公式编号 `#` 的组合。
- 查看 sample v2 产物：`projects/sample/intermediate/outline.json`、`mindmap.json`、`mindmap_v2.md`、`v2_self_check.md`、`validation.json`，以及 `projects/sample/exports/sample.html/svg/png/pdf`。
- 每个文档应继续使用独立 `projects/<project_name>/`，不要把导图结果写到仓库根目录；当前 `projects/*` 默认被 git 忽略。
- 若要做真实 v1/v2 差异复盘，需提供或恢复 v1 的 `mindmap.json`、HTML/PNG/PDF 与验证报告。
- 补齐 `source_to_md/pdf_to_md.py` 和 `source_to_md/web_to_md.py`，让 Step 1 覆盖 README 中承诺的 PDF/Web 输入。
- 实现 `extract_assets.py`，生成 `assets/images/index.json`，并接入可选 OCR 信息。
- 实现 `templates/markmap.html`、`render_mindmap.py`、`batch_validate.py`、`export_mindmap.py`，闭环 Step 6 到 Step 8。
- 增加最小测试样例和测试命令，覆盖项目初始化、DOCX 转换、OMML 转换和后续导出链路。
- 更新 README 当前阶段，避免继续声称“scripts and references are added in later gated steps”。

## ⚠️ Blocked
- PDF 支持依赖系统 `poppler`；导出和截图依赖 Playwright Chromium，开发机需要单独安装。
- OCR 能力依赖可选 `tesseract`，当前没有脚本消费该配置。
- 缺少公开样例文档，无法验证 DOCX 图片/公式抽取在真实复杂文档上的表现。

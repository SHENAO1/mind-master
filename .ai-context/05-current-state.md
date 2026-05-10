# 05 · 当前状态

<!-- 动态文档。每次会话结束前都要更新。保持短小。 -->

**最近更新**: 2026-05-10

> Mind-Master 已完成正式渲染/验证/导出闭环，并新增密集导图自适应双侧布局；当前重点是把 source-faithful outline 生成继续产品化，并扩展第 6-8 节回归。

## ✅ Done
- 仓库基础文件已建立：`README.md`、`README_CN.md`、`.env.example`、`.gitignore`、`requirements.txt`。
- Skill 入口已建立：`skills/mind-master/SKILL.md`，包含触发词、八步流水线、GATE 规则、路径契约和命令样例。
- Reference 规范已建立：shared standards、strategist、executor base/classic/logic/org、mindmap formats、math rendering、image policy。
- 项目管理脚本已实现：`project_manager.py` 支持 `init`、`import-sources`、`validate`。
- 章节拆分脚本已实现：`split_sections.py` 可按 H1 将 `intermediate/source.md` 拆成 `intermediate/sections/<section_id>.md`，并创建 `maps/<section_id>/` 导图子工作区。
- DOCX 转 Markdown 脚本已实现初版：`doc_to_md.py` 支持标题、列表、表格、图片抽取、OMML 公式转换和资产报告。
- OMML 到 LaTeX 转换脚本已实现：`omml_to_latex.py` 支持常见分式、根式、上下标、n-ary、矩阵、重音等结构。
- 已用 `ai-handoff-init` 初始化跨助手上下文：`.ai-context/`、`AGENTS.md`、`CLAUDE.md`、`.github/copilot-instructions.md`。
- 已根据第 5 节导图失败案例迭代 `skills/mind-master/references/`：补充层级保真、去冗余、source_quote、table 节点、数学包裹、图片重绘优先和布局权重规则。
- 已用新 reference 规则重生成第 5 节测试导图：`projects/ml_theory2_test/maps/lesson_05_regen/`，包含 outline/mindmap/validation/self_check 和 HTML/SVG/PNG/PDF 导出。
- 已实现正式 Markmap 闭环脚本：`render_mindmap.py`、`batch_validate.py`、`export_mindmap.py` 与 `templates/markmap.html`；Step 6-8 不再依赖手写固定坐标海报。
- 已实现 `layout_profile` 自适应布局：密度画像、双侧分支权重分配、双栏语义 HTML、导出适配、`layout_self_check.md` 与布局/保真校验。

## 🚧 In Progress
- 已为真实课程笔记 DOCX 创建脱敏测试项目 `projects/ml_theory2_test/`；脱敏后的源文件为 `sources/ml_theory2_notes.docx`，可作为后续导图生成测试基线。
- 该测试项目已按 H1 拆分为 4 个章节导图单元：`lesson_05`、`lesson_06`、`lesson_07`、`lesson_08`。生成文件在 `projects/ml_theory2_test/intermediate/sections/` 和 `projects/ml_theory2_test/maps/`，当前按项目规则被 git 忽略。
- 已生成第 5、6 节导图：`projects/ml_theory2_test/maps/lesson_05/` 与 `projects/ml_theory2_test/maps/lesson_06/` 下包含 `outline.json`、`mindmap.json`、`mindmap.md`、`validation.json`、`self_check.md` 和 HTML/SVG/PNG/PDF 导出。
- `lesson_05_regen` 是新规则验证版：一级分支严格保留 Batch / Momentum / 本节小结；表 5-1 保留为 table 节点；课程截图不嵌入，改用 SVG 概念重绘。
- 已用正式链路重跑 `lesson_05` 并触发 `balanced_two_sided`：Batch 在左侧，Momentum 与本节小结在右侧；H2/H3 覆盖 9/9，表 5-1 保留，公式 5-1 通过 KaTeX，7 张源图均有 `figure_decisions`，HTML/SVG/PNG/PDF 已导出。
- 2026-05-10 再次重生成 `lesson_05`，重新导出 HTML/SVG/PNG/PDF 并通过 `batch_validate.py`；本地预览可用 `projects/ml_theory2_test/maps/lesson_05/exports/lesson_05.html`。
- 2026-05-10 根据用户反馈将双侧布局继续优化为横向中心放射式：根节点居中，分支枢纽与子卡片围绕分布，新增 root-to-branch / branch-to-child 连接曲线；`lesson_05` 导出视口为 2200x1120，校验记录 `connectorCount=12`。
- 2026-05-10 修复 PDF 跨页和连接线错位：连接线改为浏览器按真实 DOM 位置动态计算，PDF 改为由高分辨率 PNG 生成单页；`lesson_05` 最新导出 `pdf_mode=single_page_png_pdf`，PNG 4400x2412，`connectorCount=11`。

## ⏭️ Next
- 下一轮应继续把 `lesson_05` 的 source-faithful outline 生成方式产品化，减少手工写 outline 的比例。
- 继续复核第 6 节并用新的 `layout_profile` 链路重生成，确认多公式、多图场景下校验仍可靠。
- 继续用同一方式生成 `lesson_07`、`lesson_08`；每节课输出到 `projects/ml_theory2_test/maps/<section_id>/exports/`。
- 公式初筛发现 14 条可能需要清洗，主要是希腊字母/算子 Unicode 和公式编号 `#` 的组合。
- 查看 sample v2 产物：`projects/sample/intermediate/outline.json`、`mindmap.json`、`mindmap_v2.md`、`v2_self_check.md`、`validation.json`，以及 `projects/sample/exports/sample.html/svg/png/pdf`。
- 每个文档应继续使用独立 `projects/<project_name>/`，不要把导图结果写到仓库根目录；当前 `projects/*` 默认被 git 忽略。
- 若要做真实 v1/v2 差异复盘，需提供或恢复 v1 的 `mindmap.json`、HTML/PNG/PDF 与验证报告。
- 补齐 `source_to_md/pdf_to_md.py` 和 `source_to_md/web_to_md.py`，让 Step 1 覆盖 README 中承诺的 PDF/Web 输入。
- 实现 `extract_assets.py`，生成 `assets/images/index.json`，并接入可选 OCR 信息。
- 增加最小测试样例和测试命令，覆盖项目初始化、DOCX 转换、OMML 转换和后续导出链路。
- 更新 README 当前阶段，避免继续声称“scripts and references are added in later gated steps”。

## ⚠️ Blocked
- PDF 支持依赖系统 `poppler`；导出和截图依赖 Playwright Chromium，开发机需要单独安装。
- OCR 能力依赖可选 `tesseract`，当前没有脚本消费该配置。
- 缺少公开样例文档，无法验证 DOCX 图片/公式抽取在真实复杂文档上的表现。

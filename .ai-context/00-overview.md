# 00 · 项目概览

<!-- 静态文档。范围或目标发生重大变更时才修订。 -->

## 项目名称
mind-master

## 一句话描述
Local-first Word/PDF to Markmap mind map workflow with LaTeX math and selected images/screenshots.

## 项目目标
- 把本地 Word/PDF 源文档转换为结构化 Markdown，并保留标题、列表、表格、图片和公式证据。
- 通过 `skills/mind-master` 提供可被 AI 助手调用的思维导图流水线入口、角色规范和脚本化步骤。
- 输出可交互的 Markmap HTML，并计划支持 SVG、PNG、PDF 导出。
- 保持公式为可编辑 LaTeX 文本，由浏览器中的 KaTeX 渲染，不把公式栅格化为图片。
- 以本地优先为默认安全边界，源文件、资产、中间产物和导出物都留在用户磁盘。

## 范围边界

### 本项目做什么(In scope)
- 提供 Mind-Master skill 入口和按阶段加载的 reference 规范。
- 管理 `projects/<project_name>/` 下的 sources、assets、intermediate、exports 项目结构。
- 支持 DOCX 到 Markdown 的初步转换，含图片抽取、表格转换和 OMML 到 LaTeX 转换。
- 通过 manifest 记录导图风格、画布、字体、节点限制、图片嵌入方式和导出参数。
- 规划 PDF/Web 转换、资产抽取、截图、渲染、验证和导出脚本，使八步流水线闭环。

### 本项目不做什么(Out of scope)
- 不提供托管 SaaS、账号体系、云端文档上传或远程存储。
- 不默认调用外部模型、OCR 或图片服务；这些能力只能在脚本明确实现并由用户配置后使用。
- 不在未确认的情况下打开外部 URL 截图。
- 不把 OCR 结果当作正文重写来源；OCR 只用于图片相关性判断。
- 不把用户生成项目产物纳入默认版本控制，`projects/*` 默认忽略。

## 成功标准
- [ ] DOCX 样例可生成 `intermediate/source.md`、`source_assets.json`、图片和公式缓存。
- [ ] `project_manager.py init/import-sources/validate` 可创建、导入并校验项目目录。
- [ ] PDF/Web 转 Markdown、资产抽取、截图、渲染、验证、导出脚本补齐后，八步流水线每步都打印 GATE checkpoint。
- [ ] 生成的 HTML 可用 Markmap 展示层级结构，公式由 KaTeX 成功渲染，引用图片路径有效且有 alt 文本。
- [ ] SVG、PNG、PDF 导出物可从同一 HTML 生成，并在 Windows PowerShell 环境中可复现。

## 相关资源
- 本仓库 `README.md` 与 `README_CN.md`
- `skills/mind-master/SKILL.md`
- `skills/mind-master/references/*.md`
- `https://github.com/markmap/markmap`
- `https://katex.org/`
- `https://python-docx.readthedocs.io/`
- `https://github.com/mwilliamson/python-mammoth`

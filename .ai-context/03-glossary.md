# 03 · 术语表

<!-- 随项目推进增补。每条一行,定义精炼。 -->

## 通用
- GATE: 每个流水线步骤结束时打印的检查点，必须列出交付物路径，并等待用户确认后进入下一步。
- Manifest: `projects/<project_name>/manifest.json`，记录项目名、风格、画布、设计参数、来源文件和流水线元数据。
- Source Markdown: `intermediate/source.md`，从 DOCX/PDF/Web 源文档转换出的结构化 Markdown。
- Asset Index: `assets/images/index.json`，记录图片、截图、alt 文本、来源锚点和可选 OCR 信息的索引文件。
- Local-first: 默认所有源文件、资产、中间文件和导出物都留在本机，不上传云端。

## 项目特有术语
- Mind-Master: 本仓库提供的本地文档转思维导图工作流和同名 skill。
- Strategist: Step 4 规划角色，读取 source markdown 与候选图片，输出 `outline.json`。
- Executor: Step 6 渲染角色，读取 outline、manifest 和 assets，输出 `mindmap.json` 与 HTML。
- Markmap: 将 Markdown/层级数据渲染为交互式思维导图的前端技术。
- KaTeX: 浏览器内公式渲染库，用于把 LaTeX 文本渲染为可读公式。
- OMML: Microsoft Office Math Markup Language，Word 文档内公式的 XML 表示。
- `classic`: 经典放射式思维导图风格。
- `logic`: 逻辑树或鱼骨式推理导图风格。
- `org`: 组织结构或层级树风格。
- Image/Screenshot Gate: 打开外部 URL 截图前必须列出目标 URL 并等待用户确认的安全门。

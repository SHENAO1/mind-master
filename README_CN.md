# Mind-Master

Mind-Master 是一个本地运行、IDE 内对话驱动的文档转思维导图工程。它接收 Word 或 PDF 文档，输出支持 LaTeX 公式渲染、按需嵌入关键图片或截图的高质量思维导图。

本项目对齐 `ppt-master` 的工程范式：以 Skill 作为总入口，`references/` 存放角色规范，`scripts/` 承接可重复执行的流水线步骤，所有阶段串行推进并通过 `GATE` checkpoint 交接。不做托管 SaaS，不默认上传任何源文件。

## 输出物

- Markmap 交互式单文件 HTML
- KaTeX 渲染的 LaTeX 公式
- 来自原始文档的内嵌图片
- 经用户确认后由 Playwright 本地截取的网页或 PDF 局部截图
- 从 HTML 导出的 SVG、PNG、PDF

## 仓库结构

```text
mind-master/
├── README.md
├── README_CN.md
├── requirements.txt
├── .env.example
├── skills/
│   └── mind-master/
│       ├── SKILL.md
│       ├── references/
│       │   ├── shared-standards.md
│       │   ├── strategist.md
│       │   ├── executor-base.md
│       │   ├── executor-classic.md
│       │   ├── executor-logic.md
│       │   ├── executor-org.md
│       │   ├── mindmap-formats.md
│       │   ├── math-rendering.md
│       │   └── image-policy.md
│       └── scripts/
│           ├── project_manager.py
│           ├── source_to_md/
│           │   ├── doc_to_md.py
│           │   ├── pdf_to_md.py
│           │   └── web_to_md.py
│           ├── extract_assets.py
│           ├── omml_to_latex.py
│           ├── screenshot_capture.py
│           ├── render_mindmap.py
│           ├── export_mindmap.py
│           └── batch_validate.py
├── templates/
│   └── markmap.html
└── projects/
    └── <project_name>/
        ├── sources/
        ├── assets/
        │   ├── images/
        │   └── equations/
        ├── intermediate/
        │   ├── source.md
        │   ├── outline.json
        │   └── mindmap.json
        └── exports/
```

## 八步流水线

```text
DOCX/PDF
  -> [1. 转 Markdown]
  -> [2. 建项目]
  -> [3. 抽资产]
  -> [4. Strategist 结构规划]
  -> [5. Image/Screenshot 决策]
  -> [6. Executor 渲染]
  -> [7. 公式与图片融合校验]
  -> [8. 导出]
```

## 最高优先级工程纪律

1. 串行流水线：每一步输出都是下一步输入，不并行跳步。
2. GATE checkpoint：每步结束前打印 `✅` checkpoint，列出交付物路径，确认后继续。
3. `--move` 而非 copy：用户原始文件导入 `sources/` 后，原位置不再保留。
4. 批量预读：Executor 第一次生成前一次性读完相关 `references/` 文件，过程中不反复重读。
5. 设计参数确认：第一张图生成前确认画布尺寸、配色、字体、最大层级数、节点最大字数。
6. 外部 URL 截图门禁：截图前必须列出目标 URL 并等待用户确认；本地 PDF 截图可直接执行。

## 安装

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

Windows PowerShell 可使用：

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
```

系统依赖：

- `poppler`：`pdf2image` 渲染 PDF 页面需要。
- `tesseract`：可选，用于图片 OCR，帮助 Strategist 判断图片是否值得纳入导图。

如需要模型、OCR 或图片服务配置，可复制 `.env.example` 为 `.env`。默认本地流程不要求上传文档。

## 当前阶段

当前仓库按第一阶段交付顺序搭建。第 1 项先落地目录骨架、README、依赖清单和环境变量模板；后续每项通过 GATE checkpoint 单独确认。

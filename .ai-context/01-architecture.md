# 01 · 架构与技术栈

<!-- 静态文档。重大重构时更新。 -->

## 技术栈
- Python
- python-docx
- mammoth
- lxml
- Pillow
- pdf2image
- pytesseract
- playwright
- markdown-it-py
- beautifulsoup4
- rich
- Markmap
- KaTeX

## 模块划分

| 模块 | 职责 | 关键入口文件 |
| --- | --- | --- |
| 根目录文档 | 描述项目目标、安装方式、流水线和当前阶段 | `README.md`, `README_CN.md`, `.env.example`, `requirements.txt` |
| Skill 入口 | 为 AI 助手提供触发词、八步流水线、GATE 规则、路径契约和命令约定 | `skills/mind-master/SKILL.md` |
| Reference 规范 | 存放 Strategist、Executor、格式、公式、图片、共享标准等角色和产物规范 | `skills/mind-master/references/*.md` |
| 项目管理脚本 | 初始化项目目录、移动源文件、生成/校验 manifest | `skills/mind-master/scripts/project_manager.py` |
| DOCX 转换脚本 | 将 Word 文档转换为 Markdown，抽取图片，转换 OMML 公式，写入资产报告 | `skills/mind-master/scripts/source_to_md/doc_to_md.py` |
| 公式转换脚本 | 将 OMML XML 片段转换为 KaTeX 友好的 LaTeX 字符串 | `skills/mind-master/scripts/omml_to_latex.py` |
| 模板与项目输出 | 计划存放 Markmap HTML 模板；用户产物在 `projects/<name>/` 下生成 | `templates/`, `projects/` |

## 数据流

```text
DOCX/PDF source
  -> Step 1: source_to_md/*
  -> projects/<name>/intermediate/source.md
  -> Step 2: project_manager init/import-sources
  -> projects/<name>/manifest.json
  -> Step 3: extract_assets.py
  -> projects/<name>/assets/images/index.json
  -> Step 4: Strategist outline
  -> projects/<name>/intermediate/outline.json
  -> Step 5: image/screenshot decision
  -> updated assets/images/index.json
  -> Step 6: render_mindmap.py
  -> exports/<name>.html + intermediate/mindmap.json
  -> Step 7: batch_validate.py
  -> intermediate/validation.json
  -> Step 8: export_mindmap.py
  -> exports/<name>.svg/.png/.pdf
```

当前实际实现到 Step 1 的 DOCX 转换能力和 Step 2 的项目管理能力；后续脚本仍需补齐。

## 依赖与外部服务
- Python 包依赖在 `requirements.txt`，当前以 Python 脚本和标准 CLI 为主。
- `poppler` 是 PDF 页面渲染所需的系统依赖，当前 README 已声明但 PDF 脚本尚未实现。
- `tesseract` 是可选 OCR 依赖，当前 README 已声明但资产评分/抽取脚本尚未实现。
- Playwright Chromium 计划用于截图和 HTML 导出，需执行 `python -m playwright install chromium`。
- 默认流程不要求云服务；`.env.example` 仅预留模型、OCR、图片服务和导出配置。

## 构建与运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium

python skills\mind-master\scripts\project_manager.py init demo --style classic
python skills\mind-master\scripts\project_manager.py validate projects\demo
python skills\mind-master\scripts\source_to_md\doc_to_md.py --source path\to\source.docx --project projects\demo
python -m compileall skills\mind-master\scripts
```

## 目录结构

```text
.
├── .ai-context/                 # 跨助手项目上下文
├── .github/
│   └── copilot-instructions.md  # Copilot 入口
├── projects/                    # 用户项目产物，默认忽略 projects/*
├── skills/
│   └── mind-master/
│       ├── SKILL.md
│       ├── references/
│       └── scripts/
├── templates/                   # 计划存放 markmap.html
├── AGENTS.md                    # Codex 入口
├── CLAUDE.md                    # Claude Code 入口
├── README.md
├── README_CN.md
└── requirements.txt
```

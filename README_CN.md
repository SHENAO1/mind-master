# Mind-Master

Mind-Master 是一个本地优先的文档转思维导图工作流。它把课程讲义、Word 笔记等长文档转换成可验证、可导出、保留公式与关键图片证据的学习型思维导图。

这个仓库当前重点不是做一个在线 SaaS，而是提供一套 Codex Skill + Python 脚本 + 浏览器导出链路。源文件、抽取图片、中间结构、验证报告和最终导出默认都留在本机 `projects/` 目录中。

## 当前能做什么

- 将 DOCX 转成结构化 Markdown，并抽取文档内图片。
- 将 Word OMML 公式尽量转换为可编辑 LaTeX。
- 按一级标题拆分章节，例如一份课程笔记拆成第 5、6、7、8 节。
- 为每节课生成独立导图工作区：`outline.json`、`mindmap.json`、`mindmap.md`、校验报告和导出文件。
- 渲染 compact learning poster 风格的 Markmap/HTML 思维导图。
- 通过 KaTeX 在浏览器中渲染公式，而不是把公式栅格化成图片。
- 对源图做五类决策：`preserve_full`、`preserve_crop`、`redraw_high_fidelity`、`redraw_concept`、`omit`。
- 把保留图片渲染成图证卡：包含图号、证据标题、裁剪图、来源短句和 callout。
- 使用浏览器实测校验版面、连接线、图证卡、公式、图片、章节覆盖和导出结果。
- 导出 HTML、SVG、PNG、单页 PDF。

## 适用场景

- 课程讲义转学习海报。
- Word 笔记转章节思维导图。
- 带数学公式的机器学习、深度学习、统计学材料整理。
- 需要源文档保真、可追溯引用、可复验导出的本地工作流。

不适合的场景：

- 需要多人在线协作编辑的云端白板。
- 只想快速画一个没有来源约束的装饰性脑图。
- 需要当前就完整支持 PDF/Web 输入的流水线。PDF/Web 入口仍在计划中。

## 快速开始

安装 Python 依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
```

macOS/Linux 可使用：

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

系统依赖：

- `poppler`：后续 PDF 页面渲染需要。
- `tesseract`：可选，后续 OCR 图片增强需要。

## 典型流程

创建项目：

```powershell
python skills/mind-master/scripts/project_manager.py init ml_notes --style classic
```

导入 DOCX。注意这里是移动文件，不是复制文件：

```powershell
python skills/mind-master/scripts/project_manager.py import-sources projects/ml_notes --move .\my_notes.docx
```

转换 DOCX：

```powershell
python skills/mind-master/scripts/source_to_md/doc_to_md.py --source projects/ml_notes/sources/my_notes.docx --project projects/ml_notes
```

抽取和分类图片资产：

```powershell
python skills/mind-master/scripts/extract_assets.py projects/ml_notes
```

按章节拆分：

```powershell
python skills/mind-master/scripts/split_sections.py projects/ml_notes
```

生成某一节课的导图前，需要先由 Codex 根据 `skills/mind-master/SKILL.md` 和 `references/` 编写该节的 `outline.json`。完成后渲染：

```powershell
python skills/mind-master/scripts/render_mindmap.py projects/ml_notes --section-id lesson_06 --style classic --image-mode relative
```

校验：

```powershell
python skills/mind-master/scripts/batch_validate.py projects/ml_notes --section-id lesson_06
python -m unittest discover -s skills/mind-master/tests -p "test_*.py"
```

导出：

```powershell
python skills/mind-master/scripts/export_mindmap.py projects/ml_notes --section-id lesson_06 --html projects/ml_notes/maps/lesson_06/exports/lesson_06.html --scale 2
```

最终输出位于：

```text
projects/ml_notes/maps/lesson_06/exports/
├── lesson_06.html
├── lesson_06.svg
├── lesson_06.png
└── lesson_06.pdf
```

## 工作区约定

每份文档或一组相关文档对应一个项目目录：

```text
projects/<project_name>/
├── manifest.json
├── sources/
├── assets/
│   ├── images/
│   └── equations/
├── intermediate/
│   ├── source.md
│   └── sections/
├── exports/
└── maps/
    └── <section_id>/
        ├── intermediate/
        │   ├── outline.json
        │   ├── mindmap.json
        │   └── validation.json
        └── exports/
            ├── <section_id>.html
            ├── <section_id>.svg
            ├── <section_id>.png
            └── <section_id>.pdf
```

`projects/*` 默认被 git 忽略，避免把用户原始文档、截图、抽取图片和导出文件误提交。

## Skill 结构

```text
skills/mind-master/
├── SKILL.md
├── references/
│   ├── shared-standards.md
│   ├── strategist.md
│   ├── executor-base.md
│   ├── executor-classic.md
│   ├── executor-logic.md
│   ├── executor-org.md
│   ├── mindmap-formats.md
│   ├── math-rendering.md
│   └── image-policy.md
├── scripts/
│   ├── project_manager.py
│   ├── source_to_md/
│   │   └── doc_to_md.py
│   ├── extract_assets.py
│   ├── omml_to_latex.py
│   ├── split_sections.py
│   ├── render_mindmap.py
│   ├── export_mindmap.py
│   └── batch_validate.py
├── templates/
│   └── markmap.html
├── assets/
│   └── svg_templates/
└── tests/
```

## 质量门禁

Mind-Master 不只生成图片，还会验证结果。当前校验重点包括：

- H2/H3 章节覆盖完整。
- 不凭空添加原文不存在的章节编号。
- 表格、公式、图片都有明确处置。
- LaTeX 公式通过 KaTeX 渲染，无 `.katex-error`。
- 保留或重绘图片必须有来源支撑的 callout。
- 裁剪图片必须有 crop metadata。
- 派生节点必须标记来源，不伪装成原文章节。
- 学习海报版面要通过空白率、比例、图证卡紧凑度、底部学习带和连接线语义检查。
- 导出 HTML/SVG/PNG/PDF 后再次复验。

## 当前状态

已经落地：

- Codex Skill 入口与完整 reference 规范。
- 项目初始化、DOCX 转 Markdown、OMML 转 LaTeX、图片资产抽取、章节拆分。
- Markmap/HTML 渲染、compact learning poster 布局、浏览器导出。
- 批量验证和 unittest 回归。
- 第 5、6 节机器学习课程笔记的本地测试产物。

仍待补齐：

- PDF 输入转换脚本。
- Web 输入转换脚本。
- 外部 URL 截图脚本的完整产品化。
- OCR 驱动的图片语义增强。
- 更多公开示例和端到端 fixtures。

## 隐私与安全

- 默认不上传源文件。
- 默认不提交 `projects/*`。
- 外部 URL 截图需要用户确认。
- 公式保留为可编辑文本。
- 原图只在有学习价值和来源支撑时进入导图。

## License

当前仓库尚未声明开源许可证。公开复用前请先补充明确的 LICENSE 文件。

---
name: mind-master
description: Local-first Word/PDF to Markmap mind map workflow with LaTeX math, image selection, screenshot capture, validation, and SVG/PNG/PDF export.
---

# Mind-Master Skill

Mind-Master turns a local Word or PDF document into a high-quality interactive mind map. It follows the `ppt-master` style: Skill entrypoint, durable reference specs, scripts for repeatable work, serial role handoff, and explicit GATE checkpoints.

The workflow is local-first. Do not upload source documents or generated assets by default.

## Trigger Keywords

Use this skill when the user asks for:

- 制作思维导图
- 生成思维导图
- mind map
- mind-master
- 思维导图

## Pipeline

```text
DOCX/PDF
  -> [1. Convert Source to Markdown]
  -> [2. Initialize Project]
  -> [3. Extract Assets]
  -> [4. Strategist Outline]
  -> [5. Image/Screenshot Decision]
  -> [6. Executor Render]
  -> [7. Formula and Image Validation]
  -> [8. Export]
```

## Highest-Priority Rules

1. Serial pipeline only. Each step consumes the previous step's output. Do not skip ahead.
2. GATE checkpoints are mandatory. At the end of each step, print a `✅` checkpoint with concrete delivered paths and wait for user confirmation before continuing.
3. Use `--move` for source import. After `project_manager.py import-sources`, the original source path should no longer retain the file.
4. Batch preread before Executor. Before the first Step 6 generation, read all relevant `references/` files in one pass and do not reread them during generation.
5. Confirm design parameters before the first rendered mind map: canvas size, palette, font stack, max depth, node word limits, image mode.
6. External screenshot safety gate. Before opening any external URL, list every target URL and wait for explicit user confirmation. Local PDF screenshots are allowed without that URL gate.
7. Keep equations editable. Equations must remain LaTeX text in HTML and render through KaTeX. Do not rasterize formulas into images.
8. OCR informs image relevance only. Do not rewrite node text from OCR.

## Required References

Read only what the current stage needs, except Step 6 where batch preread is required.

- `references/shared-standards.md`: global design and content limits
- `references/strategist.md`: Step 4 planning role
- `references/executor-base.md`: Step 6 common execution rules
- `references/executor-classic.md`: classic radial style
- `references/executor-logic.md`: logic tree or fishbone style
- `references/executor-org.md`: org or hierarchy style
- `references/mindmap-formats.md`: JSON, Markdown, HTML, SVG, PNG, PDF contracts
- `references/math-rendering.md`: OMML, LaTeX, MathML, KaTeX rules
- `references/image-policy.md`: image selection, screenshots, crop, alt, copyright, readability

## Project Path Contract

Default project root:

```text
projects/<project_name>/
```

Required project layout:

```text
projects/<project_name>/
├── manifest.json
├── sources/
├── assets/
│   ├── images/
│   │   └── index.json
│   └── equations/
├── intermediate/
│   ├── source.md
│   ├── outline.json
│   └── mindmap.json
└── exports/
    ├── <project_name>.html
    ├── <project_name>.svg
    ├── <project_name>.png
    └── <project_name>.pdf
```

## Style Selection Gate

Before Step 4, ensure the user has selected one style:

- `classic`: classic radial mind map
- `logic`: logic tree or fishbone-style reasoning map
- `org`: organization or hierarchy map

Default: `classic`.

If the project has not been initialized yet, ask before Step 2 because `manifest.json` records the style. If an existing project is already initialized, read `manifest.json`; if style is missing or inconsistent with the user request, stop and ask.

Required prompt:

```text
Style GATE: 请选择导图风格：classic / logic / org。默认 classic。确认后我会把选择写入 manifest.json，并在 Step 4 前使用同一风格规划 outline。
```

## Design Parameter Gate

Before the first Step 6 render, print:

- canvas size
- palette
- font stack
- max depth
- node word limits
- image embedding mode: `relative` or `base64`
- export scale

Required prompt:

```text
Design GATE: 我将使用以下设计参数生成第一版导图，请确认后继续：
- canvas: <width>x<height>
- palette: <name>
- fonts: <font stack>
- max_depth: <n>
- node_limits: 一级≤12字，二级≤18字，叶子≤30字
- image_mode: <relative|base64>
- export_scale: <n>
```

## Image Policy Gate

Before Step 5 opens external URLs, print every planned URL and wait for confirmation.

Required prompt:

```text
Image/Screenshot GATE: 我准备对以下外部 URL 截图。请确认后我才会打开这些 URL：
1. <url> - <reason>
```

If there are no external URL intents, say so and continue. Local PDF page rendering does not require this URL gate, but still record generated screenshots in `assets/images/index.json`.

## Step 1. Convert Source to Markdown

Role: source converter.

Inputs:

- source document: `<path/to/source.docx>` or `<path/to/source.pdf>`
- project path if already created: `projects/<project_name>/`

Command for DOCX:

```bash
python skills/mind-master/scripts/source_to_md/doc_to_md.py \
  --source <path/to/source.docx> \
  --project projects/<project_name>
```

Command for PDF:

```bash
python skills/mind-master/scripts/source_to_md/pdf_to_md.py \
  --source <path/to/source.pdf> \
  --project projects/<project_name>
```

Outputs:

- `projects/<project_name>/intermediate/source.md`
- extracted inline images under `projects/<project_name>/assets/images/`
- unresolved formulas as `[EQUATION_UNRESOLVED:<id>]`
- printed asset list

Checkpoint:

```text
GATE 1 ✅ Source converted to Markdown.
Deliverables:
- source markdown: projects/<project_name>/intermediate/source.md
- inline images: projects/<project_name>/assets/images/
- equation cache: projects/<project_name>/assets/equations/
Confirm to continue to Step 2.
```

Failure helper:

- `references/math-rendering.md#error-helper`
- `references/mindmap-formats.md#error-helper`

## Step 2. Initialize Project

Role: project manager.

Inputs:

- project name
- selected style: `classic`, `logic`, or `org`

Command:

```bash
python skills/mind-master/scripts/project_manager.py init <project_name> --style <classic|logic|org>
```

Optional source import:

```bash
python skills/mind-master/scripts/project_manager.py import-sources \
  projects/<project_name> \
  --move <path/to/source.docx>
```

Outputs:

- project directory skeleton
- `projects/<project_name>/manifest.json`
- source files moved into `projects/<project_name>/sources/`

Checkpoint:

```text
GATE 2 ✅ Project initialized.
Deliverables:
- manifest: projects/<project_name>/manifest.json
- sources: projects/<project_name>/sources/
- assets: projects/<project_name>/assets/
- intermediate: projects/<project_name>/intermediate/
- exports: projects/<project_name>/exports/
Confirm to continue to Step 3.
```

Failure helper:

- `references/mindmap-formats.md#error-helper`

## Step 3. Extract Assets

Role: asset extractor.

Inputs:

- `projects/<project_name>/sources/`
- `projects/<project_name>/intermediate/source.md`

Command:

```bash
python skills/mind-master/scripts/extract_assets.py projects/<project_name>
```

Outputs:

- `projects/<project_name>/assets/images/index.json`
- all extracted document images under `projects/<project_name>/assets/images/`
- optional `ocr_text` fields when OCR is available

Checkpoint:

```text
GATE 3 ✅ Assets extracted.
Deliverables:
- image index: projects/<project_name>/assets/images/index.json
- images: projects/<project_name>/assets/images/
Confirm to continue to Step 4.
```

Failure helper:

- `references/image-policy.md#error-helper`

## Step 4. Strategist Outline

Role: strategist.

Before starting:

1. Confirm style if not already confirmed.
2. Read `references/shared-standards.md`.
3. Read `references/strategist.md`.
4. Read `references/image-policy.md` only for candidate image semantics, not final image decisions.

Inputs:

- `projects/<project_name>/intermediate/source.md`
- `projects/<project_name>/assets/images/index.json`
- `projects/<project_name>/manifest.json`

Command pattern:

```bash
python skills/mind-master/scripts/project_manager.py validate projects/<project_name>
```

The actual outline authoring is done by the agent according to `references/strategist.md`.

Output:

- `projects/<project_name>/intermediate/outline.json`

Checkpoint:

```text
GATE 4 ✅ Strategist outline complete.
Deliverables:
- outline: projects/<project_name>/intermediate/outline.json
Confirm to continue to Step 5.
```

Failure helper:

- `references/strategist.md#error-helper`
- `references/shared-standards.md#error-helper`

## Step 5. Image/Screenshot Decision

Role: image curator and screenshot operator.

Before external URL screenshots:

1. Read all `screenshot_intents` from `outline.json`.
2. Print the Image/Screenshot GATE prompt with every external URL.
3. Wait for user confirmation before opening those URLs.

Inputs:

- `projects/<project_name>/intermediate/outline.json`
- `projects/<project_name>/assets/images/index.json`
- optional local PDF paths in `projects/<project_name>/sources/`

Command for URL or PDF screenshot after gate:

```bash
python skills/mind-master/scripts/screenshot_capture.py \
  --url <url|file://...pdf#page=3> \
  --selector "<css selector>" \
  --out projects/<project_name>/assets/images/screenshots/<shot_id>.png \
  --full-page false \
  --wait-for networkidle
```

Outputs:

- updated `projects/<project_name>/assets/images/index.json`
- selected image IDs recorded for Step 6
- screenshots under `projects/<project_name>/assets/images/screenshots/`

Checkpoint:

```text
GATE 5 ✅ Image and screenshot decisions complete.
Deliverables:
- updated image index: projects/<project_name>/assets/images/index.json
- screenshots: projects/<project_name>/assets/images/screenshots/
Confirm to continue to Step 6.
```

Failure helper:

- `references/image-policy.md#error-helper`

## Step 6. Executor Render

Role: executor.

Batch preread requirement:

Read these files once before generation:

- `references/shared-standards.md`
- `references/executor-base.md`
- `references/executor-<style>.md`
- `references/mindmap-formats.md`
- `references/math-rendering.md`
- `references/image-policy.md`

Do not reread them while generating the same version.

Inputs:

- `projects/<project_name>/intermediate/outline.json`
- `projects/<project_name>/assets/images/index.json`
- `projects/<project_name>/manifest.json`

Command:

```bash
python skills/mind-master/scripts/render_mindmap.py projects/<project_name> \
  --style <classic|logic|org> \
  --image-mode relative
```

Outputs:

- `projects/<project_name>/intermediate/mindmap.json`
- `projects/<project_name>/exports/<project_name>.html`

Checkpoint:

```text
GATE 6 ✅ Mind map rendered.
Deliverables:
- mindmap json: projects/<project_name>/intermediate/mindmap.json
- html: projects/<project_name>/exports/<project_name>.html
Confirm to continue to Step 7.
```

Failure helper:

- `references/executor-base.md#error-helper`
- `references/executor-<style>.md#error-helper`
- `references/math-rendering.md#error-helper`

## Step 7. Formula and Image Validation

Role: validator.

Inputs:

- `projects/<project_name>/exports/<project_name>.html`
- `projects/<project_name>/intermediate/mindmap.json`
- `projects/<project_name>/assets/images/index.json`

Command:

```bash
python skills/mind-master/scripts/batch_validate.py projects/<project_name>
```

Checks:

- no `.katex-error`
- every image has alt text
- every referenced image exists
- max depth is respected
- node word limits are respected

Checkpoint:

```text
GATE 7 ✅ Formula and image validation passed.
Deliverables:
- validated html: projects/<project_name>/exports/<project_name>.html
- validation report: projects/<project_name>/intermediate/validation.json
Confirm to continue to Step 8.
```

Failure helper:

- `references/math-rendering.md#error-helper`
- `references/image-policy.md#error-helper`
- `references/shared-standards.md#error-helper`

## Step 8. Export

Role: exporter.

Inputs:

- `projects/<project_name>/exports/<project_name>.html`

Command:

```bash
python skills/mind-master/scripts/export_mindmap.py projects/<project_name> \
  --html projects/<project_name>/exports/<project_name>.html \
  --scale 2
```

Outputs:

- `projects/<project_name>/exports/<project_name>.svg`
- `projects/<project_name>/exports/<project_name>.png`
- `projects/<project_name>/exports/<project_name>.pdf`

Checkpoint:

```text
GATE 8 ✅ Export complete.
Deliverables:
- html: projects/<project_name>/exports/<project_name>.html
- svg: projects/<project_name>/exports/<project_name>.svg
- png: projects/<project_name>/exports/<project_name>.png
- pdf: projects/<project_name>/exports/<project_name>.pdf
Workflow complete.
```

Failure helper:

- `references/mindmap-formats.md#error-helper`

## Agent Operating Notes

- Rebuild context from `docs/session_state.md` first if it exists, then `docs/progress.md`, then evidence summaries under `results/latest`.
- Check dirty files before editing.
- Prefer existing scripts over ad hoc shell fragments once scripts exist.
- Keep generated artifacts inside `projects/<project_name>/`.
- When a step is blocked, report the exact missing input and the helper section to inspect next.

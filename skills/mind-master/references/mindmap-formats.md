# Mindmap Format Reference

This file defines artifact formats for Mind-Master.

## Markdown Source

`intermediate/source.md` should preserve:

- heading hierarchy
- paragraphs
- lists
- tables as Markdown tables where practical
- image references with alt text
- equations as `$...$` or `$$...$$`
- unresolved equations as `[EQUATION_UNRESOLVED:<id>]`

## Outline JSON

`intermediate/outline.json` is the Strategist output. It contains semantic structure and candidates, not final render choices.

Required top-level fields:

- `root`
- `style`
- `max_depth`
- `nodes`

## Mindmap JSON

`intermediate/mindmap.json` is the Executor output. It is the final render tree.

Required top-level fields:

- `root`
- `style`
- `theme`
- `assets`

Each node may include:

- `id`
- `title`
- `summary`
- `equations`
- `images`
- `notes`
- `children`

## Markmap Markdown

Render target:

```markdown
# 中心主题
## 一级分支
- 凝练要点
- 公式：$E = mc^2$
- ![图示说明](assets/images/example.png)
```

Rules:

- Use heading levels for hierarchy.
- Use bullets for summaries, formulas, and images.
- Do not use raw HTML unless required for image sizing.
- Preserve LaTeX delimiters.

## HTML Output

`exports/<project_name>.html` must:

- include Markmap runtime or local-compatible CDN configuration;
- include KaTeX CSS and JS support;
- include custom CSS theme;
- load all images from relative paths or embedded base64;
- be openable by double-click where possible.

## Export Output

Step 8 writes:

- `exports/<project_name>.svg`
- `exports/<project_name>.png`
- `exports/<project_name>.pdf`

PNG default scale: `2`.

## Validation Report

`intermediate/validation.json` should include:

- `passed`
- `checks`
- `errors`
- `warnings`

## Error Helper

Common failures:

- JSON parse error: validate and repair exact file.
- broken path: resolve relative to project root.
- invalid image extension: convert or skip.
- missing export: rerun `export_mindmap.py` after confirming Playwright Chromium is installed.

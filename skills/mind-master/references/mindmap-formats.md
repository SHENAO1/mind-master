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

## Section Sources

When a single document contains several lesson, chapter, or module sections, split the source by the chosen heading level before outlining.

Default section mode uses H1 headings:

```text
intermediate/sections/
├── index.json
├── lesson_05.md
└── lesson_06.md
```

`intermediate/sections/index.json` contains:

- `source`: original Markdown source path
- `split_level`: heading level used as the map unit
- `section_count`
- `sections[]` with `id`, `title`, `source`, `map_dir`, `line_start`, and `line_end`

Rules:

- One section source produces one mind map.
- The section heading is the root node.
- The section's direct child headings become the first-level branches.
- Keep map-specific artifacts under `maps/<section_id>/`; do not mix multiple section maps in the project root.

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

In section map mode, write HTML to:

```text
maps/<section_id>/exports/<section_id>.html
```

Relative image paths should still resolve to the project-level `assets/images/` directory.

## Export Output

Step 8 writes:

- `exports/<project_name>.svg`
- `exports/<project_name>.png`
- `exports/<project_name>.pdf`

In section map mode, Step 8 writes:

- `maps/<section_id>/exports/<section_id>.svg`
- `maps/<section_id>/exports/<section_id>.png`
- `maps/<section_id>/exports/<section_id>.pdf`

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

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

Node fields:

- `id`: stable node ID
- `type`: optional node type. Defaults to `concept`; may be `concept`, `table`, `formula`, `image`, or `note`
- `title`: short visible label
- `description`: optional factual explanation grounded in source
- `summary`: optional independent synthesis from source, not a mandatory conclusion
- `source_quote`: required for leaf claims and evidence-bearing nodes
- `source_span`: optional source location object with `line_start` and `line_end`
- `equations`: editable LaTeX strings, without rasterization
- `image_candidates`: source image IDs or planned redraw IDs
- `children`: child nodes

Top-level Strategist fields:

- `coverage_report`: required for Word/PDF conversion quality checks
- `figure_decisions`: required when the active source contains images

## Coverage Report

The coverage report records where source content went. It prevents the map from looking clean while silently dropping Word content.

```json
{
  "coverage_report": {
    "source": "intermediate/sections/lesson_05.md",
    "sections": [
      {
        "source_heading": "5.1 Batch（批次）",
        "node_path": "root > Batch",
        "action": "node",
        "source_span": {"line_start": 7, "line_end": 81}
      }
    ],
    "tables": [
      {"source_label": "表5-1", "node_path": "root > Batch > 性能对比表", "action": "table"}
    ],
    "formulas": [
      {"source_label": "公式5-1", "node_path": "root > Momentum > 动量公式", "action": "formula"}
    ],
    "figures": [
      {"source_id": "fig_p23_002", "source_path": "assets/images/fig_p23_002.png", "node_path": "root > Batch > Batch 定义", "action": "image"}
    ],
    "omitted": [
      {"source": "fig_p12_001", "reason": "装饰性图片"}
    ]
  }
}
```

Actions are `node`, `table`, `formula`, `image`, `redraw`, or `omitted`.

## Figure Decisions

Every image in the active source must receive one explicit decision:

```json
{
  "figure_decisions": [
    {
      "source_id": "fig_p38_004",
      "source_path": "assets/images/fig_p38_004.png",
      "decision": "image",
      "node_id": "n_batch_speed",
      "node_path": "root > Batch > 效率机制",
      "alt": "不同 Batch Size 下单次更新时间与 Epoch 时间对比",
      "reason": "核心实验趋势图，文字无法完全替代"
    }
  ]
}
```

Allowed decisions:

- `image`: embed the source image near the relevant node
- `crop`: embed a readable crop of the source image
- `redraw`: recreate as SVG or simple diagram
- `omitted`: omit because it is decorative, duplicated, too blurry, or not useful

## Table Nodes

Use a `table` node when the source contains a meaningful comparison table or matrix. Do not split the table's rows and columns into unrelated sibling branches.

Required table node fields:

```json
{
  "id": "n_table_1",
  "type": "table",
  "title": "Batch 大小对比",
  "source_quote": "表5-1 Small Batch与Large Batch性能对比表",
  "table": {
    "columns": ["维度", "Small Batch", "Large Batch"],
    "rows": [
      ["Time for one epoch", "Slower", "Faster"],
      ["Gradient", "Noisy", "Stable"]
    ],
    "row_sources": [
      "Time for one epoch | Slower | Faster",
      "Gradient | Noisy | Stable"
    ]
  }
}
```

Rules:

- `columns` and `rows` are mandatory.
- `row_sources` is optional but recommended when rows are derived from prose or when row-level evidence is useful.
- Keep source row and column meanings intact.
- A table node may have a short `summary`, but the table remains the primary content.
- Table cells may contain LaTeX, but formulas must stay wrapped in `$...$` or `$$...$$`.

## Mindmap JSON

`intermediate/mindmap.json` is the Executor output. It is the final render tree.

Required top-level fields:

- `root`
- `style`
- `theme`
- `assets`
- `coverage_report`
- `figure_decisions`
- `markdown`
- `html`

Each node may include:

- `id`
- `type`
- `title`
- `description`
- `summary`
- `source_quote`
- `equations`
- `images`
- `notes`
- `table`
- `children`

## Markmap Markdown

`intermediate/mindmap.md` is the primary render source. It must preserve the final hierarchy and content that Markmap will render.

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
- Render table nodes as Markdown tables or as compact HTML tables only when Markdown cannot preserve layout. Do not decompose the table into separate branches.
- Course-note maps should look like expandable study notes: H2/H3 skeleton first, then concise leaves under the closest relevant heading.

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
- `deduplicated_nodes`: nodes merged or removed by the Strategist deduplication pass
- `hallucination_checks`: sampled node claims, their `source_quote`, and whether a matching source fragment was found
- `math_delimiter_checks`: failures where LaTeX-like strings appear outside math delimiters
- `table_checks`: table node presence, required fields, and row/column integrity
- `heading_coverage`: H2/H3 source headings mapped into the mind map
- `image_decisions`: source images and their keep/crop/redraw/omit decisions
- `browser`: Playwright-rendered HTML checks, including KaTeX errors and SVG presence

## Error Helper

Common failures:

- JSON parse error: validate and repair exact file.
- broken path: resolve relative to project root.
- invalid image extension: convert or skip.
- missing export: rerun `export_mindmap.py` after confirming Playwright Chromium is installed.

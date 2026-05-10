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
- `type`: optional node type. Defaults to `concept`; may be `concept`, `table`, `formula`, `image`, `note`, `keywords`, or `tips`
- `section_id`: required on H2/H3 heading nodes when the source has visible numbering, such as `5.1` or `5.1.1`
- `icon`: optional line icon key for learning-poster rendering, such as `database`, `file-text`, `gauge`, `line-chart`, `scale`, `running`, `lightbulb`, `settings`, `list-checks`, `key`, or `wrench`
- `title`: short visible label
- `description`: optional factual explanation grounded in source
- `summary`: optional independent synthesis from source, not a mandatory conclusion
- `source_quote`: required for leaf claims and evidence-bearing nodes
- `source_span`: optional source location object with `line_start` and `line_end`
- `equations`: editable LaTeX strings, without rasterization
- `image_candidates`: source image IDs or planned redraw IDs
- `derived`: true only for non-source-heading derived nodes
- `grounded_hint`: true for inferred but source-grounded learning hints
- `derived_from` / `derived_from_summary`: source node IDs or summary node IDs that ground a derived node
- `children`: child nodes

Top-level Strategist fields:

- `coverage_report`: required for Word/PDF conversion quality checks
- `figure_decisions`: required when the active source contains images
- `layout_profile`: optional Strategist hint and required Executor output. If missing, `render_mindmap.py` must generate it from the final tree.

## Layout Profile

`layout_profile` records the density decision used by the renderer. It is a layout contract, not a license to simplify source content.

```json
{
  "layout_profile": {
    "mode": "vertical | balanced_two_sided | compact_radial",
    "visual_profile": "compact_learning_poster",
    "density_score": 0,
    "reason": "",
    "branch_weights": [
      {
        "node_id": "n_batch",
        "weight": 18,
        "side": "left"
      }
    ]
  }
}
```

Rules:

- Legal `mode` values are `vertical`, `balanced_two_sided`, and `compact_radial`.
- `density_score` is the weighted subtree score used to choose the layout.
- `branch_weights` must include every first-level branch under the root.
- `side` is `center` for `vertical` / `compact_radial`, and `left` or `right` for `balanced_two_sided`.
- Layout changes must not remove or merge H2/H3 sections, tables, formulas, or figure decisions.
- `visual_profile: "compact_learning_poster"` means the same source-faithful tree is rendered as a finished learning poster: stronger center card, closer branches, evidence cards, a bottom learning band, and low-noise connectors.
- Compact learning posters must measure the final `.balanced-layout` content bbox and report poster-packing metrics: `content_bbox_ratio`, `top_blank_ratio`, `center_void_ratio`, `edge_blank_ratio`, and `poster_aspect_ratio`.
- Under `balanced_two_sided`, all H3 and lower content under the same H2 stays on the same side as that H2.
- H2 headings remain first-level branches and H3 headings remain second-level nodes. `balanced_two_sided` may move an entire H2 branch left/right, but must not promote H3 nodes to first-level cards.

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
      {"source_id": "fig_p23_002", "source_path": "assets/images/fig_p23_002.png", "node_path": "root > Batch > Batch 定义", "action": "omit"}
    ],
    "omitted": [
      {"source": "fig_p12_001", "reason": "装饰性图片"}
    ]
  }
}
```

Actions are `node`, `table`, `formula`, `preserve_full`, `preserve_crop`, `redraw_high_fidelity`, `redraw_concept`, or `omit`.

## Figure Decisions

Every image in the active source must receive one explicit decision:

```json
{
  "figure_decisions": [
    {
      "source_id": "fig_p38_004",
      "source_path": "assets/images/fig_p38_004.png",
      "decision": "preserve_full",
      "node_id": "n_batch_speed",
      "node_path": "root > Batch > 效率机制",
      "evidence_title": "证明：大 Batch 在一个 Epoch 上更省时",
      "source_figure_label": "图5-3",
      "alt": "不同 Batch Size 下单次更新时间与 Epoch 时间对比",
      "reason": "核心实验趋势图，文字无法完全替代",
      "callouts": [
        {
          "text": "大 Batch 在单个 Epoch 上更快",
          "source_quote": "在一个 Epoch 中，较大的 Batch Size 反而能缩短训练时间"
        }
      ],
      "readability_tier": "dense"
    }
  ]
}
```

Allowed decisions:

- `preserve_full`: embed the full source image near the relevant node when the whole image is clear source-backed evidence
- `preserve_crop`: crop a source figure to its evidence-bearing region, save the derivative locally, and embed the crop while preserving provenance
- `redraw_high_fidelity`: recreate the source structure, key arrows, formulas, labels, and relative relationships when the original is unreadable at map size
- `redraw_concept`: recreate only the learning concept through a registered SVG template when exact source geometry is not required
- `omit`: omit because the figure is decorative, duplicated, too blurry, not useful, or lacks a registered redraw template

Screenshot-like assets are not eligible for direct embed:

- If `assets/images/index.json` says `type` is `screenshot`, `slide`, or `photo`, the effective decision must be `preserve_crop`, `redraw_high_fidelity`, `redraw_concept`, or `omit` unless the asset is explicitly marked as a real data chart.
- `preserve_full` may embed only assets explicitly marked `type: "data_chart"`, `is_data_chart: true`, `redraw_required: false`, or other non-screenshot visual evidence approved by the Strategist.
- A `preserve_crop` decision must preserve `source_id`, `source_path`, `alt`, `crop_box`, `crop_source_id`, `crop_path`, and `crop_focus` or `crop_reason`; coverage action should be `preserve_crop`.
- A `redraw_high_fidelity` or `redraw_concept` decision must preserve `source_id`, `source_path`, `alt`, `redraw_template_id`, and `redraw_instruction`; coverage action should match the final decision.
- Every retained or redrawn figure must include 1 to 2 callouts. Each callout has short `text` plus a `source_quote` that appears in the active source.
- Every retained or redrawn figure in learning-poster layouts must include `evidence_title` and `source_figure_label`, and render as an evidence card: title, image/redraw, 1-2 source-backed callouts, and figure provenance.
- Evidence cards should use a compact teaching-callout structure: media and source-backed conclusion chips appear as one group, and multi-figure evidence nodes may use side-by-side cards when this lowers branch height without hurting readability.
- Retained figures must include a readability tier or explicit `min_render_width` / `min_render_height` so validation can prove the final PNG/PDF is readable.
- Missing redraw templates must downgrade to `omit` before rendering and validation must record the absence.

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

## Keywords Nodes

Use a `keywords` node when the source contains repeated terms, bold terms, or Chinese-English paired terminology.

```json
{
  "id": "n_keywords",
  "type": "keywords",
  "title": "[*] 关键词",
  "terms": ["Batch Size", "Epoch", "Shuffle", "Noisy Gradient"],
  "derived": true,
  "derived_from": ["source_terms"]
}
```

Rules:

- Use 8 to 12 terms when the source supports that many.
- Terms must come from the active source, not general domain knowledge.
- Keywords render as a horizontal bottom capsule strip in GPT Image 2 inspired layouts.
- In compact learning posters, keywords join tuning hints and Momentum advantages in a single bottom learning band. They must not appear as separate fake source sections.
- Keywords are derived nodes, not source chapters; keep the `[*]` prefix and do not assign source-style section numbers.
- Keywords must carry `derived: true` and `derived_from`.

## Tips Nodes

Use a `tips` node only when the source explicitly contains practice advice, tuning guidance, cautions, or tips.

Rules:

- Do not generate a tips/takeaway node when the source has no such paragraph.
- Tips nodes must include `source_quote` and complete-sentence details.
- Added tips nodes that are not original headings must use a title prefixed with `[*]`.
- Derived tuning hints must mark each item with `derived_from_summary` or `grounded_hint`; they must never be numbered as `5.4`, `5.5`, etc.
- Derived tuning or advantage nodes must set `derived: true` or `grounded_hint: true`, include `derived_from` or `derived_from_summary`, and keep a non-numbered title such as `[*] 调参启示（派生）`.

## Mindmap JSON

`intermediate/mindmap.json` is the Executor output. It is the final render tree.

Required top-level fields:

- `root`
- `style`
- `theme`
- `assets`
- `coverage_report`
- `figure_decisions`
- `layout_profile`
- `markdown`
- `html`

Each node may include:

- `id`
- `type`
- `section_id`
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
- `section_numbering`: H2/H3 nodes preserve visible source numbers and parent/child placement
- `image_decisions`: source images and their `preserve_full` / `preserve_crop` / `redraw_high_fidelity` / `redraw_concept` / `omit` decisions
- `layout_profile_checks`: legal layout mode, density score, and first-level branch coverage
- `layout_readability`: export aspect ratio and balanced side-weight checks
- `source_fidelity`: H2/H3, table, formula, and figure coverage after layout switching
- `forbidden_section_numbers`: rendered source-style section IDs must be drawn only from active source headings
- `figure_decision_values`: all source figures use only `preserve_full`, `preserve_crop`, `redraw_high_fidelity`, `redraw_concept`, or `omit`; crop files exist
- `crop_metadata`: every `preserve_crop` decision has `crop_box`, `crop_path`, and `crop_focus` or `crop_reason`
- `image_callout_grounding`: every retained or redrawn figure has 1 to 2 callouts backed by source quotes
- `image_readability`: retained or redrawn images meet their required final render width and height
- `derived_node_labeling`: derived nodes have `derived=true` or `grounded_hint=true`, include `derived_from`, and do not use source-style section numbers
- `text_compression`: compressed visible titles do not truncate English words and auto density nodes stay within the owning `source_span`
- `layout_aesthetics`: compact poster ratio, blank rate, center-card position, branch distance, and bottom-band height checks
- `evidence_card_quality`: every retained/redrawn figure has `evidence_title`, source figure label, source-backed callouts, and readable rendered area
- `bottom_learning_band`: keywords, tuning hints, and derived advantages are grouped in one bottom band without fake section numbers
- `connector_noise`: connector count, stroke width, opacity, and center-card crossing checks
- `poster_packing`: `content_bbox_ratio`, `top_blank_ratio`, `center_void_ratio`, `edge_blank_ratio`, and `poster_aspect_ratio`
- `batch_height_compactness`: `left_branch_height_ratio`, `table_compactness`, and `evidence_grid_compactness`
- `evidence_compactness`: `evidence_title_visible`, `evidence_callout_visible`, `evidence_media_area_ratio`, and `evidence_card_not_too_tall`
- `learning_band_compactness`: `learning_band_column_count`, `learning_band_keyword_limit`, and `learning_band_height_ratio`
- `tips_grounding`: tips/takeaway nodes require explicit source evidence and must not appear when unsupported
- `summary_sentence_checks`: summary/takeaway details remain complete sentences and do not collapse into short noun phrases
- `browser`: Playwright-rendered HTML checks, including KaTeX errors and SVG presence

## Error Helper

Common failures:

- JSON parse error: validate and repair exact file.
- broken path: resolve relative to project root.
- invalid image extension: convert or skip.
- missing export: rerun `export_mindmap.py` after confirming Playwright Chromium is installed.

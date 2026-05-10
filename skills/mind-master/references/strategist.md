# Strategist Reference

The Strategist reads the converted source and asset index, then produces `intermediate/outline.json`.

## Inputs

- `intermediate/source.md`
- `assets/images/index.json`
- `manifest.json`
- selected style: `classic`, `logic`, or `org`

## Output Contract

Write valid JSON:

```json
{
  "root": "中心主题",
  "style": "classic",
  "max_depth": 4,
  "nodes": [
    {
      "id": "n1",
      "title": "一级分支标题",
      "description": "可选事实说明",
      "summary": "≤30 字提炼",
      "source_quote": "原文证据片段",
      "equations": ["E = mc^2"],
      "image_candidates": ["fig_p3_eq2.png"],
      "screenshot_intents": [
        {
          "target": "https://example.com/diagram",
          "selector": "#main-figure",
          "reason": "原文引用了这张架构图"
        }
      ],
      "children": []
    }
  ]
}
```

## Planning Rules

1. Preserve the author's argument structure before optimizing layout.
2. Keep node labels short according to `shared-standards.md`.
3. Put formulas on the most relevant node.
4. Treat source images with the four-way learning-map policy: `preserve` for key evidence charts, `crop_preserve` for source figures whose focused region is useful, `redraw:<template_id>` only when a registered SVG template exists, and `omit` by default.
5. Use OCR text only to judge image relevance.
6. Register external referenced visuals as `screenshot_intents`; do not fetch them in this step.
7. Keep IDs stable and simple: `n1`, `n1_1`, `n1_2`.
8. Prefer 4 to 7 first-level branches for `classic`.
9. Prefer cause/effect, premise/conclusion, or stage ordering for `logic`.
10. Prefer parent/child hierarchy for `org`.

## Word Content Fidelity Rules

For Word/PDF course notes, the primary job is faithful conversion into a readable mind map, not poster-style reinterpretation.

- Preserve the active H1/H2/H3 teaching skeleton unless the user explicitly requests a different synthesis.
- Heading nodes must preserve their original section number visibly in `title`, for example `5.1.1 Batch 的定义`. Do not replace numbered source headings with only conceptual labels such as `效率机制`.
- Each H2/H3 heading node must carry `section_id`. Nodes that do not correspond to an original source heading but are added by the Strategist must start their title with `[*]`.
- Source-numbered headings are a closed set. If the active source contains only `5.1`, `5.1.1` through `5.1.4`, `5.2`, `5.2.1` through `5.2.2`, and `5.3`, the outline must not create `5.2.3`, `5.4`, `5.5`, or any other absent source-style number.
- Convert paragraphs into concise leaf bullets under the nearest heading node instead of compressing several paragraphs into one oversized card description.
- Preserve source tables, display formulas, and instructional figures as first-class outline items.
- `本节小结` / `本章小结` can summarize the section, but it must not replace earlier body content.
- If a source paragraph is omitted, record the omission reason in `coverage_report.omitted`.

## Hierarchy Fidelity Rules

The outline must preserve the source's main skeleton.

- First-level outline branches must correspond to the source H2 headings or the highest semantic group under the active section. Do not promote H3 subsections to first-level branches just to get more branches.
- If the source clearly has a two-part or multi-part structure, such as "Topic A vs Topic B", keep those topics as first-level branches and place their subsections below them.
- In section map mode, the active H1 section is the root, its H2 headings become first-level branches, and its H3 headings become second-level nodes unless there is a documented reason to merge them.
- Under `balanced_two_sided`, the H2 branch root remains visible, such as `5.1 Batch`, and its H3 nodes remain one layer below it. Do not flatten `5.1.1` through `5.1.4` into independent first-level cards.
- If a style prefers 4 to 7 branches but the source has fewer H2 groups, preserve the source groups. Do not flatten lower-level sections to satisfy branch-count preference.

Hierarchy GATE:

After drafting `outline.json`, print a hierarchy correspondence table and wait for user confirmation before Step 5:

```text
Hierarchy GATE: 请确认章节层级映射后继续。
| Source section | Outline path | Action |
| --- | --- | --- |
| 5.1 Batch | root > Batch | preserved |
| 5.1.1 Batch 的定义 | root > Batch > Batch 的定义 | preserved |
```

The table must cover every H2 and H3 in the active source. If any source section is merged, list the target node and reason.

## Coverage Report

`outline.json` must include `coverage_report` for each active source section:

```json
{
  "coverage_report": {
    "source": "intermediate/sections/lesson_05.md",
    "sections": [
      {
        "source_heading": "5.1.1 Batch的定义",
        "node_path": "root > Batch > Batch 定义",
        "action": "node",
        "source_span": {"line_start": 9, "line_end": 26}
      }
    ],
    "tables": [
      {"source_label": "表5-1", "node_path": "root > Batch > 性能对比表", "action": "table"}
    ],
    "formulas": [
      {"source_label": "公式5-1", "node_path": "root > Momentum > 动量公式", "action": "formula"}
    ],
    "figures": [
      {"source_id": "fig_p38_004", "node_path": "root > Batch > 效率机制", "action": "image"}
    ],
    "omitted": [
      {"source": "装饰性校牌", "reason": "品牌装饰，不帮助理解课程概念"}
    ]
  }
}
```

Rules:

- Every H2 and H3 in the active source must appear in `coverage_report.sections`.
- Every source Markdown table must appear in `coverage_report.tables`.
- Every display formula must appear in `coverage_report.formulas`.
- Every source image in the active section must appear in `coverage_report.figures` or `coverage_report.omitted`.
- Missing coverage is a blocking validation failure.

## GPT Image 2 Inspired but Source-Faithful Profile

This is a visual organization profile, not a content rewriting mode.

- Use the source H1 as a strong center card. For Lesson 5, the preferred root title is `第5节课 模型训练技巧1：批量处理与动量`.
- Keep Batch on the left side; keep Momentum and the source summary on the right side when the source has this two-topic structure.
- Under Batch, keep the original sequence: definition, efficiency, generalization, comparison table. Details may render as numbered lists, but the node titles keep `5.1.1` through `5.1.4`.
- Under Momentum, use a formula node/card and a visual node/card to express `当前梯度 + 历史方向`.
- Keywords render as one bottom capsule strip with title `[*] 关键词`; they are not a numbered source chapter.
- A tuning or learning-hint node is allowed only when every item is marked `derived_from_summary` or `grounded_hint` and has `source_quote` or `source_span`. Its title must start with `[*]`.
- Do not sacrifice source truth for symmetry, icons, or a denser canvas.

## Specificity Rules

Concrete source detail should survive abstraction.

- Preserve specific numbers, ranges, examples, named concepts, and comparison dimensions as node details or table rows.
- An independent H3 node must carry 4 to 6 source-backed details when rendered as its own card. If the source cannot support at least four details and there is no formula/table attached, merge that material into the nearest sibling or parent instead of creating a sparse standalone card.
- Do not replace "20 training examples", "Batch Size 1~1000", or "10000~60000" with only "small" or "large".
- Do not split a source comparison table into unrelated sibling branches. Preserve it as a `table` node when the table is central to the explanation.
- For comparison tables, keep the original column and row dimensions unless a column is empty or duplicative.

## Evidence Rules

Every evidence-bearing node must be traceable.

- Leaf nodes must include `source_quote`.
- H2/H3 core nodes must include `source_quote` or `source_span`; prefer both when line spans are known.
- Auto-added density leaves must be drawn only from the owning node's `source_span`. If a candidate sentence cannot be bound to that span, do not add it.
- Table rows should include `source_quote` when the row is derived from prose or a source table row.
- Do not use general ML knowledge to complete missing explanations. If the source does not mention GPU memory, bandwidth, framework defaults, or other background details, omit them.
- If evidence is ambiguous, use `notes` to mark uncertainty rather than inventing a claim.

## Deduplication Pass

After drafting but before the hierarchy GATE:

1. Compare sibling branches and leaf nodes for synonymous claims.
2. Merge any node where at least 50% of its content repeats sibling content.
3. Record removed or merged nodes in `validation.json` under `deduplicated_nodes` when validation is produced.
4. If the merged node carried a useful synthesis, move it to parent `description` or `notes`; use parent `summary` only when the synthesis is explicitly present in source.

## Summary Rules

- `summary` is optional. Do not manufacture a "conclusion" for every node.
- Fill `summary` only when the source includes an explicit independent summary sentence.
- If a node's `description` and `summary` repeat each other, keep only the more informative field.

## Keywords and Tips Rules

- Scan the active source for bold terms, repeated technical terms, and Chinese-English paired terms such as `Noisy Gradient`.
- When enough terms exist, create one `type: "keywords"` node with `title: "[*] 关键词"` and `terms` containing 8 to 12 source-backed terms.
- Keywords must come from the active source; do not add domain terms just because they are common.
- Keywords nodes still need a traceable `source_quote`; use a real source sentence containing one or more of the listed terms, not a synthetic joined list.
- Create a `type: "tips"` node only when the source explicitly contains practice advice, tuning guidance, cautions, or tips.
- If the source has no practice/tuning/tips paragraph, do not generate a tips node. If the user asks for derived tuning implications, use title `[*] 调参启示`, set `type: "tips"`, and mark each item with `derived_from_summary` or `grounded_hint`; never number it as a source section.

## Grouping and Opposition Map

When the source contains opposing concepts, print a grouping map after the hierarchy table:

```text
Grouping map:
- Opposed groups: Small Batch ↔ Large Batch
- Layout intent: opposite sides of canvas
- Shared parent: Batch
```

This does not replace the hierarchy GATE; it tells the Executor which subtrees should receive contrasting visual treatment.

## Screenshot Intent Rules

Create a `screenshot_intents` entry only when:

- the source references a URL or local PDF page;
- the referenced visual is important to understanding;
- no adequate embedded image already exists.

For external URLs, include:

- `target`: full URL
- `selector`: CSS selector if known, otherwise empty string
- `reason`: why the visual matters

For local PDF pages, use:

```json
{
  "target": "file://projects/<project_name>/sources/source.pdf#page=3",
  "selector": "",
  "reason": "第 3 页包含核心流程图"
}
```

## Quality Bar

The outline is successful when an Executor can render a complete map without rereading the source document.

## Error Helper

If outline generation fails:

- invalid JSON: repair JSON first, then rerun validation;
- too deep: merge low-value leaves into `description` or `notes`; use `summary` only for explicit source synthesis;
- too verbose: shorten node titles before reducing branch count;
- missing formulas: search `source.md` for `$`, `$$`, and `EQUATION_UNRESOLVED`;
- unclear images: leave them as candidates and let Step 5 filter.

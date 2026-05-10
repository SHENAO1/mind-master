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
4. Treat images as candidates only. Do not force inclusion.
5. Use OCR text only to judge image relevance.
6. Register external referenced visuals as `screenshot_intents`; do not fetch them in this step.
7. Keep IDs stable and simple: `n1`, `n1_1`, `n1_2`.
8. Prefer 4 to 7 first-level branches for `classic`.
9. Prefer cause/effect, premise/conclusion, or stage ordering for `logic`.
10. Prefer parent/child hierarchy for `org`.

## Word Content Fidelity Rules

For Word/PDF course notes, the primary job is faithful conversion into a readable mind map, not poster-style reinterpretation.

- Preserve the active H1/H2/H3 teaching skeleton unless the user explicitly requests a different synthesis.
- Convert paragraphs into concise leaf bullets under the nearest heading node instead of compressing several paragraphs into one oversized card description.
- Preserve source tables, display formulas, and instructional figures as first-class outline items.
- `本节小结` / `本章小结` can summarize the section, but it must not replace earlier body content.
- If a source paragraph is omitted, record the omission reason in `coverage_report.omitted`.

## Hierarchy Fidelity Rules

The outline must preserve the source's main skeleton.

- First-level outline branches must correspond to the source H2 headings or the highest semantic group under the active section. Do not promote H3 subsections to first-level branches just to get more branches.
- If the source clearly has a two-part or multi-part structure, such as "Topic A vs Topic B", keep those topics as first-level branches and place their subsections below them.
- In section map mode, the active H1 section is the root, its H2 headings become first-level branches, and its H3 headings become second-level nodes unless there is a documented reason to merge them.
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

## Specificity Rules

Concrete source detail should survive abstraction.

- Preserve specific numbers, ranges, examples, named concepts, and comparison dimensions as node details or table rows.
- Do not replace "20 training examples", "Batch Size 1~1000", or "10000~60000" with only "small" or "large".
- Do not split a source comparison table into unrelated sibling branches. Preserve it as a `table` node when the table is central to the explanation.
- For comparison tables, keep the original column and row dimensions unless a column is empty or duplicative.

## Evidence Rules

Every evidence-bearing node must be traceable.

- Leaf nodes must include `source_quote`.
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

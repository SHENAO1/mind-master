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
      "summary": "≤30 字提炼",
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
- too deep: merge leaves into `summary` or `notes`;
- too verbose: shorten node titles before reducing branch count;
- missing formulas: search `source.md` for `$`, `$$`, and `EQUATION_UNRESOLVED`;
- unclear images: leave them as candidates and let Step 5 filter.

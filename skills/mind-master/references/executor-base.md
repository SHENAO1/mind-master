# Executor Base Reference

The Executor converts `outline.json` and curated assets into `mindmap.json`, `mindmap.md`, and Markmap HTML.

The primary output is an expandable Markmap mind map. Do not render the main result as a fixed-coordinate poster, infographic, or card canvas. SVG/PNG/PDF exports must come from the rendered Markmap HTML so that all formats match.

## Batch Preread

Before first generation, read in one pass:

- `shared-standards.md`
- `executor-base.md`
- selected style file
- `mindmap-formats.md`
- `math-rendering.md`
- `image-policy.md`

Do not reread references during the same render pass.

## Inputs

- `intermediate/outline.json`
- `assets/images/index.json`
- `manifest.json`
- design parameters confirmed by the user

## Outputs

- `intermediate/mindmap.json`
- `intermediate/mindmap.md`
- `exports/<project_name>.html`

## Mindmap JSON Shape

```json
{
  "root": {
    "id": "root",
    "title": "中心主题",
    "summary": "",
    "equations": [],
    "images": [],
    "children": []
  },
  "style": "classic",
  "theme": {
    "canvas": {"width": 1600, "height": 1000},
    "palette": "mind-master-default",
    "font_stack": "Inter, Noto Sans SC, Microsoft YaHei, PingFang SC, Arial, sans-serif"
  }
}
```

Nodes may include `type`, `description`, `summary`, `source_quote`, `table`, `equations`, `images`, `notes`, and `children` as defined in `mindmap-formats.md`.

For `type: "keywords"`, render `terms` as a horizontal capsule strip. For `type: "tips"`, render only source-backed complete-sentence guidance; if the node lacks source evidence, fail validation rather than inventing advice.
For learning-poster profiles, render `icon` metadata as simple inline line icons. Do not use emoji. If a node lacks an explicit icon, infer one from its source section or node type.

## Rendering Rules

1. Keep node titles short; put supporting points into markdown bullets under the node.
2. Use equations exactly as LaTeX strings.
3. Include only images that improve understanding at the rendered size.
4. Every included image must have `alt`.
5. Preserve source image filenames or screenshot IDs in `mindmap.json`.
6. Use Markmap-compatible Markdown as the HTML source.
7. Ensure the HTML can be opened offline.
8. Preserve the final hierarchy in `mindmap.md`; the HTML must render that Markdown with Markmap.
9. Do not use manual x/y coordinates for the main map. Layout belongs to Markmap and browser export.
10. Do not directly embed raw assets whose `type` is `screenshot`, `slide`, or `photo`, or whose `redraw_required` is true. Normalize figure decisions to `preserve_full`, `preserve_crop`, `redraw_high_fidelity`, `redraw_concept`, or `omit`; `preserve_crop` must write a cropped derivative with provenance and focus metadata, redraw may render only a registered SVG/HTML template, and missing templates must downgrade to `omit`.

## Layout Profile and Density Rules

Before rendering, read `layout_profile` from `outline.json` or generate it from the final tree. The layout profile must be copied into `mindmap.json`.

Weighting:

- ordinary node = 1
- leaf node = 1
- `table` node = 3
- `formula` node = 2
- `image` node or embedded source image = 3

Use `vertical` when total node count is `<= 18` and image count is `<= 2`.

Use `balanced_two_sided` when any of these conditions is true:

- total node count `> 24`
- any first-level branch weight `> 12`
- image count `>= 4`
- table count `>= 1` and leaf node count `> 16`
- estimated vertical height exceeds `1.4x` the configured canvas height

Use `compact_radial` only for medium-density maps that are too full for a simple vertical chain but do not trigger the two-sided thresholds.

When `mode = balanced_two_sided`:

- keep the root visually centered;
- for GPT Image 2 inspired course-note maps, make the root a strong center card rather than a small label;
- assign first-level branches left/right by subtree weight so both sides are as balanced as practical;
- place the largest and second-largest first-level branches on opposite sides;
- preserve explicit side intent when the source or outline marks it, such as Batch on the left and Momentum plus summary on the right;
- distribute cards around the root so the exported PNG/PDF reads as a horizontal mind map, not as two uneven columns;
- render visible connector curves from the root to first-level branches and from branch hubs to their child clusters, but keep connector stroke and opacity visually lighter than content cards;
- keep every H3 and lower descendant under the same H2 on that H2 side;
- keep images with their related node and pair each retained/redrawn image with 1 to 2 source-backed callouts;
- keep table nodes intact; they may render wider or scroll horizontally, but rows and columns must not be split;
- do not drop source-backed nodes, tables, formulas, or image decisions to improve aesthetics.
- render `type: "keywords"` nodes whose title starts with `[*]` as a bottom capsule strip, not as fake numbered branches.
- render `type: "tips"` nodes whose title starts with `[*]` as derived learning strips or compact grouped nodes, with visible non-numbered titles.

## Word Conversion Rendering

When the source is a Word/PDF course note:

- Render the H1/H2/H3 skeleton as headings in `mindmap.md`.
- Render paragraph-level facts as concise bullets, not as long card descriptions.
- Prefer short, numbered learning statements that preserve source claims, such as `Batch Size：一次迭代的更新样本数`.
- Use numbered lists for sibling facts when a card has three or more details; keep bullets compact and readable.
- If a node has fewer than two detail bullets, render the detail as plain text without numeric markers.
- If a single detail bullet repeats the node description, render only the more specific version.
- H3 heading nodes should render 4 to 6 source-backed details. If source text cannot support that density, merge the H3 into its parent or nearest sibling before rendering.
- Keep source tables as Markdown tables under the owning node.
- Keep figure decisions near the node selected by `figure_decisions`; screenshot-like figures render only as `preserve_crop` derivatives, registered high-fidelity/concept redraws, or are omitted with text density fallback.
- Size learning images by decision: dense charts and formula/axis/arrow images need larger minimum render dimensions than simple concept redraws.
- For `preserve_crop`, crop before layout so the final card contains the evidence region plus its callouts, not a tiny full-page screenshot.
- If no grounded callout can be found for a retained or redrawn figure, downgrade it to `omit`.
- Carry `coverage_report` and `figure_decisions` from `outline.json` into `mindmap.json`.
- Derived nodes such as keywords, Momentum advantages, or tuning hints must keep `[*]` titles and carry `derived`, `grounded_hint`, and `derived_from` metadata.

## Auto Density Guardrails

- Auto density extraction is section-local. Use only the owning node's `source_span`.
- Never scan the whole active source to backfill a sparse Momentum card with Batch or introduction content.
- Every auto density child must carry `source_span` for the exact source line and a `source_quote` that can be found in that line.
- Truncate display titles only at sentence, clause, or word boundaries. Do not cut an English token in half; keep the full `source_quote` even when the visible title is shortened.
- If fewer than the desired number of local candidates exist, leave the node sparse and let validation/reporting surface the limitation instead of inventing or cross-filling.

## Summary Rendering

- Do not render a "Conclusion", "结论", or summary label unless `summary` is non-empty and independent from `description`.
- If `summary` is empty, the card should not reserve visual space for it.
- If `description` and `summary` are synonymous, render only the more specific text.

## Center Node Requirements

The center/root node is the most important visual position and must contain:

- title;
- one sentence stating the core problem or learning question;
- 2 to 3 key terms from the source.

Do not render the center as only a slogan or one-line tagline. Do not fill the center by directly listing child branch titles.

For Lesson 5-like maps, the center card may use `第5节课 模型训练技巧1：批量处理与动量` and should state the learning question: how Batch Size affects efficiency/generalization and how Momentum combines current gradient with historical direction.
For the `gpt_image2_inspired_source_faithful` / `source_faithful_learning_poster` profile, split the center card into a strong kicker (`第5节课`), a large title (`模型训练技巧1：批量处理与动量`), and a short core theme line (`核心主题：Batch（批次）与 Momentum（动量）`).

## Math Delimiter Rules

- Any string containing subscripts, superscripts, Greek symbols, fractions, summations, or LaTeX commands must be wrapped in `$...$` or `$$...$$` before rendering.
- Strings containing `_{...}`, `^{...}`, `\frac`, `\sum`, `\nabla`, `\theta`, `\lambda`, or similar LaTeX syntax outside math delimiters are invalid.
- Step 7 validation must fail and block when node text contains LaTeX syntax that is not inside a math block.
- `batch_validate.py` should scan node text for patterns such as `_\{`, `\^\{`, `\frac`, `\sum`, and `\nabla` outside `$...$`, `$$...$$`, `\(...\)`, or `\[...\]`. This requires a script update.

## Table Rendering

Render `type: "table"` nodes as compact tables:

- title centered above the table;
- high-contrast header row;
- row height consistent with normal node text;
- no decorative cell backgrounds unless needed for comparison;
- keep columns and rows together in one node rather than scattering them across branches.

If a table is too wide for the node, prefer a wider node or horizontal scroll in HTML before dropping rows.

## Error Helper

When rendering fails:

- missing style: verify `manifest.json` and selected `executor-<style>.md`;
- broken image: remove or fix the asset path, then update `assets/images/index.json`;
- KaTeX failure: keep the formula in text and mark it unresolved if needed;
- overcrowded map: switch to `balanced_two_sided`, crop/reflow images, or widen tables before dropping content.

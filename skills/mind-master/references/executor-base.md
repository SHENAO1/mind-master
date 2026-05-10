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

## Word Conversion Rendering

When the source is a Word/PDF course note:

- Render the H1/H2/H3 skeleton as headings in `mindmap.md`.
- Render paragraph-level facts as concise bullets, not as long card descriptions.
- Keep source tables as Markdown tables under the owning node.
- Keep figures near the node selected by `figure_decisions`.
- Carry `coverage_report` and `figure_decisions` from `outline.json` into `mindmap.json`.

## Summary Rendering

- Do not render a "Conclusion", "结论", or summary label unless `summary` is non-empty and independent from `description`.
- If `summary` is empty, the card should not reserve visual space for it.
- If `description` and `summary` are synonymous, render only the more specific text.

## Center Node Requirements

The center/root node is the most important visual position and must contain:

- title;
- one sentence stating the core problem or learning question;
- a compact list of first-level branches, 2 to 6 items.

Do not render the center as only a slogan or one-line tagline.

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
- overcrowded map: reduce low-value image inclusions before dropping content.

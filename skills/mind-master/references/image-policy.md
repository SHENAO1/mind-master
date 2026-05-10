# Image Policy Reference

Images must improve comprehension. They are not decoration.

## Image Sources

- images embedded in DOCX
- rendered pages or regions from local PDF
- screenshots from external URLs after explicit user confirmation
- future generated images only when the user asks

## Per-Figure Decision Rule

Every image that appears in the active Word/PDF source must receive one explicit decision before rendering.

Allowed final decisions:

- `preserve_full`: keep the original source figure when the whole image is clear and all of it is evidence.
- `preserve_crop`: keep a cropped derivative when the original is valuable but needs white-space, slide title, decorative text, or edge clutter removed.
- `redraw_high_fidelity`: redraw the source figure with the same structure, key arrows, labels, equations, and relative relationships when the original is too complex or unreadable at map size.
- `redraw_concept`: redraw only the concept when exact source geometry is not important.
- `omit`: completely remove the image region and let text carry the node. This is the default for every figure that does not meet the strict requirements for `preserve_full`, `preserve_crop`, `redraw_high_fidelity`, or `redraw_concept`.

Legacy input decisions such as `image`, `preserve`, `crop_preserve`, `crop`, `embed_source`, `redraw_svg`, or `omitted` must be normalized to one of the five final decisions before final rendering.

Record the decision in both `figure_decisions` and `coverage_report.figures` / `coverage_report.omitted`. Do not silently drop source images.

Layout crowding alone is not a valid reason to delete a source figure, but mind maps are text-first artifacts. If a figure has no readable evidence value and no registered redraw template, omit it explicitly and strengthen the related node text instead of inserting a low-value visual.

Every source image in the active section must:

- appear in `figure_decisions`;
- appear in either `coverage_report.figures` or `coverage_report.omitted`;
- keep its source ID/path traceable even when cropped, redrawn, or omitted.

## Five-Way Figure Policy

The default is `omit`.

### A. `preserve_full`

Use only for source-backed data or irreducible visual evidence:

- real experimental curves, plots, heatmaps, or measured data visuals;
- figures where exact shape, values, or coordinates matter;
- assets explicitly classified as `type: "data_chart"`, `is_data_chart: true`, and `decision_hint: "preserve_full"`.

Rendering requirements:

- embed the original image at readable size, normally width `>= 400px`;
- provide meaningful `alt`, caption, and source ID;
- never classify ordinary slide screenshots as `preserve_full` merely because they contain a curve-like drawing.

Failure conditions:

- only a subregion is relevant;
- labels or axes become unreadable at final map size;
- slide title or unrelated English text dominates the useful graphic.

### B. `preserve_crop`

Use when a source figure is valuable but the full image wastes space or includes slide text/noise.

Rendering requirements:

- create a derivative under `assets/images/crops/`;
- keep `source_id`, `source_path`, `crop_source_id`, `crop_box`, and `crop_path` in `figure_decisions`;
- keep `crop_focus` or `crop_reason` explaining why the crop exists;
- crop to the evidence region without cutting axes, labels, equations, arrows, legends, or visual objects needed for interpretation;
- caption the crop with the same source-backed alt text and source ID;
- do not use `preserve_crop` to hide missing evidence or make a decorative crop.

Failure conditions:

- crop cuts off labels, axes, arrows, formulas, or the visual object being taught;
- crop is still too small to meet readability thresholds;
- crop lacks focus metadata.

Recommended Lesson 5 decisions:

- `fig_p38_004`: `preserve_crop`; keep both timing curves and key annotations while trimming surrounding whitespace.
- `fig_p46_006`: `preserve_crop`; it explains Flat Minima / Sharp Minima and generalization.
- `fig_p56_007`: `preserve_crop` or `redraw_high_fidelity`; it is the Momentum physical-inertia memory anchor.
- `fig_p63_008`: `preserve_crop` or `redraw_high_fidelity`; it explains recursive historical direction.
- `fig_p32_003`: `redraw_high_fidelity`; preserve the Full Batch vs Batch=1 update-frequency contrast.
- `fig_p43_005`: optional; include only if there is space and a clear evidence role.
- `fig_p23_002`: usually `omit` unless emphasizing the Batch/Epoch/Shuffle workflow.

### C. `redraw_high_fidelity`

Use when the source figure is visually important but a direct crop is still unreadable.

Rendering requirements:

- use a registered SVG/HTML template or a hand-built high-fidelity redraw;
- preserve source structure, key arrows, formulas, labels, and directionality;
- keep `source_id`, `source_path`, `redraw_template_id`, and `redraw_instruction`;
- include image callouts grounded in source quotes.

Failure conditions:

- a generic placeholder diagram replaces source structure;
- key arrows, formula terms, or contrast groups are lost;
- no registered or explicit high-fidelity redraw exists.

### D. `redraw_concept`

Use only when a registered SVG template exists in `assets/svg_templates/`.

Initial registered templates:

- `loss_landscape_sharp_vs_flat.svg`
- `gradient_vs_momentum_vector.svg`
- `batch_size_update_comparison.svg`

Rules:

- The renderer must load the registered template by ID.
- If the redraw template is missing, automatically downgrade to `omit` and log `redraw_template_missing: <asset_id>`.
- Do not use generic placeholder curves, generic wave diagrams, or repeated filler SVGs.

Failure conditions:

- exact source figure structure matters;
- the concept sketch would change the source's claim;
- the drawing is merely decorative.

### E. `omit`

Use for the normal case:

- screenshots, slide captures, dense text screenshots, decorative images, and blurry diagrams;
- concept visuals without a registered SVG template;
- figures already fully covered by text.

When omitting a source figure, the related node must carry enough text to stand alone: at least one concept description plus normally 4 to 6 source-backed details for an H3 node.

## Hard Screenshot Rule

Document screenshots are semantic references, not final embedded artwork.

- Every asset whose `type` is `screenshot`, `slide`, or `photo` defaults to `decision_hint: "omit"` unless it is explicitly classified as a real data chart, a `preserve_crop` learning image, or matches a registered SVG template.
- Executor must not render these assets through `<img>` or Markdown image syntax as raw originals.
- Executor may reference the raw asset only as source evidence for a cropped derivative, a registered-template redraw, or for explaining why it was omitted.
- `render_mindmap.py` must normalize any `figure_decisions` item targeting such an asset into `preserve_full`, `preserve_crop`, `redraw_high_fidelity`, `redraw_concept`, or `omit` before writing HTML.
- `batch_validate.py` must fail when final HTML or `mindmap.md` directly embeds an `assets/images/...` file whose asset `type` is `screenshot`, `slide`, or `photo`, or whose `redraw_required` is true.
- `batch_validate.py` must fail when inline SVGs look like repeated generic placeholder curves.
- Coverage must still record the original source asset ID/path, with the final action such as `preserve_crop`, `redraw_high_fidelity`, `redraw_concept`, or `omit`.

## Image Callouts

Every non-omitted figure must include 1 to 2 callouts:

```json
{
  "callouts": [
    {
      "text": "大 Batch 在单个 Epoch 上更快",
      "source_quote": "在一个 Epoch 中，较大的 Batch Size 反而能缩短训练时间"
    }
  ]
}
```

Rules:

- `text` is a short learning conclusion, not OCR text.
- `source_quote` must appear in the active source.
- Do not use general ML knowledge as a callout.
- If no grounded callout can be found, omit the figure.

## Selection Rules

Keep an image when:

- it explains a concept better than text;
- it is referenced by the source document;
- it is readable at the intended node size;
- its OCR text or alt text matches the node context;
- it is a diagram, chart, figure, or important screenshot.

Reject an image when:

- width or height is below 200 px;
- it is mostly body text;
- it is decorative;
- it duplicates a clearer image;
- it cannot be given meaningful alt text.

## Image Handling Priority

Use this priority order for every candidate visual:

1. Classify the asset in `assets/images/index.json` with `type`, `is_data_chart`, `redraw_required`, and `decision_hint`.
2. Use `preserve_full` for real data charts only when the full chart remains meaningful at readable size.
3. Use `preserve_crop` for focused source evidence when a full screenshot is too large but a region is useful.
4. Use `redraw_high_fidelity` for source structures that need arrows/formulas/labels preserved.
5. Use `redraw_concept` only through a registered SVG template when a simplified concept is enough.
6. Omit all other visuals and strengthen the related node text.
7. Reflow the layout, including switching to `balanced_two_sided`, when several preserved/cropped/redrawn visuals make the map too tall.

Source images used in final output must have:

- concise `alt`;
- visible caption;
- provenance from `source_anchor`, source page, or original asset ID.

## Schematic vs Data Gate

For every important image candidate, Step 5 must ask:

```text
Image Decision GATE: 这张候选图应是 preserve_full、preserve_crop、redraw_high_fidelity、redraw_concept 还是 omit？
- image_id: <id>
- source_anchor: <anchor>
- proposed decision: preserve_full | preserve_crop | redraw_high_fidelity | redraw_concept | omit
- proposed callouts: <1-2 source-backed conclusions>
- reason: <why>
```

Default decisions:

- slide screenshots, whiteboard photos, lecture schematic screenshots, and generic DOCX extracted images use `omit` by default;
- real data curves, heatmaps, or tables captured as images may use `preserve_full` only when `type: "data_chart"`, `is_data_chart: true`, and `redraw_required: false`;
- source-faithful learning screenshots may use `preserve_crop` only when a focused crop is readable and the source figure carries evidence not easily replaced by text;
- complex source figures may use `redraw_high_fidelity` only when the redraw preserves structure;
- concept screenshots may use `redraw_concept` only when a registered template matches;
- decorative logos, cover images, dense text screenshots, and unmatched screenshots use `omit`.

`assets/images/index.json` must record `type`, `is_data_chart`, `redraw_required`, `decision_hint`, optional `crop_box`, optional `crop_focus`, optional `redraw_template_id`, optional `redraw_instruction`, and `caption` where available to carry this decision into Step 6. The active outline must still include `figure_decisions` so validation can prove every source image was handled.

## OCR Rules

- OCR is optional.
- OCR text may inform image relevance.
- OCR text must not rewrite node labels.
- Store OCR output in `assets/images/index.json` as `ocr_text`.

## Image Index Contract

`assets/images/index.json` entries:

```json
{
  "id": "fig_p3_eq2",
  "path": "assets/images/fig_p3_eq2.png",
  "alt": "Diagram showing the relationship between variables",
  "source_anchor": "page-3-equation-2",
  "width": 640,
  "height": 360,
  "type": "screenshot | slide | photo | data_chart | illustration | decorative",
  "is_data_chart": false,
  "redraw_required": true,
  "decision_hint": "omit | preserve_full | preserve_crop | redraw_high_fidelity | redraw_concept",
  "crop_box": [0, 0, 640, 360],
  "crop_focus": "Crop to axes and trend lines; remove slide title.",
  "redraw_template_id": "",
  "redraw_instruction": "Redraw this screenshot as a compact SVG concept diagram.",
  "ocr_text": ""
}
```

Screenshots add:

```json
{
  "kind": "screenshot",
  "target": "https://example.com",
  "selector": "#main-figure",
  "reason": "原文引用了这张架构图"
}
```

## Screenshot Safety

Before opening external URLs:

1. Print every URL and reason.
2. Wait for user confirmation.
3. Use Playwright Chromium in headless mode.
4. Save screenshots under `assets/images/screenshots/`.
5. Generate one-sentence alt text after capture.

Local PDF page screenshots do not require external URL confirmation.

## Cropping and Readability

- Prefer selector or bbox crop over full-page screenshot.
- Avoid browser chrome in screenshots.
- Keep aspect ratio.
- Do not crop labels or legends.
- If a figure is unreadable at node size, exclude it or attach as a link.

## Copyright and Provenance

- Keep source path, URL, or source anchor in `index.json`.
- Do not strip provenance.
- For external screenshots, store target URL and capture time.
- Do not upload or republish beyond local output unless the user asks.
- Do not directly embed lecture slide screenshots when an equivalent inline SVG redraw can explain the concept.

## Error Helper

When image handling fails:

- missing file: remove or fix the index entry before rendering;
- missing alt: write a concise factual alt;
- screenshot blocked: record the failed intent and continue without it;
- unreadable preserve image: enlarge it, then omit with recorded reason if it still cannot be read;
- OCR unavailable: leave `ocr_text` empty and continue.

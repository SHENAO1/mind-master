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

- `preserve`: keep and enlarge the original source figure only when it is a real data chart, experimental plot, readable source photograph, or non-recreatable core evidence. Data charts should render at a readable width, normally at least 400 px, with caption and source ID.
- `crop_preserve`: keep a cropped derivative of the original source figure when the original is too large or slide-like but a focused region is important learning evidence.
- `redraw:<template_id>` / `redraw`: recreate the concept only when the asset has a registered SVG template in `assets/svg_templates/`. Redraw is semantic, not decorative.
- `omit`: completely remove the image region and let text carry the node. This is the default for all figures that are neither `preserve` nor registered-template `redraw`.

Legacy input decisions such as `image`, `crop`, `embed_source`, `redraw_svg`, or `omitted` must be normalized to `preserve`, `crop_preserve`, `redraw:<template_id>`, or `omit` before final rendering.

Record the decision in both `figure_decisions` and `coverage_report.figures` / `coverage_report.omitted`. Do not silently drop source images.

Layout crowding alone is not a valid reason to delete a source figure, but mind maps are text-first artifacts. If a figure has no readable evidence value and no registered redraw template, omit it explicitly and strengthen the related node text instead of inserting a low-value visual.

Every source image in the active section must:

- appear in `figure_decisions`;
- appear in either `coverage_report.figures` or `coverage_report.omitted`;
- keep its source ID/path traceable even when cropped, redrawn, or omitted.

## Four-Way Figure Policy

The default is `omit`.

### A. `preserve`

Use only for source-backed data or irreducible visual evidence:

- real experimental curves, plots, heatmaps, or measured data visuals;
- figures where exact shape, values, or coordinates matter;
- assets explicitly classified as `type: "data_chart"`, `is_data_chart: true`, and `decision_hint: "preserve"`.

Rendering requirements:

- embed the original image at readable size, normally width `>= 400px`;
- provide meaningful `alt`, caption, and source ID;
- never classify ordinary slide screenshots as `preserve` merely because they contain a curve-like drawing.

### B. `crop_preserve`

Use when a source figure is valuable but the full image wastes space or includes slide text/noise.

Rendering requirements:

- create a derivative under `assets/images/crops/`;
- keep `source_id`, `source_path`, `crop_source_id`, `crop_box`, and `crop_path` in `figure_decisions`;
- crop to the evidence region without cutting axes, labels, equations, arrows, legends, or visual objects needed for interpretation;
- caption the crop with the same source-backed alt text and source ID;
- do not use `crop_preserve` to hide missing evidence or make a decorative crop.

Recommended Lesson 5 decisions:

- `fig_p38_004`: `preserve`; it is the core evidence for Batch Size and epoch time.
- `fig_p46_006`: `preserve` or `crop_preserve`; it explains Flat Minima / Sharp Minima and generalization.
- `fig_p56_007`: `crop_preserve` or high-fidelity `redraw`; it is the Momentum physical-inertia memory anchor.
- `fig_p63_008`: `crop_preserve` or high-fidelity `redraw`; it explains recursive historical direction.
- `fig_p32_003`: `redraw:<template_id>` or `crop_preserve`; it explains Full Batch vs Batch=1.
- `fig_p43_005`: optional; include only if there is space and a clear evidence role.
- `fig_p23_002`: usually `omit` unless emphasizing the Batch/Epoch/Shuffle workflow.

### C. `redraw:<template_id>`

Use only when a registered SVG template exists in `assets/svg_templates/`.

Initial registered templates:

- `loss_landscape_sharp_vs_flat.svg`
- `gradient_vs_momentum_vector.svg`
- `batch_size_update_comparison.svg`

Rules:

- The renderer must load the registered template by ID.
- If `decision=redraw` but the template is missing, automatically downgrade to `omit` and log `redraw_template_missing: <asset_id>`.
- Do not use generic placeholder curves, generic wave diagrams, or repeated filler SVGs.

### D. `omit`

Use for the normal case:

- screenshots, slide captures, dense text screenshots, decorative images, and blurry diagrams;
- concept visuals without a registered SVG template;
- figures already fully covered by text.

When omitting a source figure, the related node must carry enough text to stand alone: at least one concept description plus normally 4 to 6 source-backed details for an H3 node.

## Hard Screenshot Rule

Document screenshots are semantic references, not final embedded artwork.

- Every asset whose `type` is `screenshot`, `slide`, or `photo` defaults to `decision_hint: "omit"` unless it is explicitly classified as a real data chart, a `crop_preserve` learning image, or matches a registered SVG template.
- Executor must not render these assets through `<img>` or Markdown image syntax as raw originals.
- Executor may reference the raw asset only as source evidence for a cropped derivative, a registered-template redraw, or for explaining why it was omitted.
- `render_mindmap.py` must normalize any `figure_decisions` item targeting such an asset into `preserve`, `crop_preserve`, `redraw:<template_id>`, or `omit` before writing HTML.
- `batch_validate.py` must fail when final HTML or `mindmap.md` directly embeds an `assets/images/...` file whose asset `type` is `screenshot`, `slide`, or `photo`, or whose `redraw_required` is true.
- `batch_validate.py` must fail when inline SVGs look like repeated generic placeholder curves.
- Coverage must still record the original source asset ID/path, with `action: "crop_preserve"`, `action: "redraw"`, or `action: "omit"` as appropriate.

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
2. Preserve real data charts only when they remain meaningful at readable size.
3. Crop-preserve focused source evidence when a full screenshot is too large but a region is useful.
4. Redraw only through a registered SVG template.
5. Omit all other visuals and strengthen the related node text.
6. Reflow the layout, including switching to `balanced_two_sided`, when several preserved/cropped/redrawn visuals make the map too tall.

Source images used in final output must have:

- concise `alt`;
- visible caption;
- provenance from `source_anchor`, source page, or original asset ID.

## Schematic vs Data Gate

For every important image candidate, Step 5 must ask:

```text
Image Decision GATE: 这张候选图是数据图（preserve）、重点截图（crop_preserve）、示意图（redraw）还是低价值图（omit）？
- image_id: <id>
- source_anchor: <anchor>
- proposed decision: omit | redraw:<template_id> | crop_preserve | preserve
- reason: <why>
```

Default decisions:

- slide screenshots, whiteboard photos, lecture schematic screenshots, and generic DOCX extracted images use `omit` by default;
- real data curves, heatmaps, or tables captured as images may use `preserve` only when `type: "data_chart"`, `is_data_chart: true`, and `redraw_required: false`;
- source-faithful learning screenshots may use `crop_preserve` only when a focused crop is readable and the source figure carries evidence not easily replaced by text;
- concept screenshots may use `redraw:<template_id>` only when a registered template matches;
- decorative logos, cover images, dense text screenshots, and unmatched screenshots use `omit`.

`assets/images/index.json` must record `type`, `is_data_chart`, `redraw_required`, `decision_hint`, optional `crop_box`, optional `redraw_template_id`, optional `redraw_instruction`, and `caption` where available to carry this decision into Step 6. The active outline must still include `figure_decisions` so validation can prove every source image was handled.

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
  "decision_hint": "omit | preserve | crop_preserve | redraw:<template_id>",
  "crop_box": [0, 0, 640, 360],
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

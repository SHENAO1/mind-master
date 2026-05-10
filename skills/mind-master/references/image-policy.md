# Image Policy Reference

Images must improve comprehension. They are not decoration.

## Image Sources

- images embedded in DOCX
- rendered pages or regions from local PDF
- screenshots from external URLs after explicit user confirmation
- future generated images only when the user asks

## Per-Figure Decision Rule

Every image that appears in the active Word/PDF source must receive one explicit decision before rendering.

Allowed decisions:

- `image`: keep and embed the source image near the relevant node.
- `crop`: keep a readable crop when the original contains useful but crowded content.
- `redraw`: recreate as SVG or a simple diagram when the original is an instructional sketch, slide screenshot, or too blurry at node size.
- `omitted`: remove only when decorative, duplicated, too small, unreadable, or not needed for understanding.

Record the decision in both `figure_decisions` and `coverage_report.figures` / `coverage_report.omitted`. Do not silently drop source images.

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

1. Prefer no image. If a concept is clear with concise text, table structure, formula, or layout, do not add an image.
2. Prefer SVG redraw. If a schematic is useful, such as Sharp vs Flat Minima, a vector-sum diagram, or a simple process diagram, the Executor should redraw it as clean inline SVG instead of embedding a raster slide screenshot.
3. Use the source image only as the last option. Embed a DOCX/PDF image only when it is hard to redraw, such as real experimental curves, heatmaps, screenshots of data, or visually dense evidence, and only when it remains readable at node size.

Source images used in final output must have:

- concise `alt`;
- visible caption;
- provenance from `source_anchor`, source page, or original asset ID.

## Schematic vs Data Gate

For every important image candidate, Step 5 must ask:

```text
Image Decision GATE: 这张候选图是数据图（可保留）还是示意图（应重绘）？
- image_id: <id>
- source_anchor: <anchor>
- proposed decision: no image | redraw_svg | embed_source
- reason: <why>
```

Default decisions:

- slide screenshots, whiteboard photos, and lecture schematic images extracted from DOCX use `redraw` when the idea is needed and `omitted` when the image repeats text;
- real data curves, heatmaps, tables captured as images, or non-redrawable screenshots may use `embed_source` if readable;
- decorative logos, cover images, and dense text screenshots use `no image`.

`assets/images/index.json` may record `figure_kind`, `decision`, `embed`, `redraw_instruction`, and `caption` to carry this decision into Step 6. The active outline must still include `figure_decisions` so validation can prove every source image was handled.

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
- Avoid republishing lecture slide screenshots when an equivalent inline SVG redraw can explain the concept.

## Error Helper

When image handling fails:

- missing file: remove or fix the index entry before rendering;
- missing alt: write a concise factual alt;
- screenshot blocked: record the failed intent and continue without it;
- unreadable crop: retry with a larger bbox or full figure selector;
- OCR unavailable: leave `ocr_text` empty and continue.

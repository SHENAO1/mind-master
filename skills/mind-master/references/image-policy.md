# Image Policy Reference

Images must improve comprehension. They are not decoration.

## Image Sources

- images embedded in DOCX
- rendered pages or regions from local PDF
- screenshots from external URLs after explicit user confirmation
- future generated images only when the user asks

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

## Error Helper

When image handling fails:

- missing file: remove or fix the index entry before rendering;
- missing alt: write a concise factual alt;
- screenshot blocked: record the failed intent and continue without it;
- unreadable crop: retry with a larger bbox or full figure selector;
- OCR unavailable: leave `ocr_text` empty and continue.

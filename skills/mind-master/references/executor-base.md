# Executor Base Reference

The Executor converts `outline.json` and curated assets into `mindmap.json` and Markmap HTML.

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

## Rendering Rules

1. Keep node titles short; put supporting points into markdown bullets under the node.
2. Use equations exactly as LaTeX strings.
3. Include only images that improve understanding at the rendered size.
4. Every included image must have `alt`.
5. Preserve source image filenames or screenshot IDs in `mindmap.json`.
6. Use Markmap-compatible Markdown as the HTML source.
7. Ensure the HTML can be opened offline.

## Error Helper

When rendering fails:

- missing style: verify `manifest.json` and selected `executor-<style>.md`;
- broken image: remove or fix the asset path, then update `assets/images/index.json`;
- KaTeX failure: keep the formula in text and mark it unresolved if needed;
- overcrowded map: reduce low-value image inclusions before dropping content.

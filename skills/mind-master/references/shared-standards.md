# Shared Standards

This file defines global content, design, and accessibility constraints for every Mind-Master role.

## Content Limits

Node text must be condensed.

| Node level | Limit |
| --- | --- |
| Root | concise topic phrase |
| Level 1 | <= 12 Chinese characters or <= 8 English words |
| Level 2 | <= 18 Chinese characters or <= 12 English words |
| Leaf | <= 30 Chinese characters or <= 20 English words |

If source text is longer, summarize. Do not paste paragraphs into nodes.

## Depth Limits

- Default `max_depth`: 4
- Hard maximum: 5
- If the document has deeper structure, merge low-value leaves or move detail into node `notes`.

## Canvas and Coordinate Defaults

Default design parameters for the first render:

- canvas: `1600x1000`
- export scale: `2`
- viewport fit: center root and fit all visible nodes
- avoid manual fixed coordinates unless a style spec requires them

## Typography

Default font stack:

```css
Inter, "Noto Sans SC", "Microsoft YaHei", "PingFang SC", Arial, sans-serif
```

Math font is controlled by KaTeX. Do not replace equations with screenshots.

## Color Standards

Use calm, high-contrast palettes. Avoid one-note monochrome maps.

Default palette:

- background: `#fbfbf8`
- root: `#1f4e5f`
- primary branches: `#2f6f73`, `#8a5a44`, `#5b6c8f`, `#7a6f3d`, `#8b4d64`
- node fill: `#ffffff`
- text: `#202124`
- muted text: `#5f6368`
- connector: `#8b949e`

## Accessibility

- Every image must have meaningful `alt`.
- Do not rely on color alone to show hierarchy.
- Maintain contrast suitable for reading on light background.
- Do not embed tiny unreadable images.
- Preserve source figure intent in `alt` and node context.

## Formula Placement

Place equations under the most relevant node, not the root by default. If a formula is central to the whole document, attach it to the root and reference its section in `notes`.

## Error Helper

When validation fails:

1. Identify whether the failure is content length, depth, math, image, or export.
2. Report the exact node ID or asset ID.
3. Prefer shrinking text, lowering depth, or removing low-value images before changing style.
4. Do not silently drop formulas or images; mark unresolved items explicitly.

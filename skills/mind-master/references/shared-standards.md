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

## Fidelity Rules

Mind-Master must stay grounded in the converted source.

- Every leaf-level claim must have evidence in `intermediate/source.md` or the active section source.
- Do not add background knowledge, hardware assumptions, framework advice, or common-sense explanations unless the source explicitly says them.
- Strategist nodes must carry `source_quote` for leaf claims and evidence-bearing table rows. The quote may be truncated, but it must be specific enough to find in source text.
- Validation must sample node claims and reverse-check the source. A claim with no corresponding source evidence is marked `hallucinated: true` and the outline must be rewritten.

## Redundancy Rules

Avoid creating nodes that only restate sibling content.

- If at least 50% of a node's points are synonymous restatements or concatenations of other sibling nodes, the node cannot remain independent.
- Merge redundant material into the nearest parent as `description` or `notes`; use `summary` only when the synthesis is explicitly present in source.
- Redundancy signal: a node combines paired phrases such as "X advantage / X disadvantage", "small X / large X", or "fast but risky / slow but robust" when those exact ideas already appear under sibling nodes.
- Strategist must run a node deduplication pass after drafting the outline. Validation output must record merged or removed nodes under `deduplicated_nodes`.

## Summary Semantics

Summaries are optional and must carry new information.

- There is no requirement that every node has a conclusion or `summary`.
- Fill `summary` only when the source has an explicit independent synthesis, signaled by words such as "therefore", "conclusion", "in summary", "因此", "结论", "综上", or an equivalent clearly summarizing sentence.
- `description` and `summary` must not be synonymous. If they repeat each other, keep the more informative one and leave the other empty.
- Renderers must not display empty "Conclusion", "结论", or summary slots.
- Summary nodes such as `本节小结`, `本章小结`, or `summary` must preserve complete source-backed statements. Do not reduce them to noun phrases.
- Each summary detail must be at least 15 visible Chinese characters or equivalent length in English, unless the source itself is shorter.
- Each summary detail must contain a verb-like predicate and must not end as a bare nominal phrase such as `效率泛化折中` or `加入方向惯性`.

## Detail Density

- H3-level teaching nodes should contain 4 to 6 source-backed details when they remain independent cards.
- If the source does not support four distinct details, merge the H3 into its parent or nearest sibling instead of padding the card with decorative images.
- Image omission must trigger text density fallback: the related node should still carry a concept sentence and enough source-backed details to stand alone.

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

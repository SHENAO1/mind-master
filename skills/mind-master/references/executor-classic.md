# Executor Classic Style

Classic style is a radial or balanced branch mind map for broad conceptual summaries.

## Best For

- textbook chapters
- reports with several peer topics
- research summaries
- planning documents

## Structure

- Root in the center.
- 4 to 7 first-level branches.
- Each first-level branch should feel like a category, not a sentence.
- Keep depth to 4 unless the source strongly requires 5.
- In section map mode, first-level branches are the source H2 headings with visible section numbers. H3 headings remain child cards under their H2 parent.

## Visual Treatment

- Use the default shared palette with branch-specific accent colors.
- Root should be visually strongest.
- For GPT Image 2 inspired source-faithful maps, the root is a large center card with the exact source lesson title and a short source-grounded learning question.
- For `source_faithful_poster` or `gpt_image2_inspired_source_faithful`, keep the canvas compact enough to feel like a finished learning poster rather than an infinite whiteboard screenshot.
- Level 1 nodes use accent color.
- Level 2 and leaves use white or light tinted fills.
- Images should appear near the node they explain, not near the root.
- Preserve semantic color grouping: children under the same parent use the same hue family with lighter tints.
- Opposing concepts should use contrast colors, such as cool colors for Small Batch and warm colors for Large Batch.
- Opposed or paired top-level themes should be placed on opposite sides of the canvas, not adjacent on the same side.
- Branch visual weight should reflect subtree size and importance. Use child count multiplied by a weighting factor to size or allocate space, instead of forcing every first-level branch to be equal.
- Route connectors around nodes. A connector must not cross through another node when a clear route exists.
- Child cards should remain compact. Use a maximum width around 320 px; wrap long titles/content rather than stretching cards into dashboard panels.
- Sibling cards under the same H2 may stack tightly. Do not force equal spacing when a compact cluster is more readable.
- Connect child cards back to the H2 branch hub with same-color thin connectors so cards do not appear to float independently.
- Keep connector strokes lower-contrast than content cards; images, formulas, and numbered details must carry the visual emphasis.
- Render keyword nodes (`[*] 关键词`) as a bottom capsule strip; do not give them invented source numbers.
- Render retained/redrawn images as grouped learning callouts: visual first, then 1 to 2 short source-backed conclusions next to or under the visual.

## Adaptive Layout

Classic maps must honor the shared `layout_profile` rules:

- small maps stay `vertical`;
- dense maps switch to `balanced_two_sided`;
- medium maps may use `compact_radial` if no two-sided threshold is reached.

For density scoring:

- ordinary node = 1
- leaf node = 1
- `table` node = 3
- `formula` node = 2
- `image` node or embedded source image = 3

Trigger `balanced_two_sided` when total nodes exceed 24, any first-level branch weight exceeds 12, source image count is at least 4, any table exists with more than 16 leaf nodes, or estimated vertical height exceeds 1.4 times canvas height.

In `balanced_two_sided`, place the root in the center and distribute first-level branches left/right by weight. The largest and second-largest first-level branches must be on opposite sides. Render connector curves so the result remains a mind map rather than a card dashboard. Use branch hubs plus child clusters to keep visual mass distributed around the center. Do not split H3 descendants away from their H2 parent, and do not split tables or move images away from their related node.

For course-note maps such as Lesson 5, the left or right side branch root is the H2 node itself, for example `5.1 Batch`, with `5.1.1` through `5.1.4` rendered one layer below it. Never flatten H3 sections into peer cards beside the H2 root.

Lesson 5 preferred balance:

- left: `5.1 Batch（批次）`
- right: `5.2 Momentum（动量）` and `5.3 本章小结`
- bottom: `[*] 关键词` and optional `[*] 调参启示` only when grounded
- Batch branch details should use compact numbered lists for definition, efficiency, generalization, and the comparison table.
- Momentum branch should keep the formula card close to the visual that explains `当前梯度 + 历史方向`.
- Never add fake visual-only source numbers such as `5.2.3`, `5.4`, or `5.5`; derived keyword and tuning nodes must keep the `[*]` prefix.

## Content Rules

- Level 1 labels: <= 12 Chinese characters.
- Avoid repeated prefixes across sibling branches.
- Prefer noun phrases over full sentences.
- If a formula defines a branch, place it immediately under that branch as a bullet.
- If the outline marks `type: "table"`, render it as a compact table inside one node with a centered title and consistent row height.
- Keep comparison tables visually intact. Do not turn table rows into separate radial branches.
- If a node has fewer than two bullet details, render the detail as plain body text, not as a numbered list.
- H3 child cards should normally contain 4 to 6 source-backed details. Do not stretch sparse cards with filler visuals; omit unmatched images and make the text do the work.
- If an H3 needs auto density, extract only from that H3's `source_span` and bind every added item to a source line.

## Error Helper

If classic output feels crowded:

1. Generate or correct `layout_profile` and switch to `balanced_two_sided` when thresholds are met.
2. Convert minor leaves into `description` or `notes` only when source fidelity remains traceable.
3. For screenshot-like source assets, use `preserve_crop` for source-faithful learning evidence, `redraw_high_fidelity` when source structure must be preserved through a registered template, `redraw_concept` for simplified registered concept sketches, or `omit`; for true data charts, use `preserve_full` at readable size before considering omission.
4. Keep formulas and source tables even if the layout must become wider.

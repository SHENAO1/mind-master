# Executor Org Style

Org style renders clean parent-child hierarchy for organizational, taxonomy, chapter, or component structures.

## Best For

- organization charts
- hierarchical taxonomies
- chapter outlines
- component breakdowns
- policy or standard structures

## Structure

- Root at top or left.
- Children arranged by hierarchy.
- Sibling order follows source order unless importance clearly differs.
- Keep child counts balanced where possible.

## Visual Treatment

- Use restrained colors and clear level distinction.
- Avoid radial decoration.
- Use compact nodes and predictable alignment.
- Images should be rare and attached only to nodes that need visual identification.
- Use consistent hue families for each parent subtree.
- Use contrast colors only when the hierarchy explicitly represents alternatives or opposing concepts.
- Keep sibling groups separated enough that connectors do not pass through unrelated nodes.
- Parent node size or visual weight should reflect the number and importance of visible descendants.

## Content Rules

- Keep labels as entity names or section names.
- Do not turn every paragraph into a leaf.
- Use `description` or `notes` to preserve important detail below a hierarchy node; use `summary` only for explicit source synthesis.
- Equations belong to the component, section, or concept they define.
- Render `type: "table"` nodes as compact tables under their owning section.
- Preserve comparison tables as one child node instead of distributing rows across the hierarchy.

## Error Helper

If org output is too deep:

1. Preserve the top three source heading levels.
2. Merge lower levels into summaries.
3. Keep critical equations and figures as node attachments.
4. Use notes rather than extra leaves for long procedural text.

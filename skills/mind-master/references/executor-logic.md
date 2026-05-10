# Executor Logic Style

Logic style renders argument structure, cause-effect chains, decision trees, or fishbone-style reasoning.

## Best For

- analytical essays
- technical root-cause analysis
- policy reasoning
- systems design explanations
- documents with premises, mechanisms, and conclusions

## Structure

Choose one of these structures:

- `logic-tree`: root -> premises -> evidence -> conclusion
- `cause-effect`: root problem -> causes -> mechanisms -> outcomes
- `fishbone`: root issue -> major cause categories -> evidence leaves

Do not mix all three in one map unless the document explicitly does.

## Visual Treatment

- Prefer left-to-right flow for process reasoning.
- Use connectors to clarify dependency order.
- Use muted colors for evidence and stronger colors for conclusions or key mechanisms.
- Images are useful only when they explain a mechanism or evidence source.
- Use one hue family for nodes in the same causal chain.
- Use contrast colors for opposing causes, tradeoffs, or alternatives.
- Place opposed concepts on opposite sides of the root question or decision point.
- Allocate more visual space to branches with more evidence nodes or more causal weight.
- Connectors must follow the reasoning direction and avoid crossing through evidence nodes.

## Content Rules

- Labels should show reasoning roles: cause, constraint, mechanism, outcome.
- Do not create decorative parallel branches.
- Preserve equations where they support a causal or analytical relation.
- Render `type: "table"` nodes as compact evidence tables when the source contains comparison data.
- Keep table rows and columns together as evidence; do not flatten them into separate causes.

## Error Helper

If logic output is unclear:

1. Identify the root question or problem.
2. Rename first-level branches by reasoning role.
3. Merge redundant evidence leaves.
4. Move background context into notes.

# Math Rendering Reference

Mind-Master keeps formulas editable as text and renders them through KaTeX in the final HTML.

## Source Formula Types

- Word OMML
- MathML fallback from Pandoc
- plain LaTeX in source text
- unresolved equation placeholders

## Conversion Rules

1. Convert OMML to LaTeX through `omml_to_latex.py`.
2. Inline equations use `$...$`.
3. Display equations use `$$...$$`.
4. If conversion fails, write `[EQUATION_UNRESOLVED:<id>]`.
5. Do not silently drop formulas.
6. Do not convert formulas into PNG or SVG images for normal rendering.

## LaTeX Safety

Allowed:

- arithmetic and algebra
- Greek symbols
- fractions
- roots
- matrices if KaTeX supports them
- common operators

Avoid:

- custom macros not supported by KaTeX
- raw HTML inside math
- TeX packages

## Placement Rules

- Strategist assigns formulas to the most relevant node.
- Executor preserves formula strings.
- Validator checks rendered HTML for `.katex-error`.

## KaTeX in HTML

The Markmap template should include KaTeX assets and auto-render configuration compatible with:

- `$...$`
- `$$...$$`
- `\(...\)`
- `\[...\]`

This rule already existed before the failed case: KaTeX is the intended renderer for `$...$`, `$$...$$`, `\(...\)`, and `\[...\]`. The stricter requirement is that formula-like text must be inside those delimiters before validation.

## Delimiter Validation

- Any node text containing LaTeX syntax such as `_{...}`, `^{...}`, `\frac`, `\sum`, `\sqrt`, `\nabla`, `\theta`, `\eta`, or `\lambda` must be wrapped in math delimiters.
- Unicode math shorthand such as `θ`, `η`, `λ`, `∇`, and superscript-like expressions should be normalized to editable LaTeX where practical.
- Step 7 validation must fail when LaTeX-like syntax appears outside `$...$`, `$$...$$`, `\(...\)`, or `\[...\]`.
- `batch_validate.py` should add a regex scan for unwrapped math patterns. This requires a script update.

## Error Helper

When math fails:

1. Find the equation ID or node ID.
2. Keep the original unresolved placeholder in source evidence.
3. Try a simpler KaTeX-compatible expression.
4. If still unresolved, display `[EQUATION_UNRESOLVED:<id>]` near the relevant node.
5. Never replace the equation with a screenshot unless the user explicitly requests a visual fallback.

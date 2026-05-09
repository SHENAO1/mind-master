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

## Error Helper

When math fails:

1. Find the equation ID or node ID.
2. Keep the original unresolved placeholder in source evidence.
3. Try a simpler KaTeX-compatible expression.
4. If still unresolved, display `[EQUATION_UNRESOLVED:<id>]` near the relevant node.
5. Never replace the equation with a screenshot unless the user explicitly requests a visual fallback.

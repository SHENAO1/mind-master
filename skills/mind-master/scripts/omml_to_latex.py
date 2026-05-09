#!/usr/bin/env python
"""Minimal OMML to LaTeX converter used by Mind-Master."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from lxml import etree

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:  # pragma: no cover
    pass


GREEK = {
    "α": r"\alpha",
    "β": r"\beta",
    "γ": r"\gamma",
    "δ": r"\delta",
    "ε": r"\epsilon",
    "θ": r"\theta",
    "λ": r"\lambda",
    "μ": r"\mu",
    "π": r"\pi",
    "ρ": r"\rho",
    "σ": r"\sigma",
    "φ": r"\phi",
    "ω": r"\omega",
    "Γ": r"\Gamma",
    "Δ": r"\Delta",
    "Θ": r"\Theta",
    "Λ": r"\Lambda",
    "Π": r"\Pi",
    "Σ": r"\Sigma",
    "Φ": r"\Phi",
    "Ω": r"\Omega",
}

OPERATORS = {
    "×": r"\times",
    "÷": r"\div",
    "·": r"\cdot",
    "≤": r"\le",
    "≥": r"\ge",
    "≠": r"\ne",
    "≈": r"\approx",
    "∞": r"\infty",
    "±": r"\pm",
    "∑": r"\sum",
    "∫": r"\int",
    "∏": r"\prod",
    "√": r"\sqrt",
    "→": r"\to",
    "←": r"\leftarrow",
    "↔": r"\leftrightarrow",
}

NARY_OPERATORS = {
    "∑": r"\sum",
    "∫": r"\int",
    "∏": r"\prod",
    "⋃": r"\bigcup",
    "⋂": r"\bigcap",
}


def local_name(element: Any) -> str:
    return etree.QName(element).localname


def attr_value(element: Any, name: str, default: str = "") -> str:
    for key, value in element.attrib.items():
        if etree.QName(key).localname == name:
            return value
    return default


def first_child(element: Any, name: str) -> Any | None:
    for child in element:
        if local_name(child) == name:
            return child
    return None


def convert_text(text: str | None) -> str:
    if not text:
        return ""
    converted: list[str] = []
    for char in text:
        converted.append(GREEK.get(char) or OPERATORS.get(char) or char)
    return "".join(converted)


def join_parts(parts: list[str]) -> str:
    return "".join(part for part in parts if part)


def braced(value: str) -> str:
    value = value.strip()
    return value if len(value) == 1 and value.isalnum() else "{" + value + "}"


def convert_container(element: Any) -> str:
    return join_parts([convert_element(child) for child in element])


def convert_fraction(element: Any) -> str:
    numerator = convert_element(first_child(element, "num"))
    denominator = convert_element(first_child(element, "den"))
    return rf"\frac{{{numerator}}}{{{denominator}}}"


def convert_radical(element: Any) -> str:
    degree = convert_element(first_child(element, "deg"))
    body = convert_element(first_child(element, "e"))
    if degree:
        return rf"\sqrt[{degree}]{{{body}}}"
    return rf"\sqrt{{{body}}}"


def convert_superscript(element: Any) -> str:
    base = convert_element(first_child(element, "e"))
    sup = convert_element(first_child(element, "sup"))
    return f"{braced(base)}^{{{sup}}}"


def convert_subscript(element: Any) -> str:
    base = convert_element(first_child(element, "e"))
    sub = convert_element(first_child(element, "sub"))
    return f"{braced(base)}_{{{sub}}}"


def convert_subsup(element: Any) -> str:
    base = convert_element(first_child(element, "e"))
    sub = convert_element(first_child(element, "sub"))
    sup = convert_element(first_child(element, "sup"))
    return f"{braced(base)}_{{{sub}}}^{{{sup}}}"


def convert_nary(element: Any) -> str:
    props = first_child(element, "naryPr")
    char = "∑"
    if props is not None:
        chr_element = first_child(props, "chr")
        if chr_element is not None:
            char = attr_value(chr_element, "val", char)
    operator = NARY_OPERATORS.get(char, OPERATORS.get(char, char))
    sub = convert_element(first_child(element, "sub"))
    sup = convert_element(first_child(element, "sup"))
    body = convert_element(first_child(element, "e"))

    limits = ""
    if sub:
        limits += f"_{{{sub}}}"
    if sup:
        limits += f"^{{{sup}}}"
    return f"{operator}{limits} {body}".rstrip()


def convert_delimiter(element: Any) -> str:
    props = first_child(element, "dPr")
    left = "("
    right = ")"
    if props is not None:
        beg = first_child(props, "begChr")
        end = first_child(props, "endChr")
        if beg is not None:
            left = attr_value(beg, "val", left)
        if end is not None:
            right = attr_value(end, "val", right)
    body = convert_element(first_child(element, "e"))
    return rf"\left{left} {body} \right{right}"


def convert_function(element: Any) -> str:
    name = convert_element(first_child(element, "fName")).strip()
    body = convert_element(first_child(element, "e"))
    if name:
        return rf"\{name}{{{body}}}" if name.isalpha() else f"{name}({body})"
    return body


def convert_matrix(element: Any) -> str:
    rows: list[str] = []
    for row in element:
        if local_name(row) != "mr":
            continue
        cells = [convert_element(cell) for cell in row if local_name(cell) == "e"]
        rows.append(" & ".join(cells))
    return r"\begin{matrix}" + r" \\ ".join(rows) + r"\end{matrix}"


def convert_accent(element: Any) -> str:
    props = first_child(element, "accPr")
    accent = "^"
    if props is not None:
        chr_element = first_child(props, "chr")
        if chr_element is not None:
            accent = attr_value(chr_element, "val", accent)
    body = convert_element(first_child(element, "e"))
    if accent == "\u0305" or accent == "¯":
        return rf"\overline{{{body}}}"
    if accent == "^":
        return rf"\hat{{{body}}}"
    return rf"\overset{{{accent}}}{{{body}}}"


def convert_bar(element: Any) -> str:
    body = convert_element(first_child(element, "e"))
    return rf"\overline{{{body}}}"


def convert_lim(element: Any, upper: bool) -> str:
    base = convert_element(first_child(element, "e"))
    limit = convert_element(first_child(element, "lim"))
    return f"{braced(base)}^{{{limit}}}" if upper else f"{braced(base)}_{{{limit}}}"


def convert_element(element: Any | None) -> str:
    if element is None:
        return ""

    name = local_name(element)
    if name == "t":
        return convert_text(element.text)
    if name in {"oMath", "oMathPara", "r", "e", "num", "den", "sub", "sup", "deg", "fName", "lim"}:
        return convert_container(element)
    if name == "f":
        return convert_fraction(element)
    if name == "rad":
        return convert_radical(element)
    if name == "sSup":
        return convert_superscript(element)
    if name == "sSub":
        return convert_subscript(element)
    if name == "sSubSup":
        return convert_subsup(element)
    if name == "nary":
        return convert_nary(element)
    if name == "d":
        return convert_delimiter(element)
    if name == "func":
        return convert_function(element)
    if name == "m":
        return convert_matrix(element)
    if name == "acc":
        return convert_accent(element)
    if name == "bar":
        return convert_bar(element)
    if name == "limLow":
        return convert_lim(element, upper=False)
    if name == "limUpp":
        return convert_lim(element, upper=True)

    return convert_container(element)


def parse_omml(omml: str | bytes | Any) -> Any:
    if hasattr(omml, "tag"):
        return omml
    parser = etree.XMLParser(resolve_entities=False, recover=True)
    if isinstance(omml, str):
        omml = omml.encode("utf-8")
    return etree.fromstring(omml, parser=parser)


def omml_to_latex(omml: str | bytes | Any) -> str:
    """Convert an OMML XML fragment or lxml element to a KaTeX-friendly string."""

    root = parse_omml(omml)
    latex = convert_element(root)
    return " ".join(latex.split())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert OMML XML to LaTeX.")
    parser.add_argument("--input", "-i", type=Path, help="OMML XML input file. Reads stdin if omitted.")
    parser.add_argument("--output", "-o", type=Path, help="Output .tex file. Prints stdout if omitted.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.input:
            xml = args.input.read_bytes()
        else:
            xml = sys.stdin.buffer.read()
        latex = omml_to_latex(xml)
    except Exception as exc:
        print(f"OMML conversion failed: {exc}", file=sys.stderr)
        return 1

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(latex + "\n", encoding="utf-8")
    else:
        print(latex)
    return 0


if __name__ == "__main__":
    sys.exit(main())

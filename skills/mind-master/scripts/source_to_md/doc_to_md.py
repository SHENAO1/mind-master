#!/usr/bin/env python
"""Convert DOCX sources to structured Markdown for Mind-Master."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from lxml import etree

try:  # Keep required checkpoint symbols printable on Windows consoles.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:  # pragma: no cover - Python implementations without reconfigure
    pass

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from omml_to_latex import omml_to_latex  # noqa: E402

try:
    from docx import Document
    from docx.document import Document as DocumentObject
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph
except ImportError as exc:  # pragma: no cover - surfaced in CLI
    raise SystemExit("python-docx is required. Install with: pip install python-docx") from exc


REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def local_name(element: Any) -> str:
    return etree.QName(element).localname


def attr_by_local_name(element: Any, local: str, default: str = "") -> str:
    for key, value in element.attrib.items():
        if etree.QName(key).localname == local:
            return value
    return default


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-").lower()
    return slug or "item"


def content_type_extension(content_type: str) -> str:
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/gif": ".gif",
        "image/bmp": ".bmp",
        "image/tiff": ".tif",
        "image/svg+xml": ".svg",
    }
    return mapping.get(content_type.lower(), ".bin")


def markdown_escape_cell(value: str) -> str:
    return " ".join(value.split()).replace("|", r"\|")


def paragraph_style_name(paragraph: Paragraph) -> str:
    return (paragraph.style.name if paragraph.style is not None else "") or ""


def paragraph_style_id(paragraph: Paragraph) -> str:
    return (paragraph.style.style_id if paragraph.style is not None else "") or ""


def heading_level(paragraph: Paragraph) -> int | None:
    style_name = paragraph_style_name(paragraph).strip()
    style_id = paragraph_style_id(paragraph).strip()
    for value in (style_id, style_name):
        match = re.search(r"(?:Heading|标题)\s*([1-6])", value, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def is_list_paragraph(paragraph: Paragraph) -> bool:
    style_name = paragraph_style_name(paragraph).lower()
    if "list" in style_name or "bullet" in style_name or "number" in style_name:
        return True
    ppr = paragraph._p.pPr
    return bool(ppr is not None and ppr.numPr is not None)


def list_prefix(paragraph: Paragraph) -> str:
    style_name = paragraph_style_name(paragraph).lower()
    if "number" in style_name:
        return "1. "
    return "- "


def iter_block_items(parent: DocumentObject | Any) -> Iterable[Paragraph | Table]:
    if hasattr(parent, "element") and hasattr(parent, "part"):
        parent_element = parent.element.body
        parent_part = parent.part
    else:
        parent_element = parent._tc
        parent_part = parent.part

    for child in parent_element.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent_part)


@dataclass
class ExtractedImage:
    temp_path: Path
    content_type: str
    alt: str = ""
    final_path: Path | None = None


@dataclass
class ConversionState:
    project_path: Path
    source_path: Path
    images_dir: Path
    equations_dir: Path
    image_pool: list[ExtractedImage] = field(default_factory=list)
    image_index: int = 0
    equation_index: int = 0
    paragraph_index: int = 0
    table_index: int = 0
    assets: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: {"images": [], "equations": [], "warnings": []}
    )

    def next_equation_id(self, anchor: str) -> str:
        self.equation_index += 1
        return f"eq_{safe_slug(anchor)}_{self.equation_index:03d}"

    def consume_image(self, anchor: str, alt: str, r_id: str | None, document: DocumentObject) -> str:
        self.image_index += 1
        image_record: ExtractedImage | None = None
        if self.image_pool:
            image_record = self.image_pool.pop(0)

        if image_record is None:
            if not r_id:
                self.assets["warnings"].append({"kind": "image", "message": f"Missing rId at {anchor}"})
                return ""
            related = document.part.related_parts.get(r_id)
            if related is None:
                self.assets["warnings"].append({"kind": "image", "message": f"Unknown image rId {r_id} at {anchor}"})
                return ""
            extension = content_type_extension(getattr(related, "content_type", "application/octet-stream"))
            temp_path = self.images_dir / f"_direct_img_{self.image_index:03d}{extension}"
            temp_path.write_bytes(related.blob)
            image_record = ExtractedImage(temp_path=temp_path, content_type=getattr(related, "content_type", ""), alt="")

        extension = image_record.temp_path.suffix or content_type_extension(image_record.content_type)
        final_name = f"fig_{safe_slug(anchor)}_{self.image_index:03d}{extension}"
        final_path = self.images_dir / final_name
        counter = 1
        while final_path.exists():
            final_name = f"fig_{safe_slug(anchor)}_{self.image_index:03d}_{counter}{extension}"
            final_path = self.images_dir / final_name
            counter += 1

        image_record.temp_path.replace(final_path)
        image_record.final_path = final_path
        resolved_alt = alt or image_record.alt or f"Image extracted from {anchor}"
        relative_path = final_path.relative_to(self.project_path).as_posix()
        self.assets["images"].append(
            {
                "id": final_path.stem,
                "path": relative_path,
                "alt": resolved_alt,
                "source_anchor": anchor,
                "content_type": image_record.content_type,
            }
        )
        return f"![{resolved_alt}]({relative_path})"

    def record_equation(self, anchor: str, latex: str, display: bool, unresolved: bool) -> None:
        equation_id = self.next_equation_id(anchor)
        if latex and not unresolved:
            (self.equations_dir / f"{equation_id}.tex").write_text(latex + "\n", encoding="utf-8")
        self.assets["equations"].append(
            {
                "id": equation_id,
                "latex": latex,
                "display": display,
                "status": "unresolved" if unresolved else "converted",
                "source_anchor": anchor,
            }
        )


def extract_images_with_mammoth(source_path: Path, images_dir: Path) -> tuple[list[ExtractedImage], list[str]]:
    try:
        import mammoth
    except ImportError:
        return [], ["mammoth is not installed; falling back to direct DOCX image extraction."]

    extracted: list[ExtractedImage] = []

    def convert_image(image: Any) -> dict[str, str]:
        index = len(extracted) + 1
        content_type = getattr(image, "content_type", "") or "application/octet-stream"
        extension = content_type_extension(content_type)
        temp_path = images_dir / f"_mammoth_img_{index:03d}{extension}"
        with image.open() as image_bytes:
            temp_path.write_bytes(image_bytes.read())
        alt = getattr(image, "alt_text", "") or ""
        extracted.append(ExtractedImage(temp_path=temp_path, content_type=content_type, alt=alt))
        return {"src": temp_path.name, "alt": alt}

    with source_path.open("rb") as docx_file:
        result = mammoth.convert_to_markdown(
            docx_file,
            convert_image=mammoth.images.img_element(convert_image),
        )
    messages = [
        str(message)
        for message in result.messages
        if "officeDocument/2006/math" not in str(message)
    ]
    return extracted, messages


def element_text(element: Any, xpath: str) -> str:
    values = element.xpath(xpath)
    texts: list[str] = []
    for value in values:
        if isinstance(value, str):
            texts.append(value)
        elif value.text:
            texts.append(value.text)
    return " ".join(texts).strip()


def drawing_to_markdown(drawing: Any, state: ConversionState, document: DocumentObject, anchor: str) -> str:
    blips = drawing.xpath(".//*[local-name()='blip']")
    if not blips:
        return ""
    r_id = blips[0].get(f"{{{REL_NS}}}embed") or blips[0].get(f"{{{REL_NS}}}link")
    doc_pr = drawing.xpath(".//*[local-name()='docPr']")
    alt = ""
    if doc_pr:
        alt = attr_by_local_name(doc_pr[0], "descr") or attr_by_local_name(doc_pr[0], "title")
    return state.consume_image(anchor, alt, r_id, document)


def omml_to_markdown(element: Any, state: ConversionState, anchor: str, display: bool) -> str:
    try:
        latex = omml_to_latex(element)
    except Exception:
        latex = ""

    unresolved = not bool(latex)
    equation_id = f"eq_{safe_slug(anchor)}_{state.equation_index + 1:03d}"
    state.record_equation(anchor, latex, display, unresolved)
    if unresolved:
        return f"[EQUATION_UNRESOLVED:{equation_id}]"
    if display:
        return f"\n\n$${latex}$$\n\n"
    return f"${latex}$"


def run_element_to_markdown(run_element: Any, state: ConversionState, document: DocumentObject, anchor: str) -> str:
    parts: list[str] = []
    for child in run_element:
        name = local_name(child)
        if name == "t":
            parts.append(child.text or "")
        elif name in {"tab"}:
            parts.append(" ")
        elif name in {"br", "cr"}:
            parts.append("\n")
        elif name in {"drawing", "pict"}:
            image_markdown = drawing_to_markdown(child, state, document, anchor)
            if image_markdown:
                parts.append(image_markdown)
        elif name in {"oMath", "oMathPara"}:
            parts.append(omml_to_markdown(child, state, anchor, display=name == "oMathPara"))
        else:
            for math_child in child.xpath(".//*[local-name()='oMath' or local-name()='oMathPara']"):
                parts.append(omml_to_markdown(math_child, state, anchor, display=local_name(math_child) == "oMathPara"))
    return "".join(parts)


def paragraph_to_markdown(paragraph: Paragraph, state: ConversionState, document: DocumentObject, anchor: str) -> str:
    parts: list[str] = []
    for child in paragraph._p:
        name = local_name(child)
        if name == "r":
            parts.append(run_element_to_markdown(child, state, document, anchor))
        elif name == "oMath":
            parts.append(omml_to_markdown(child, state, anchor, display=False))
        elif name == "oMathPara":
            parts.append(omml_to_markdown(child, state, anchor, display=True))
    text = "".join(parts).strip()
    if not text:
        return ""

    level = heading_level(paragraph)
    if level:
        return f"{'#' * level} {text}"
    if is_list_paragraph(paragraph):
        return f"{list_prefix(paragraph)}{text}"
    return text


def table_to_markdown(table: Table, state: ConversionState, document: DocumentObject) -> str:
    state.table_index += 1
    rows: list[list[str]] = []
    for row_index, row in enumerate(table.rows, start=1):
        cells: list[str] = []
        for cell_index, cell in enumerate(row.cells, start=1):
            anchor = f"tbl{state.table_index}_r{row_index}_c{cell_index}"
            paragraphs = [
                paragraph_to_markdown(paragraph, state, document, anchor)
                for paragraph in cell.paragraphs
            ]
            cell_text = " ".join(part for part in paragraphs if part)
            cells.append(markdown_escape_cell(cell_text))
        rows.append(cells)

    if not rows:
        return ""

    max_cols = max(len(row) for row in rows)
    normalized = [row + [""] * (max_cols - len(row)) for row in rows]
    header = normalized[0]
    separator = ["---"] * max_cols
    body = normalized[1:]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def is_list_block(block: str) -> bool:
    stripped = block.lstrip()
    return stripped.startswith("- ") or bool(re.match(r"^\d+\.\s+", stripped))


def join_markdown_blocks(blocks: list[str]) -> str:
    if not blocks:
        return ""
    output = blocks[0]
    previous = blocks[0]
    for block in blocks[1:]:
        separator = "\n" if is_list_block(previous) and is_list_block(block) else "\n\n"
        output += separator + block
        previous = block
    return output


def convert_docx(source_path: Path, project_path: Path) -> dict[str, Any]:
    project_path = project_path.resolve()
    images_dir = project_path / "assets" / "images"
    equations_dir = project_path / "assets" / "equations"
    intermediate_dir = project_path / "intermediate"
    for path in (images_dir, equations_dir, intermediate_dir):
        path.mkdir(parents=True, exist_ok=True)

    image_pool, mammoth_messages = extract_images_with_mammoth(source_path, images_dir)
    document = Document(str(source_path))
    state = ConversionState(
        project_path=project_path,
        source_path=source_path,
        images_dir=images_dir,
        equations_dir=equations_dir,
        image_pool=image_pool,
    )
    state.assets["warnings"].extend({"kind": "mammoth", "message": message} for message in mammoth_messages)

    blocks: list[str] = []
    for block in iter_block_items(document):
        if isinstance(block, Paragraph):
            state.paragraph_index += 1
            anchor = f"p{state.paragraph_index}"
            rendered = paragraph_to_markdown(block, state, document, anchor)
        else:
            rendered = table_to_markdown(block, state, document)
        if rendered:
            blocks.append(rendered)

    for leftover in state.image_pool:
        state.assets["warnings"].append(
            {
                "kind": "image",
                "message": f"Mammoth extracted image not referenced by parser: {leftover.temp_path.name}",
            }
        )

    markdown = join_markdown_blocks(blocks).strip() + "\n"
    source_md = intermediate_dir / "source.md"
    source_md.write_text(markdown, encoding="utf-8")

    asset_report = {
        "source": str(source_path.resolve()),
        "project": str(project_path),
        "generated_at": utc_now(),
        "source_markdown": str(source_md),
        "images": state.assets["images"],
        "equations": state.assets["equations"],
        "warnings": state.assets["warnings"],
    }
    report_path = intermediate_dir / "source_assets.json"
    report_path.write_text(json.dumps(asset_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return asset_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert a DOCX file to structured Markdown.")
    parser.add_argument("--source", required=True, type=Path, help="DOCX source path.")
    parser.add_argument("--project", required=True, type=Path, help="Mind-Master project path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    source_path = args.source.resolve()
    project_path = args.project.resolve()

    if not source_path.exists():
        print(f"Source does not exist: {source_path}", file=sys.stderr)
        return 2
    if source_path.suffix.lower() != ".docx":
        print(f"DOCX source expected, got: {source_path}", file=sys.stderr)
        return 2

    try:
        report = convert_docx(source_path, project_path)
    except Exception as exc:
        print(f"DOCX conversion failed: {exc}", file=sys.stderr)
        return 1

    print("GATE 1 \u2705 Source converted to Markdown.")
    print("Deliverables:")
    print(f"- source markdown: {report['source_markdown']}")
    print(f"- asset report: {project_path / 'intermediate' / 'source_assets.json'}")
    print(f"- images extracted: {len(report['images'])}")
    print(f"- equations converted: {len([item for item in report['equations'] if item['status'] == 'converted'])}")
    if report["warnings"]:
        print("Warnings:")
        for warning in report["warnings"]:
            print(f"- {warning['kind']}: {warning['message']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

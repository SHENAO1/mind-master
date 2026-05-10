#!/usr/bin/env python
"""Render a Mind-Master outline into Markmap Markdown and HTML."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # Keep checkpoint symbols printable on Windows consoles.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:  # pragma: no cover
    pass


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_PATH = SKILL_DIR / "templates" / "markmap.html"
MATH_DELIMITER_RE = re.compile(r"^\s*(?:\$.*\$\s*|\$\$.*\$\$\s*|\\\(.*\\\)\s*|\\\[.*\\\]\s*)$", re.S)
GREEK_REPLACEMENTS = {
    "η": r"\eta",
    "θ": r"\theta",
    "λ": r"\lambda",
    "∇": r"\nabla",
    "σ": r"\sigma",
    "α": r"\alpha",
    "β": r"\beta",
    "γ": r"\gamma",
    "μ": r"\mu",
    "Σ": r"\Sigma",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def project_relative(project_path: Path, path: Path) -> str:
    return path.resolve().relative_to(project_path.resolve()).as_posix()


def resolve_context(args: argparse.Namespace) -> dict[str, Path]:
    project_path = args.project.resolve()
    if args.section_id:
        map_dir = project_path / "maps" / args.section_id
        intermediate_dir = map_dir / "intermediate"
        exports_dir = map_dir / "exports"
        source_path = project_path / "intermediate" / "sections" / f"{args.section_id}.md"
    else:
        map_dir = project_path
        intermediate_dir = project_path / "intermediate"
        exports_dir = project_path / "exports"
        source_path = project_path / "intermediate" / "source.md"

    outline_path = args.outline or intermediate_dir / "outline.json"
    return {
        "project": project_path,
        "map_dir": map_dir,
        "intermediate": intermediate_dir,
        "exports": exports_dir,
        "source": source_path,
        "outline": outline_path,
        "manifest": project_path / "manifest.json",
        "images_index": project_path / "assets" / "images" / "index.json",
    }


def normalize_latex(raw: str) -> str:
    value = str(raw).strip()
    if not value:
        return value
    if MATH_DELIMITER_RE.match(value):
        return value

    for old, new in GREEK_REPLACEMENTS.items():
        value = value.replace(old, new)
    value = value.replace(r"\lambdav", r"\lambda v")
    value = re.sub(
        r"#\\left[（(]\s*([^)）]+?)\s*\\right[）)]",
        lambda match: rf"\tag{{{match.group(1).strip()}}}",
        value,
    )
    value = value.replace("#", "")
    tag_match = re.search(r"\\tag\{([^}]+)\}", value)
    if tag_match:
        tag = tag_match.group(1).strip()
        value = re.sub(r"\\tag\{[^}]+\}", "", value).strip()
        return f"${value}$（{tag}）"
    return f"${value}$"


def normalize_inline_math(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        inner = match.group(1)
        return normalize_latex(inner)

    return re.sub(r"\$(?!\$)(.+?)(?<!\$)\$", repl, str(text))


def markdown_escape(text: Any) -> str:
    value = normalize_inline_math(str(text or "").strip())
    value = value.replace("\r", " ").replace("\n", " ")
    return value


def plain_title(outline: dict[str, Any]) -> str:
    return str(outline.get("root") or outline.get("title") or "Mind Map").strip()


def image_index_by_id(images_index: list[dict[str, Any]] | dict[str, Any]) -> dict[str, dict[str, Any]]:
    if isinstance(images_index, dict):
        images = images_index.get("images", [])
    else:
        images = images_index
    return {str(item.get("id")): item for item in images if item.get("id")}


def image_path_for_markdown(project_path: Path, exports_dir: Path, image_path: str) -> str:
    raw = Path(image_path)
    absolute = raw if raw.is_absolute() else project_path / raw
    return Path(os.path.relpath(absolute, exports_dir)).as_posix()


def figure_decisions_by_node(outline: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    decisions: dict[str, list[dict[str, Any]]] = {}
    for item in outline.get("figure_decisions", []) or []:
        if not isinstance(item, dict):
            continue
        node_id = str(item.get("node_id") or item.get("target_node") or "")
        if not node_id:
            continue
        decisions.setdefault(node_id, []).append(item)
    return decisions


def node_images(
    node: dict[str, Any],
    outline: dict[str, Any],
    images_by_id: dict[str, dict[str, Any]],
    project_path: Path,
    exports_dir: Path,
) -> list[dict[str, str]]:
    resolved: list[dict[str, str]] = []
    raw_images = list(node.get("images", []) or [])
    for decision in figure_decisions_by_node(outline).get(str(node.get("id")), []):
        if decision.get("decision") in {"image", "embed_source", "keep", "crop"}:
            raw_images.append(decision)

    for raw in raw_images:
        if isinstance(raw, str):
            raw = {"id": raw}
        if not isinstance(raw, dict):
            continue
        source_id = str(raw.get("id") or raw.get("source_id") or "")
        asset = images_by_id.get(source_id, {})
        path = raw.get("path") or asset.get("path")
        if not path:
            continue
        alt = raw.get("alt") or asset.get("alt") or source_id or "mind map image"
        resolved.append(
            {
                "id": source_id,
                "path": image_path_for_markdown(project_path, exports_dir, str(path)),
                "alt": str(alt),
            }
        )
    return resolved


def append_bullet(lines: list[str], level: int, text: str) -> None:
    if text:
        lines.append(f"- {text}")


def append_table(lines: list[str], node: dict[str, Any], level: int) -> None:
    table = node.get("table") or {}
    columns = table.get("columns") or []
    rows = table.get("rows") or []
    if not columns or not rows:
        return
    lines.append("")
    lines.append("| " + " | ".join(markdown_escape(cell) for cell in columns) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        padded = list(row) + [""] * (len(columns) - len(row))
        lines.append("| " + " | ".join(markdown_escape(cell) for cell in padded[: len(columns)]) + " |")
    lines.append("")


def append_render_heading(lines: list[str], level: int, text: str) -> None:
    safe_level = min(max(level, 2), 6)
    lines.append("")
    lines.append("#" * safe_level + " " + text)


def append_node(
    lines: list[str],
    node: dict[str, Any],
    level: int,
    outline: dict[str, Any],
    images_by_id: dict[str, dict[str, Any]],
    project_path: Path,
    exports_dir: Path,
) -> None:
    title = markdown_escape(node.get("title") or node.get("id") or "节点")
    lines.append("")
    lines.append("#" * level + " " + title)

    description = markdown_escape(node.get("description", ""))
    summary = markdown_escape(node.get("summary", ""))
    if description:
        append_bullet(lines, level, description)
    if summary and summary != description:
        append_bullet(lines, level, summary)

    for note in node.get("notes", []) or []:
        append_bullet(lines, level, markdown_escape(note))

    for equation in node.get("equations", []) or []:
        append_render_heading(lines, level + 1, "公式：" + normalize_latex(str(equation)))

    if node.get("type") == "table" or node.get("table"):
        append_table(lines, node, level)

    for image in node_images(node, outline, images_by_id, project_path, exports_dir):
        append_render_heading(lines, level + 1, f"![{markdown_escape(image['alt'])}]({image['path']})")

    for child in node.get("children", []) or []:
        if isinstance(child, dict):
            append_node(lines, child, level + 1, outline, images_by_id, project_path, exports_dir)


def build_markdown(
    outline: dict[str, Any],
    images_by_id: dict[str, dict[str, Any]],
    project_path: Path,
    exports_dir: Path,
) -> str:
    lines = ["# " + markdown_escape(plain_title(outline))]
    if outline.get("source_title"):
        append_bullet(lines, 1, markdown_escape(outline["source_title"]))
    for node in outline.get("nodes", []) or []:
        if isinstance(node, dict):
            append_node(lines, node, 2, outline, images_by_id, project_path, exports_dir)
    return "\n".join(lines).strip() + "\n"


def build_mindmap_json(
    outline: dict[str, Any],
    manifest: dict[str, Any],
    markdown_path: Path,
    html_path: Path,
) -> dict[str, Any]:
    design = manifest.get("design", {})
    root = {
        "id": "root",
        "title": plain_title(outline),
        "description": outline.get("description", ""),
        "summary": outline.get("summary", ""),
        "source_quote": outline.get("source_title", outline.get("source_quote", "")),
        "children": outline.get("nodes", []) or [],
    }
    return {
        "root": root,
        "style": outline.get("style") or manifest.get("style", "classic"),
        "theme": {
            "canvas": manifest.get("canvas", {"width": 1600, "height": 1000}),
            "palette": design.get("palette", "mind-master-default"),
            "font_stack": design.get(
                "font_stack",
                'Inter, "Noto Sans SC", "Microsoft YaHei", "PingFang SC", Arial, sans-serif',
            ),
        },
        "markdown": str(markdown_path),
        "html": str(html_path),
        "coverage_report": outline.get("coverage_report", {}),
        "figure_decisions": outline.get("figure_decisions", []),
        "generated_at": utc_now(),
    }


def render_html(markdown: str, title: str, manifest: dict[str, Any]) -> str:
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Missing template: {TEMPLATE_PATH}")
    design = manifest.get("design", {})
    canvas = manifest.get("canvas", {"width": 1600, "height": 1000})
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    replacements = {
        "{{TITLE}}": html.escape(title),
        "{{META}}": html.escape("Mind-Master Markmap output"),
        "{{MARKDOWN}}": html.escape(markdown, quote=False),
        "{{CANVAS_WIDTH}}": str(canvas.get("width", 1600)),
        "{{CANVAS_HEIGHT}}": str(canvas.get("height", 1000)),
        "{{FONT_STACK}}": design.get(
            "font_stack",
            'Inter, "Noto Sans SC", "Microsoft YaHei", "PingFang SC", Arial, sans-serif',
        ),
    }
    html_text = template
    for key, value in replacements.items():
        html_text = html_text.replace(key, value)
    return html_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render outline.json to Markmap Markdown and HTML.")
    parser.add_argument("project", type=Path, help="Mind-Master project path.")
    parser.add_argument("--section-id", help="Render one maps/<section_id>/ workspace.")
    parser.add_argument("--outline", type=Path, help="Override outline path.")
    parser.add_argument("--style", choices=("classic", "logic", "org"), help="Override style metadata.")
    parser.add_argument("--image-mode", choices=("relative", "base64"), default="relative")
    args = parser.parse_args(argv)

    if args.image_mode != "relative":
        print("Only relative image mode is implemented in this renderer.", file=sys.stderr)
        return 2

    try:
        ctx = resolve_context(args)
        manifest = load_json(ctx["manifest"])
        outline = load_json(ctx["outline"])
        if args.style:
            outline["style"] = args.style
        images_by_id = image_index_by_id(load_json(ctx["images_index"], []))

        ctx["intermediate"].mkdir(parents=True, exist_ok=True)
        ctx["exports"].mkdir(parents=True, exist_ok=True)
        base_name = args.section_id or manifest.get("project_name") or ctx["project"].name
        markdown_path = ctx["intermediate"] / "mindmap.md"
        mindmap_path = ctx["intermediate"] / "mindmap.json"
        html_path = ctx["exports"] / f"{base_name}.html"

        markdown = build_markdown(outline, images_by_id, ctx["project"], ctx["exports"])
        markdown_path.write_text(markdown, encoding="utf-8")

        mindmap = build_mindmap_json(outline, manifest, markdown_path, html_path)
        write_json(mindmap_path, mindmap)

        html_text = render_html(markdown, plain_title(outline), manifest)
        html_path.write_text(html_text, encoding="utf-8")
    except Exception as exc:
        print(f"Render failed: {exc}", file=sys.stderr)
        return 1

    print("GATE 6 ✅ Mind map rendered.")
    print("Deliverables:")
    print(f"- mindmap json: {project_relative(ctx['project'], mindmap_path)}")
    print(f"- mindmap markdown: {project_relative(ctx['project'], markdown_path)}")
    print(f"- html: {project_relative(ctx['project'], html_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

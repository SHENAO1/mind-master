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
LAYOUT_MODES = {"vertical", "balanced_two_sided", "compact_radial"}
IMAGE_LAYOUT_DECISIONS = {"image", "embed_source", "keep", "crop", "redraw"}
NODE_TYPE_WEIGHTS = {"table": 3, "formula": 2, "image": 3}
BRANCH_COLORS = ["#2563d8", "#17813b", "#f97316", "#7c3aed", "#be185d", "#0f766e"]
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


def iter_nodes(nodes: list[Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in nodes:
        if not isinstance(item, dict):
            continue
        result.append(item)
        result.extend(iter_nodes(item.get("children", []) or []))
    return result


def node_weight(node: dict[str, Any], image_counts: dict[str, int]) -> int:
    node_type = str(node.get("type") or "concept")
    weight = NODE_TYPE_WEIGHTS.get(node_type, 1)
    weight += image_counts.get(str(node.get("id")), 0) * NODE_TYPE_WEIGHTS["image"]
    for child in node.get("children", []) or []:
        if isinstance(child, dict):
            weight += node_weight(child, image_counts)
    return max(1, weight)


def first_level_branch_weights(outline: dict[str, Any], image_counts: dict[str, int]) -> list[dict[str, Any]]:
    branches: list[dict[str, Any]] = []
    for node in outline.get("nodes", []) or []:
        if not isinstance(node, dict):
            continue
        branches.append(
            {
                "node_id": str(node.get("id") or ""),
                "title": str(node.get("title") or node.get("id") or ""),
                "weight": node_weight(node, image_counts),
                "side": "center",
            }
        )
    return branches


def collect_layout_stats(outline: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    all_nodes = iter_nodes(outline.get("nodes", []) or [])
    decisions = outline.get("figure_decisions", []) or []
    image_counts: dict[str, int] = {}
    image_count = 0
    for item in decisions:
        if not isinstance(item, dict):
            continue
        decision = str(item.get("decision") or "")
        if decision not in IMAGE_LAYOUT_DECISIONS:
            continue
        image_count += 1
        node_id = str(item.get("node_id") or item.get("target_node") or "")
        if node_id:
            image_counts[node_id] = image_counts.get(node_id, 0) + 1

    for node in all_nodes:
        if node.get("type") == "image" or node.get("images"):
            node_image_count = max(1, len(node.get("images", []) or []))
            image_count += node_image_count
            node_id = str(node.get("id") or "")
            if node_id:
                image_counts[node_id] = image_counts.get(node_id, 0) + node_image_count

    table_count = sum(1 for node in all_nodes if node.get("type") == "table" or node.get("table"))
    formula_count = sum(1 for node in all_nodes if node.get("type") == "formula" or node.get("equations"))
    leaf_count = sum(1 for node in all_nodes if not node.get("children"))
    max_depth = max((node_tree_depth(node) for node in outline.get("nodes", []) or [] if isinstance(node, dict)), default=0)
    branch_weights = first_level_branch_weights(outline, image_counts)
    canvas = manifest.get("canvas", {"height": 1000}) or {}
    canvas_height = int(canvas.get("height", 1000) or 1000)
    estimated_vertical_height = 120 + len(all_nodes) * 52 + image_count * 180 + table_count * 120 + max_depth * 48
    density_score = sum(item["weight"] for item in branch_weights)
    return {
        "total_nodes": len(all_nodes),
        "leaf_nodes": leaf_count,
        "table_count": table_count,
        "formula_count": formula_count,
        "image_count": image_count,
        "branch_weights": branch_weights,
        "max_branch_weight": max((item["weight"] for item in branch_weights), default=0),
        "canvas_height": canvas_height,
        "estimated_vertical_height": estimated_vertical_height,
        "density_score": density_score,
    }


def node_tree_depth(node: dict[str, Any]) -> int:
    children = [child for child in node.get("children", []) or [] if isinstance(child, dict)]
    if not children:
        return 1
    return 1 + max(node_tree_depth(child) for child in children)


def choose_layout_mode(stats: dict[str, Any]) -> tuple[str, str]:
    if stats["total_nodes"] <= 18 and stats["image_count"] <= 2:
        return "vertical", "total_nodes <= 18 and image_count <= 2"

    triggers: list[str] = []
    if stats["total_nodes"] > 24:
        triggers.append(f"total_nodes {stats['total_nodes']} > 24")
    if stats["max_branch_weight"] > 12:
        triggers.append(f"max_branch_weight {stats['max_branch_weight']} > 12")
    if stats["image_count"] >= 4:
        triggers.append(f"image_count {stats['image_count']} >= 4")
    if stats["table_count"] >= 1 and stats["leaf_nodes"] > 16:
        triggers.append(f"table_count {stats['table_count']} >= 1 and leaf_nodes {stats['leaf_nodes']} > 16")
    if stats["estimated_vertical_height"] > stats["canvas_height"] * 1.4:
        triggers.append(
            f"estimated_vertical_height {stats['estimated_vertical_height']} > canvas_height * 1.4 ({stats['canvas_height'] * 1.4:.0f})"
        )

    if triggers:
        return "balanced_two_sided", "; ".join(triggers)
    return "compact_radial", "medium density without balanced_two_sided trigger"


def assign_branch_sides(branch_weights: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    assigned = [dict(item) for item in branch_weights]
    if mode != "balanced_two_sided":
        for item in assigned:
            item["side"] = "center"
        return assigned

    by_id = {item["node_id"]: item for item in assigned}
    sorted_items = sorted(assigned, key=lambda item: item["weight"], reverse=True)
    totals = {"left": 0, "right": 0}
    for index, item in enumerate(sorted_items):
        if index == 0:
            side = "left"
        elif index == 1:
            side = "right"
        else:
            side = "left" if totals["left"] <= totals["right"] else "right"
        by_id[item["node_id"]]["side"] = side
        totals[side] += int(item["weight"])
    return assigned


def resolve_layout_profile(outline: dict[str, Any], manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    stats = collect_layout_stats(outline, manifest)
    generated_mode, generated_reason = choose_layout_mode(stats)
    existing = outline.get("layout_profile") if isinstance(outline.get("layout_profile"), dict) else {}
    mode = str(existing.get("mode") or generated_mode)
    if mode not in LAYOUT_MODES:
        mode = generated_mode

    branch_weights = assign_branch_sides(stats["branch_weights"], mode)
    profile = {
        "mode": mode,
        "density_score": int(existing.get("density_score") or stats["density_score"]),
        "reason": str(existing.get("reason") or generated_reason),
        "branch_weights": branch_weights,
        "metrics": {
            "total_nodes": stats["total_nodes"],
            "leaf_nodes": stats["leaf_nodes"],
            "table_count": stats["table_count"],
            "formula_count": stats["formula_count"],
            "image_count": stats["image_count"],
            "estimated_vertical_height": stats["estimated_vertical_height"],
            "canvas_height": stats["canvas_height"],
        },
    }
    return profile, stats


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


def html_text(value: Any) -> str:
    return html.escape(markdown_escape(value), quote=True)


def render_table_html(node: dict[str, Any]) -> str:
    table = node.get("table") or {}
    columns = table.get("columns") or []
    rows = table.get("rows") or []
    if not columns or not rows:
        return ""
    head = "".join(f"<th>{html_text(cell)}</th>" for cell in columns)
    body_rows: list[str] = []
    for row in rows:
        padded = list(row) + [""] * (len(columns) - len(row))
        cells = "".join(f"<td>{html_text(cell)}</td>" for cell in padded[: len(columns)])
        body_rows.append(f"<tr>{cells}</tr>")
    return (
        '<div class="balanced-table-wrap">'
        f'<table><thead><tr>{head}</tr></thead><tbody>{"".join(body_rows)}</tbody></table>'
        "</div>"
    )


def render_node_html(
    node: dict[str, Any],
    depth: int,
    outline: dict[str, Any],
    images_by_id: dict[str, dict[str, Any]],
    project_path: Path,
    exports_dir: Path,
    include_children: bool = True,
    extra_class: str = "",
) -> str:
    node_id = html.escape(str(node.get("id") or ""), quote=True)
    node_type = html.escape(str(node.get("type") or "concept"), quote=True)
    classes = ["balanced-node", f"depth-{min(depth, 4)}", f"type-{node_type}"]
    if extra_class:
        classes.append(extra_class)
    parts = [f'<article class="{" ".join(classes)}" data-node-id="{node_id}" data-node-type="{node_type}">']
    parts.append(f'<h{min(depth + 2, 6)}>{html_text(node.get("title") or node.get("id") or "节点")}</h{min(depth + 2, 6)}>')

    description = html_text(node.get("description", ""))
    summary = html_text(node.get("summary", ""))
    if description:
        parts.append(f'<p class="balanced-description">{description}</p>')
    if summary and summary != description:
        parts.append(f'<p class="balanced-summary">{summary}</p>')

    notes = [html_text(note) for note in node.get("notes", []) or [] if str(note).strip()]
    if notes:
        parts.append('<ul class="balanced-notes">' + "".join(f"<li>{note}</li>" for note in notes) + "</ul>")

    equations = [normalize_latex(str(equation)) for equation in node.get("equations", []) or []]
    if equations:
        parts.append('<div class="balanced-equations">')
        for equation in equations:
            parts.append(f'<div class="balanced-equation">公式：{html.escape(equation, quote=False)}</div>')
        parts.append("</div>")

    if node.get("type") == "table" or node.get("table"):
        parts.append(render_table_html(node))

    images = node_images(node, outline, images_by_id, project_path, exports_dir)
    if images:
        parts.append('<div class="balanced-images">')
        for image in images:
            src = html.escape(image["path"], quote=True)
            alt = html_text(image["alt"])
            parts.append(f'<figure><img src="{src}" alt="{alt}"><figcaption>{alt}</figcaption></figure>')
        parts.append("</div>")

    children = [child for child in node.get("children", []) or [] if isinstance(child, dict)]
    if children:
        simple_leaves = depth >= 1 and all(
            not child.get("children")
            and not child.get("table")
            and not child.get("equations")
            and not child.get("images")
            and child.get("type") not in {"table", "formula", "image"}
            for child in children
        )
        if include_children and simple_leaves:
            parts.append('<ol class="balanced-leaf-list">')
            for child in children:
                child_id = html.escape(str(child.get("id") or ""), quote=True)
                parts.append(f'<li data-node-id="{child_id}">{html_text(child.get("title") or child.get("id") or "")}</li>')
            parts.append("</ol>")
        elif include_children:
            child_class = "balanced-branch-children" if depth == 0 else "balanced-node-children"
            parts.append(f'<div class="{child_class}">')
            for child in children:
                parts.append(render_node_html(child, depth + 1, outline, images_by_id, project_path, exports_dir))
            parts.append("</div>")

    parts.append("</article>")
    return "".join(parts)


def build_balanced_html(
    outline: dict[str, Any],
    layout_profile: dict[str, Any],
    images_by_id: dict[str, dict[str, Any]],
    project_path: Path,
    exports_dir: Path,
) -> str:
    if layout_profile.get("mode") != "balanced_two_sided":
        return ""
    branch_items = [item for item in layout_profile.get("branch_weights", []) or [] if isinstance(item, dict)]
    side_by_id = {str(item.get("node_id")): str(item.get("side") or "right") for item in branch_items}
    weight_by_id = {str(item.get("node_id")): int(item.get("weight") or 0) for item in branch_items}
    left_nodes: list[dict[str, Any]] = []
    right_nodes: list[dict[str, Any]] = []
    for node in outline.get("nodes", []) or []:
        if not isinstance(node, dict):
            continue
        side = side_by_id.get(str(node.get("id")), "right")
        if side == "left":
            left_nodes.append(node)
        else:
            right_nodes.append(node)

    max_weight = max(weight_by_id.values(), default=0)

    def render_branch(node: dict[str, Any], side: str, index: int, count: int) -> str:
        node_id = str(node.get("id") or "")
        color = BRANCH_COLORS[index % len(BRANCH_COLORS)] if side == "left" else BRANCH_COLORS[(index + 1) % len(BRANCH_COLORS)]
        weight = weight_by_id.get(node_id, 0)
        dominant = " is-dominant" if weight == max_weight and weight > 0 else ""
        children = [child for child in node.get("children", []) or [] if isinstance(child, dict)]
        child_html = "".join(
            render_node_html(child, 1, outline, images_by_id, project_path, exports_dir)
            for child in children
        )
        child_block = f'<div class="balanced-branch-children">{child_html}</div>' if child_html else ""
        hub = render_node_html(
            node,
            0,
            outline,
            images_by_id,
            project_path,
            exports_dir,
            include_children=False,
            extra_class="balanced-hub",
        )
        return (
            f'<section class="balanced-branch{dominant}" data-side="{side}" data-node-id="{html.escape(node_id, quote=True)}" '
            f'data-branch-index="{index}" data-side-count="{count}" style="--branch-color:{color}">'
            + (child_block + hub if side == "left" else hub + child_block)
            + "</section>"
        )

    def render_side(nodes: list[dict[str, Any]], side: str) -> str:
        branch_html = "".join(render_branch(node, side, index, len(nodes)) for index, node in enumerate(nodes))
        return f'<section class="balanced-side {side}" aria-label="{side} branches">{branch_html}</section>'

    branch_names = [str(node.get("title") or node.get("id") or "") for node in outline.get("nodes", []) if isinstance(node, dict)]
    root_summary = html_text(outline.get("source_title") or outline.get("description") or "")
    root_items = "".join(f"<li>{html_text(name)}</li>" for name in branch_names if name)
    parts = [
        '<section class="balanced-layout mind-master-render" data-layout-mode="balanced_two_sided">',
        '<svg class="balanced-live-connectors" aria-hidden="true"></svg>',
        render_side(left_nodes, "left"),
        '<section class="balanced-root" aria-label="root">',
        f"<h1>{html_text(plain_title(outline))}</h1>",
    ]
    if root_summary:
        parts.append(f'<p>{root_summary}</p>')
    if root_items:
        parts.append(f"<ul>{root_items}</ul>")
    parts.extend(["</section>", render_side(right_nodes, "right"), "</section>"])
    return "".join(parts)


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
    layout_profile: dict[str, Any],
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
        "layout_profile": layout_profile,
        "generated_at": utc_now(),
    }


def render_html(
    markdown: str,
    title: str,
    manifest: dict[str, Any],
    layout_profile: dict[str, Any],
    balanced_html: str,
) -> str:
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Missing template: {TEMPLATE_PATH}")
    design = manifest.get("design", {})
    canvas = manifest.get("canvas", {"width": 1600, "height": 1000})
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    layout_mode = str(layout_profile.get("mode") or "vertical")
    markmap_class = "is-hidden" if layout_mode == "balanced_two_sided" else "mind-master-render"
    replacements = {
        "{{TITLE}}": html.escape(title),
        "{{META}}": html.escape(f"Mind-Master Markmap output · layout: {layout_mode}"),
        "{{MARKDOWN}}": html.escape(markdown, quote=False),
        "{{BALANCED_HTML}}": balanced_html,
        "{{LAYOUT_MODE}}": html.escape(layout_mode),
        "{{LAYOUT_PROFILE_JSON}}": html.escape(json.dumps(layout_profile, ensure_ascii=False), quote=False),
        "{{MARKMAP_CLASS}}": markmap_class,
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


def write_layout_self_check(path: Path, layout_profile: dict[str, Any], stats: dict[str, Any]) -> None:
    metrics = layout_profile.get("metrics", {})
    branch_lines = []
    for item in layout_profile.get("branch_weights", []) or []:
        if not isinstance(item, dict):
            continue
        branch_lines.append(
            f"- `{item.get('node_id')}` / {item.get('title', '')}: weight={item.get('weight')}, side={item.get('side')}"
        )
    lines = [
        "# Layout Self Check",
        "",
        f"- selected_mode: `{layout_profile.get('mode')}`",
        f"- density_score: `{layout_profile.get('density_score')}`",
        f"- reason: {layout_profile.get('reason')}",
        f"- total_nodes: {metrics.get('total_nodes', stats.get('total_nodes'))}",
        f"- leaf_nodes: {metrics.get('leaf_nodes', stats.get('leaf_nodes'))}",
        f"- image_count: {metrics.get('image_count', stats.get('image_count'))}",
        f"- table_count: {metrics.get('table_count', stats.get('table_count'))}",
        f"- estimated_vertical_height: {metrics.get('estimated_vertical_height', stats.get('estimated_vertical_height'))}",
        "",
        "## Branch Weights",
        "",
        *branch_lines,
        "",
        "## Fidelity Notes",
        "",
        "- Layout selection only changes placement; it does not remove H2/H3 nodes, tables, formulas, or figure decisions.",
        "- In `balanced_two_sided`, each H2 branch owns all of its H3 descendants on the same side.",
        "- Images stay attached to the node selected by `figure_decisions`; tables render as intact table nodes.",
        "- Balanced two-sided HTML renders root-to-branch and branch-to-child connector paths so the output remains recognizable as a mind map.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


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
        layout_self_check_path = ctx["intermediate"] / "layout_self_check.md"
        html_path = ctx["exports"] / f"{base_name}.html"

        layout_profile, layout_stats = resolve_layout_profile(outline, manifest)
        markdown = build_markdown(outline, images_by_id, ctx["project"], ctx["exports"])
        markdown_path.write_text(markdown, encoding="utf-8")

        mindmap = build_mindmap_json(outline, manifest, markdown_path, html_path, layout_profile)
        write_json(mindmap_path, mindmap)
        write_layout_self_check(layout_self_check_path, layout_profile, layout_stats)

        balanced_html = build_balanced_html(outline, layout_profile, images_by_id, ctx["project"], ctx["exports"])
        html_text = render_html(markdown, plain_title(outline), manifest, layout_profile, balanced_html)
        html_path.write_text(html_text, encoding="utf-8")
    except Exception as exc:
        print(f"Render failed: {exc}", file=sys.stderr)
        return 1

    print("GATE 6 ✅ Mind map rendered.")
    print("Deliverables:")
    print(f"- mindmap json: {project_relative(ctx['project'], mindmap_path)}")
    print(f"- mindmap markdown: {project_relative(ctx['project'], markdown_path)}")
    print(f"- layout self-check: {project_relative(ctx['project'], layout_self_check_path)}")
    print(f"- html: {project_relative(ctx['project'], html_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

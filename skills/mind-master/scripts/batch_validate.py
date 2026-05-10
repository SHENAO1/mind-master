#!/usr/bin/env python
"""Validate Mind-Master Markmap artifacts."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment]

try:  # Keep checkpoint symbols printable on Windows consoles.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:  # pragma: no cover
    pass


HEADING_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$", re.M)
SECTION_ID_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\s*(.*)$")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
HTML_IMG_RE = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']", re.I)
DISPLAY_MATH_RE = re.compile(r"\$\$(.+?)\$\$", re.S)
INLINE_MATH_RE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.S)
LATEX_LIKE_RE = re.compile(r"(?:_\{|[\^]\{|\\(?:frac|sum|nabla|theta|lambda|eta|sigma|alpha|beta|gamma|mu|Sigma)\b)")
LAYOUT_MODES = {"vertical", "balanced_two_sided", "compact_radial"}
SCREENSHOT_EMBED_BLOCK_TYPES = {"screenshot", "slide", "photo"}
ALLOWED_FIGURE_DECISIONS = {"preserve_full", "preserve_crop", "redraw_high_fidelity", "redraw_concept", "omit"}
LEGACY_FIGURE_DECISIONS = {"preserve", "crop_preserve", "redraw"}
SVG_BLOCK_RE = re.compile(r"<svg\b[^>]*>(.*?)</svg>", re.I | re.S)
SVG_PATH_D_RE = re.compile(r"<path\b[^>]*\bd=[\"']([^\"']+)[\"']", re.I)
SVG_COMMAND_RE = re.compile(r"[A-Za-z]")
SVG_SIZE_RE = re.compile(r"<svg\b[^>]*?(?:width=\"([0-9.]+)[^\"]*\"[^>]*height=\"([0-9.]+)[^\"]*\"|height=\"([0-9.]+)[^\"]*\"[^>]*width=\"([0-9.]+)[^\"]*\")", re.I)
SVG_VIEWBOX_RE = re.compile(r"viewBox=\"[^\"]*?\s+([0-9.]+)\s+([0-9.]+)\"", re.I)


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


def resolve_context(args: argparse.Namespace) -> dict[str, Path]:
    project_path = args.project.resolve()
    if args.section_id:
        map_dir = project_path / "maps" / args.section_id
        intermediate_dir = map_dir / "intermediate"
        exports_dir = map_dir / "exports"
        base_name = args.section_id
        source_path = project_path / "intermediate" / "sections" / f"{args.section_id}.md"
    else:
        map_dir = project_path
        intermediate_dir = project_path / "intermediate"
        exports_dir = project_path / "exports"
        base_name = project_path.name
        source_path = project_path / "intermediate" / "source.md"
    return {
        "project": project_path,
        "map_dir": map_dir,
        "intermediate": intermediate_dir,
        "exports": exports_dir,
        "source": source_path,
        "outline": intermediate_dir / "outline.json",
        "mindmap": intermediate_dir / "mindmap.json",
        "markdown": intermediate_dir / "mindmap.md",
        "validation": intermediate_dir / "validation.json",
        "html": exports_dir / f"{base_name}.html",
        "svg": exports_dir / f"{base_name}.svg",
        "png": exports_dir / f"{base_name}.png",
        "export_report": intermediate_dir / "export.json",
        "images_index": project_path / "assets" / "images" / "index.json",
    }


def project_relative(project_path: Path, path: Path) -> str:
    return path.resolve().relative_to(project_path.resolve()).as_posix()


def flatten_nodes(node: dict[str, Any], level: int = 0) -> list[tuple[dict[str, Any], int]]:
    result = [(node, level)]
    for child in node.get("children", []) or []:
        if isinstance(child, dict):
            result.extend(flatten_nodes(child, level + 1))
    return result


def node_depth(node: dict[str, Any]) -> int:
    children = [child for child in node.get("children", []) or [] if isinstance(child, dict)]
    if not children:
        return 1
    return 1 + max(node_depth(child) for child in children)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value or "").replace("...", "").replace("……", "")


def source_quote_found(quote: str, source_text: str) -> bool:
    if not quote:
        return False
    normalized_source = normalize_text(source_text)
    parts = [part for part in re.split(r"\.{3,}|……", quote) if len(normalize_text(part)) >= 4]
    if not parts:
        parts = [quote]
    return all(normalize_text(part) in normalized_source for part in parts)


def visible_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def check_node_lengths(flat: list[tuple[dict[str, Any], int]]) -> dict[str, Any]:
    limits = {1: 999, 2: 12, 3: 18}
    violations: list[dict[str, Any]] = []
    for node, level in flat:
        if level == 0:
            continue
        title = str(node.get("title") or "")
        if node_section_id(node):
            limit = 42 if level >= 2 else 30
        elif node.get("summary_sentence") or node.get("auto_density") or node.get("learning_point"):
            limit = 90
        elif node.get("derived") or node.get("grounded_hint") or str(node.get("title") or "").startswith("[*]"):
            limit = 36
        else:
            limit = limits.get(level, 30)
        length = visible_len(title)
        if length > limit:
            violations.append(
                {
                    "id": node.get("id"),
                    "title": title,
                    "level": level,
                    "length": length,
                    "limit": limit,
                }
            )
    return {"passed": not violations, "violations": violations}


def iter_node_strings(node: dict[str, Any]) -> list[tuple[str, str]]:
    fields = ["title", "description", "summary"]
    result: list[tuple[str, str]] = []
    for field in fields:
        value = node.get(field)
        if isinstance(value, str) and value:
            result.append((field, value))
    for equation in node.get("equations", []) or []:
        result.append(("equations", str(equation)))
    table = node.get("table") or {}
    for row in table.get("rows", []) or []:
        for cell in row:
            result.append(("table", str(cell)))
    for child in node.get("children", []) or []:
        if isinstance(child, dict):
            result.extend(iter_node_strings(child))
    return result


def remove_math_blocks(text: str) -> str:
    text = DISPLAY_MATH_RE.sub("", text)
    text = INLINE_MATH_RE.sub("", text)
    text = re.sub(r"\\\(.+?\\\)", "", text, flags=re.S)
    text = re.sub(r"\\\[.+?\\\]", "", text, flags=re.S)
    return text


def check_math_delimiters(root: dict[str, Any], markdown: str) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    for field, value in iter_node_strings(root):
        if field == "equations":
            continue
        if LATEX_LIKE_RE.search(remove_math_blocks(value)):
            failures.append({"field": field, "text": value[:120]})
    if LATEX_LIKE_RE.search(remove_math_blocks(markdown)):
        failures.append({"field": "mindmap.md", "text": "LaTeX-like syntax outside math delimiters"})
    return {"passed": not failures, "unwrapped_latex_like": failures}


def source_headings(source_text: str) -> list[str]:
    return [match.group(2).strip() for match in HEADING_RE.finditer(source_text)]


def section_id_from_heading(value: str) -> str:
    match = SECTION_ID_RE.match(str(value or ""))
    return match.group(1) if match else ""


def section_depth(section_id: str) -> int:
    return section_id.count(".") + 1 if section_id else 0


def flatten_nodes_with_path(node: dict[str, Any], path: list[dict[str, Any]] | None = None) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    path = list(path or [])
    current_path = path + [node]
    result = [(node, current_path)]
    for child in node.get("children", []) or []:
        if isinstance(child, dict):
            result.extend(flatten_nodes_with_path(child, current_path))
    return result


def node_section_id(node: dict[str, Any]) -> str:
    explicit = str(node.get("section_id") or "")
    if explicit:
        return explicit
    return section_id_from_heading(str(node.get("title") or ""))


def title_starts_with_section(node: dict[str, Any], section_id: str) -> bool:
    return str(node.get("title") or "").strip().startswith(section_id)


def check_section_numbering(source_text: str, root: dict[str, Any]) -> dict[str, Any]:
    headings = [(heading, section_id_from_heading(heading)) for heading in source_headings(source_text)]
    source_sections = [(heading, section_id) for heading, section_id in headings if section_id]
    node_paths = flatten_nodes_with_path(root)
    missing: list[dict[str, Any]] = []
    title_failures: list[dict[str, Any]] = []
    hierarchy_failures: list[dict[str, Any]] = []

    for heading, section_id in source_sections:
        matches = [(node, path) for node, path in node_paths if node_section_id(node) == section_id or title_starts_with_section(node, section_id)]
        if not matches:
            missing.append({"source_heading": heading, "section_id": section_id})
            continue
        for node, path in matches:
            if not title_starts_with_section(node, section_id):
                title_failures.append({"id": node.get("id"), "section_id": section_id, "title": node.get("title")})
        depth = section_depth(section_id)
        node, path = matches[0]
        render_level = len(path) - 1
        if depth == 2 and render_level != 1:
            hierarchy_failures.append({"section_id": section_id, "expected": "first-level branch", "actual_level": render_level})
        if depth >= 3:
            parent_id = ".".join(section_id.split(".")[:2])
            ancestor_ids = [node_section_id(ancestor) for ancestor in path[:-1]]
            if parent_id not in ancestor_ids:
                hierarchy_failures.append({"section_id": section_id, "expected_parent_section_id": parent_id})

    return {
        "passed": not missing and not title_failures and not hierarchy_failures,
        "source_section_count": len(source_sections),
        "missing": missing,
        "title_failures": title_failures,
        "hierarchy_failures": hierarchy_failures,
    }


def check_forbidden_section_numbers(source_text: str, root: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        section_id
        for heading in source_headings(source_text)
        for section_id in [section_id_from_heading(heading)]
        if section_id
    }
    extras: list[dict[str, Any]] = []
    for node, _path in flatten_nodes_with_path(root):
        title = str(node.get("title") or "")
        explicit = str(node.get("section_id") or "")
        candidates = [candidate for candidate in [explicit, section_id_from_heading(title)] if candidate and "." in candidate]
        for candidate in candidates:
            if candidate not in allowed:
                extras.append({"id": node.get("id"), "title": title, "section_id": candidate})
    return {"passed": not extras, "allowed": sorted(allowed), "extra": extras}


def check_no_extra_section_numbers(source_text: str, root: dict[str, Any]) -> dict[str, Any]:
    return check_forbidden_section_numbers(source_text, root)


def coverage_entries(outline: dict[str, Any], mindmap: dict[str, Any]) -> list[str]:
    entries: list[str] = []
    coverage = mindmap.get("coverage_report") or outline.get("coverage_report") or {}
    for section in coverage.get("sections", []) or []:
        entries.append(str(section.get("source") or section.get("source_heading") or ""))
        entries.append(str(section.get("node_path") or section.get("path") or ""))
    for item in outline.get("hierarchy_correspondence", []) or []:
        entries.append(str(item.get("source", "")))
        entries.append(str(item.get("outline_path", "")))
    return entries


def check_heading_coverage(source_text: str, outline: dict[str, Any], mindmap: dict[str, Any]) -> dict[str, Any]:
    headings = source_headings(source_text)
    entries = normalize_text(" ".join(coverage_entries(outline, mindmap)))
    missing = [heading for heading in headings if normalize_text(heading) not in entries]
    return {"passed": not missing, "total": len(headings), "missing": missing}


def count_source_tables(source_text: str) -> int:
    lines = source_text.splitlines()
    count = 0
    in_table = False
    for line in lines:
        is_table = line.strip().startswith("|") and line.strip().endswith("|")
        if is_table and not in_table:
            count += 1
            in_table = True
        elif not is_table:
            in_table = False
    return count


def check_tables(flat: list[tuple[dict[str, Any], int]], source_text: str) -> dict[str, Any]:
    tables = [node for node, _ in flat if node.get("type") == "table" or node.get("table")]
    invalid: list[dict[str, Any]] = []
    for node in tables:
        table = node.get("table") or {}
        columns = table.get("columns") or []
        rows = table.get("rows") or []
        bad_rows = [row for row in rows if len(row) != len(columns)]
        if not columns or not rows or bad_rows:
            invalid.append({"id": node.get("id"), "columns": len(columns), "rows": len(rows), "bad_rows": len(bad_rows)})
    source_table_count = count_source_tables(source_text)
    return {
        "passed": not invalid and len(tables) >= source_table_count,
        "tables": [node.get("id") for node in tables],
        "source_table_count": source_table_count,
        "invalid": invalid,
    }


def source_display_math(source_text: str) -> list[str]:
    return [match.group(1).strip() for match in DISPLAY_MATH_RE.finditer(source_text)]


def check_formula_coverage(root: dict[str, Any], source_text: str) -> dict[str, Any]:
    source_formulas = source_display_math(source_text)
    node_equations = [value for field, value in iter_node_strings(root) if field == "equations"]
    return {
        "passed": len(node_equations) >= len(source_formulas),
        "source_display_formula_count": len(source_formulas),
        "node_equation_count": len(node_equations),
    }


def source_images(source_text: str) -> list[dict[str, str]]:
    return [{"alt": match.group(1), "path": match.group(2)} for match in IMAGE_RE.finditer(source_text)]


def image_key_values(item: dict[str, Any]) -> list[str]:
    values = [str(item.get(key, "")) for key in ("id", "source_id", "path", "source_path", "source")]
    return [value for value in values if value]


def image_key_matches(image: dict[str, str], values: list[str]) -> bool:
    image_path = image["path"]
    image_name = Path(image_path).name
    return any(image_path in value or image_name in value for value in values)


def check_image_decisions(source_text: str, outline: dict[str, Any], mindmap: dict[str, Any]) -> dict[str, Any]:
    images = source_images(source_text)
    figure_values: list[str] = []
    for item in (outline.get("figure_decisions") or []) + (mindmap.get("figure_decisions") or []):
        if isinstance(item, dict):
            figure_values.extend(image_key_values(item))

    coverage_values: list[str] = []
    coverage = mindmap.get("coverage_report") or outline.get("coverage_report") or {}
    for bucket in ("figures", "omitted"):
        for item in coverage.get(bucket, []) or []:
            if isinstance(item, dict):
                coverage_values.extend(image_key_values(item))

    decision_missing = [image for image in images if not image_key_matches(image, figure_values)]
    coverage_missing = [image for image in images if not image_key_matches(image, coverage_values)]
    missing = {"figure_decisions": decision_missing, "coverage_report": coverage_missing}
    return {
        "passed": not decision_missing and not coverage_missing,
        "source_image_count": len(images),
        "decision_missing": decision_missing,
        "coverage_missing": coverage_missing,
        "missing": missing,
    }


def check_figure_decision_values(outline: dict[str, Any], mindmap: dict[str, Any], project_path: Path) -> dict[str, Any]:
    invalid: list[dict[str, Any]] = []
    crop_missing: list[dict[str, Any]] = []
    decisions = [item for item in mindmap.get("figure_decisions", []) or [] if isinstance(item, dict)]
    if not decisions:
        decisions = [item for item in outline.get("figure_decisions", []) or [] if isinstance(item, dict)]
    seen: set[tuple[str, str]] = set()
    for item in decisions:
        source_id = str(item.get("source_id") or item.get("id") or "")
        decision = str(item.get("decision") or item.get("effective_decision") or "")
        key = (source_id, decision)
        if key in seen:
            continue
        seen.add(key)
        if decision not in ALLOWED_FIGURE_DECISIONS:
            invalid.append({"source_id": source_id, "decision": decision})
        if decision == "preserve_crop":
            crop_path = str(item.get("crop_path") or "")
            if not crop_path:
                crop_missing.append({"source_id": source_id, "reason": "crop_path missing"})
            else:
                absolute = Path(crop_path)
                if not absolute.is_absolute():
                    absolute = project_path / absolute
                if not absolute.exists():
                    crop_missing.append({"source_id": source_id, "crop_path": crop_path, "reason": "crop file missing"})
    return {
        "passed": not invalid and not crop_missing,
        "allowed": sorted(ALLOWED_FIGURE_DECISIONS),
        "legacy_disallowed": sorted(LEGACY_FIGURE_DECISIONS),
        "invalid": invalid,
        "crop_missing": crop_missing,
    }


def check_crop_metadata(mindmap: dict[str, Any], project_path: Path) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    for item in mindmap.get("figure_decisions", []) or []:
        if not isinstance(item, dict) or item.get("decision") != "preserve_crop":
            continue
        missing = [
            field
            for field in ("crop_box", "crop_path", "crop_source_id")
            if not item.get(field)
        ]
        if not (item.get("crop_focus") or item.get("crop_reason")):
            missing.append("crop_focus_or_reason")
        crop_path = str(item.get("crop_path") or "")
        if crop_path:
            absolute = Path(crop_path)
            if not absolute.is_absolute():
                absolute = project_path / absolute
            if not absolute.exists():
                missing.append("crop_file")
        if missing:
            failures.append({"source_id": item.get("source_id"), "missing": missing})
    return {"passed": not failures, "failures": failures}


def check_image_callout_grounding(mindmap: dict[str, Any], source_text: str) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    checked = 0
    for item in mindmap.get("figure_decisions", []) or []:
        if not isinstance(item, dict):
            continue
        decision = str(item.get("decision") or "")
        if decision == "omit":
            continue
        callouts = item.get("callouts") or []
        if not callouts:
            failures.append({"source_id": item.get("source_id"), "reason": "missing callouts"})
            continue
        for callout in callouts[:2]:
            if not isinstance(callout, dict):
                failures.append({"source_id": item.get("source_id"), "reason": "invalid callout"})
                continue
            quote = str(callout.get("source_quote") or "")
            text = str(callout.get("text") or "")
            checked += 1
            if not quote or not text:
                failures.append({"source_id": item.get("source_id"), "callout": text, "reason": "missing text or source_quote"})
            elif source_text and not source_quote_found(quote, source_text):
                failures.append({"source_id": item.get("source_id"), "callout": text, "source_quote": quote, "reason": "source_quote not found"})
    return {"passed": not failures, "checked": checked, "failures": failures}


def image_dimensions_for_decision(item: dict[str, Any], project_path: Path) -> tuple[int, int] | None:
    path_text = str(item.get("crop_path") or item.get("source_path") or "")
    if not path_text:
        return None
    path = Path(path_text)
    absolute = path if path.is_absolute() else project_path / path
    if not absolute.exists() or Image is None:
        return None
    try:
        with Image.open(absolute) as image:
            return image.width, image.height
    except Exception:
        return None


def check_image_readability_static(mindmap: dict[str, Any], project_path: Path) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    checked = 0
    for item in mindmap.get("figure_decisions", []) or []:
        if not isinstance(item, dict):
            continue
        decision = str(item.get("decision") or "")
        if decision not in {"preserve_full", "preserve_crop", "redraw_high_fidelity", "redraw_concept"}:
            continue
        checked += 1
        min_width = int(item.get("min_render_width") or 170)
        min_height = int(item.get("min_render_height") or 96)
        if decision.startswith("redraw"):
            continue
        dimensions = image_dimensions_for_decision(item, project_path)
        if not dimensions:
            failures.append({"source_id": item.get("source_id"), "reason": "image dimensions unavailable"})
            continue
        width, height = dimensions
        if width < min_width or height < min_height:
            failures.append(
                {
                    "source_id": item.get("source_id"),
                    "decision": decision,
                    "width": width,
                    "height": height,
                    "min_width": min_width,
                    "min_height": min_height,
                }
            )
    return {"passed": not failures, "mode": "static_asset_dimensions", "checked": checked, "failures": failures}


def check_image_readability_browser(browser: dict[str, Any]) -> dict[str, Any]:
    items = browser.get("imageReadability") or []
    failures = [
        item for item in items
        if item.get("width", 0) < item.get("minWidth", 0) or item.get("height", 0) < item.get("minHeight", 0)
    ]
    return {"passed": not failures, "mode": "browser_rendered_size", "checked": len(items), "failures": failures}


def markdown_images(markdown: str, exports_dir: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for match in IMAGE_RE.finditer(markdown):
        path_text = match.group(2)
        path = Path(path_text)
        absolute = path if path.is_absolute() else exports_dir / path
        item = {"alt": match.group(1), "path": str(absolute), "exists": absolute.exists()}
        if absolute.exists() and Image is not None:
            try:
                with Image.open(absolute) as image:
                    item["width"], item["height"] = image.size
            except Exception as exc:  # pragma: no cover - corrupt file branch
                item["error"] = str(exc)
        result.append(item)
    return result


def check_rendered_images(markdown: str, exports_dir: Path) -> dict[str, Any]:
    images = markdown_images(markdown, exports_dir)
    failures = [image for image in images if not image.get("alt") or not image.get("exists")]
    return {"passed": not failures, "images": images, "failures": failures}


def as_image_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        images = payload.get("images", [])
    else:
        images = payload
    return [item for item in images if isinstance(item, dict)]


def truthy(value: Any) -> bool:
    return value is True or str(value).lower() in {"true", "1", "yes"}


def image_asset_kind(asset: dict[str, Any]) -> str:
    return str(asset.get("type") or asset.get("figure_kind") or asset.get("kind") or "").lower()


def blocked_embed_asset(asset: dict[str, Any]) -> bool:
    if str(asset.get("decision_hint") or "") in {"preserve", "preserve_full"} and image_asset_kind(asset) == "data_chart":
        return False
    return image_asset_kind(asset) in SCREENSHOT_EMBED_BLOCK_TYPES or truthy(asset.get("redraw_required"))


def image_asset_matches_src(asset: dict[str, Any], src: str) -> bool:
    asset_path = str(asset.get("path") or asset.get("source_path") or "").replace("\\", "/")
    if not asset_path:
        return False
    src_norm = src.replace("\\", "/")
    return src_norm.endswith(asset_path) or Path(src_norm).name == Path(asset_path).name


def embedded_image_sources(markdown: str, html_text: str) -> list[dict[str, str]]:
    sources = [{"surface": "mindmap.md", "src": match.group(2)} for match in IMAGE_RE.finditer(markdown)]
    sources.extend({"surface": "html", "src": match.group(1)} for match in HTML_IMG_RE.finditer(html_text))
    return sources


def check_source_image_policy(
    markdown: str,
    html_text: str,
    outline: dict[str, Any],
    mindmap: dict[str, Any],
    images_index: Any,
) -> dict[str, Any]:
    assets = as_image_list(images_index)
    assets_by_id = {str(item.get("id")): item for item in assets if item.get("id")}
    figure_ids: set[str] = set()
    for item in (outline.get("figure_decisions") or []) + (mindmap.get("figure_decisions") or []):
        if isinstance(item, dict):
            source_id = str(item.get("source_id") or item.get("id") or "")
            if source_id:
                figure_ids.add(source_id)

    metadata_missing: list[dict[str, Any]] = []
    for source_id in sorted(figure_ids):
        asset = assets_by_id.get(source_id)
        if not asset:
            metadata_missing.append({"source_id": source_id, "missing": "asset index entry"})
            continue
        missing_fields = [field for field in ("type", "redraw_required") if field not in asset]
        if missing_fields:
            metadata_missing.append({"source_id": source_id, "missing": missing_fields})

    violations: list[dict[str, Any]] = []
    for source in embedded_image_sources(markdown, html_text):
        asset = next((item for item in assets if image_asset_matches_src(item, source["src"])), None)
        if asset and blocked_embed_asset(asset):
            violations.append(
                {
                    "surface": source["surface"],
                    "src": source["src"],
                    "source_id": asset.get("id"),
                    "type": image_asset_kind(asset),
                    "redraw_required": asset.get("redraw_required"),
                }
            )

    return {
        "passed": not violations and not metadata_missing,
        "blocked_embeds": violations,
        "metadata_missing": metadata_missing,
        "checked_assets": len(assets),
    }


def svg_signature(svg_inner: str) -> dict[str, Any]:
    paths = SVG_PATH_D_RE.findall(svg_inner)
    d_joined = "|".join(re.sub(r"\s+", " ", path.strip()) for path in paths)
    commands = "".join(SVG_COMMAND_RE.findall(d_joined))
    return {
        "path_count": len(paths),
        "d_length": len(d_joined),
        "commands": commands,
        "normalized": re.sub(r"[-+]?\d+(?:\.\d+)?", "N", d_joined),
    }


def signatures_too_similar(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if not left["path_count"] or not right["path_count"]:
        return False
    if left["normalized"] and left["normalized"] == right["normalized"]:
        return True
    path_close = abs(left["path_count"] - right["path_count"]) <= 1
    length_close = abs(left["d_length"] - right["d_length"]) <= max(12, min(left["d_length"], right["d_length"]) * 0.08)
    commands_match = left["commands"] == right["commands"]
    return path_close and length_close and commands_match


def check_placeholder_curve_detection(html_text: str) -> dict[str, Any]:
    signatures: list[dict[str, Any]] = []
    for match in SVG_BLOCK_RE.finditer(html_text):
        svg_text = match.group(0)
        if "balanced-live-connectors" in svg_text:
            continue
        if "data-template-id" not in html_text[max(0, match.start() - 240) : match.start()]:
            continue
        signature = svg_signature(match.group(1))
        signature["start"] = match.start()
        signatures.append(signature)

    similar_pairs: list[dict[str, Any]] = []
    for index, left in enumerate(signatures):
        for right_index, right in enumerate(signatures[index + 1 :], start=index + 1):
            if signatures_too_similar(left, right):
                similar_pairs.append({"left": index, "right": right_index, "path_count": left["path_count"]})
    return {
        "passed": not similar_pairs,
        "inline_template_svg_count": len(signatures),
        "similar_pairs": similar_pairs,
    }


def first_level_branch_ids(root: dict[str, Any]) -> list[str]:
    return [str(node.get("id")) for node in root.get("children", []) or [] if isinstance(node, dict) and node.get("id")]


def check_layout_profile(mindmap: dict[str, Any], root: dict[str, Any]) -> dict[str, Any]:
    profile = mindmap.get("layout_profile") or {}
    mode = profile.get("mode")
    density_score = profile.get("density_score")
    branch_weights = profile.get("branch_weights") or []
    branch_ids = set(first_level_branch_ids(root))
    covered_ids = {
        str(item.get("node_id"))
        for item in branch_weights
        if isinstance(item, dict) and item.get("node_id")
    }
    missing = sorted(branch_ids - covered_ids)
    invalid_sides = []
    for item in branch_weights:
        if not isinstance(item, dict):
            continue
        side = str(item.get("side") or "")
        if mode == "balanced_two_sided" and side not in {"left", "right"}:
            invalid_sides.append({"node_id": item.get("node_id"), "side": side})
        if mode in {"vertical", "compact_radial"} and side not in {"center", ""}:
            invalid_sides.append({"node_id": item.get("node_id"), "side": side})
    passed = mode in LAYOUT_MODES and density_score is not None and not missing and not invalid_sides
    return {
        "passed": passed,
        "mode": mode,
        "density_score": density_score,
        "branch_count": len(branch_ids),
        "covered_branch_count": len(covered_ids),
        "missing_branch_weights": missing,
        "invalid_sides": invalid_sides,
    }


def read_svg_dimensions(svg_path: Path) -> tuple[int, int] | None:
    if not svg_path.exists():
        return None
    text = svg_path.read_text(encoding="utf-8", errors="replace")[:5000]
    match = SVG_SIZE_RE.search(text)
    if match:
        width = float(match.group(1) or match.group(4) or 0)
        height = float(match.group(2) or match.group(3) or 0)
        if width > 0 and height > 0:
            return int(round(width)), int(round(height))
    viewbox = SVG_VIEWBOX_RE.search(text)
    if viewbox:
        width = float(viewbox.group(1))
        height = float(viewbox.group(2))
        if width > 0 and height > 0:
            return int(round(width)), int(round(height))
    return None


def exported_dimensions(png_path: Path, svg_path: Path, export_report_path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if png_path.exists() and Image is not None:
        try:
            with Image.open(png_path) as image:
                result["png"] = {"width": image.width, "height": image.height}
        except Exception as exc:  # pragma: no cover - corrupt file branch
            result["png_error"] = str(exc)
    svg_size = read_svg_dimensions(svg_path)
    if svg_size:
        result["svg"] = {"width": svg_size[0], "height": svg_size[1]}
    export_report = load_json(export_report_path, {})
    viewport = export_report.get("svg_viewport") if isinstance(export_report, dict) else None
    if isinstance(viewport, dict) and "svg" not in result:
        result["svg"] = {"width": viewport.get("width", 0), "height": viewport.get("height", 0)}
    return result


def check_layout_readability(mindmap: dict[str, Any], paths: dict[str, Path]) -> dict[str, Any]:
    profile = mindmap.get("layout_profile") or {}
    mode = profile.get("mode")
    dimensions = exported_dimensions(paths["png"], paths["svg"], paths["export_report"])
    aspect_failures: list[dict[str, Any]] = []
    for kind, size in dimensions.items():
        if not isinstance(size, dict):
            continue
        width = float(size.get("width") or 0)
        height = float(size.get("height") or 0)
        ratio = height / width if width else 0
        size["height_width_ratio"] = ratio
        if width > 0 and ratio > 2.2:
            aspect_failures.append({"artifact": kind, "height_width_ratio": ratio, "width": width, "height": height})

    weights = [item for item in profile.get("branch_weights", []) or [] if isinstance(item, dict)]
    left = sum(int(item.get("weight") or 0) for item in weights if item.get("side") == "left")
    right = sum(int(item.get("weight") or 0) for item in weights if item.get("side") == "right")
    total = left + right
    imbalance = abs(left - right)
    balance_passed = True
    balance_reason = ""
    if mode == "balanced_two_sided" and total > 0:
        balance_passed = imbalance <= max(8, total * 0.4)
        if not balance_passed:
            balance_reason = f"left/right weight imbalance too high: left={left}, right={right}"

    skipped = not dimensions
    return {
        "passed": not aspect_failures and balance_passed,
        "skipped": skipped,
        "dimensions": dimensions,
        "aspect_failures": aspect_failures,
        "side_weights": {"left": left, "right": right, "imbalance": imbalance},
        "balance_passed": balance_passed,
        "balance_reason": balance_reason,
    }


def check_layout_aesthetics(browser: dict[str, Any]) -> dict[str, Any]:
    if browser.get("skipped"):
        return {"passed": True, "skipped": True, "reason": browser.get("reason", "browser skipped")}
    if browser.get("layoutMode") != "balanced_two_sided":
        return {"passed": True, "skipped": True, "reason": "layout aesthetics applies to balanced poster layouts"}
    metrics = browser.get("layoutAesthetics") or {}
    failures: list[str] = []
    def num(value: Any, default: float = 0.0) -> float:
        return default if value is None else float(value)

    aspect = num(metrics.get("aspectRatio"))
    if not (1.25 <= aspect <= 1.90):
        failures.append(f"aspect ratio {aspect:.3f} is outside poster range 1.25-1.90")
    blank_ratio = num(metrics.get("blankRatio"), 1.0)
    if blank_ratio > 0.74:
        failures.append(f"blank ratio {blank_ratio:.3f} is too high")
    offset = metrics.get("rootCenterOffset") or {}
    if num(offset.get("xRatio"), 1.0) > 0.08 or num(offset.get("yRatio"), 1.0) > 0.13:
        failures.append("root card is not close enough to canvas center")
    if num(metrics.get("maxBranchDistanceRatio"), 1.0) > 0.43:
        failures.append("branch hubs are too far from the center card")
    band_ratio = num(metrics.get("bottomBandHeightRatio"))
    if band_ratio <= 0 or band_ratio > 0.15:
        failures.append(f"bottom learning band height ratio {band_ratio:.3f} is outside 0-0.15")
    return {"passed": not failures, "metrics": metrics, "failures": failures}


def active_figure_decisions(mindmap: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item for item in mindmap.get("figure_decisions", []) or []
        if isinstance(item, dict) and str(item.get("decision") or "") in (ALLOWED_FIGURE_DECISIONS - {"omit"})
    ]


def check_evidence_card_quality(mindmap: dict[str, Any], source_text: str, browser: dict[str, Any]) -> dict[str, Any]:
    rendered = {
        str(card.get("sourceId") or ""): card
        for card in browser.get("evidenceCards", []) or []
        if isinstance(card, dict)
    }
    failures: list[dict[str, Any]] = []
    for item in active_figure_decisions(mindmap):
        source_id = str(item.get("source_id") or item.get("id") or "")
        if not str(item.get("evidence_title") or "").strip():
            failures.append({"source_id": source_id, "reason": "missing evidence_title"})
        callouts = [callout for callout in item.get("callouts", []) or [] if isinstance(callout, dict)]
        if not callouts:
            failures.append({"source_id": source_id, "reason": "missing callout"})
        for callout in callouts:
            quote = str(callout.get("source_quote") or "")
            if not source_quote_found(quote, source_text):
                failures.append({"source_id": source_id, "reason": "callout source_quote not found", "source_quote": quote})
        card = rendered.get(source_id)
        if browser and not browser.get("skipped") and not card:
            failures.append({"source_id": source_id, "reason": "evidence card not rendered"})
        if card:
            if not card.get("hasEvidenceTitle"):
                failures.append({"source_id": source_id, "reason": "rendered card missing evidence title"})
            if int(card.get("calloutCount") or 0) < 1:
                failures.append({"source_id": source_id, "reason": "rendered card missing source-backed callout"})
            if not card.get("hasSourceLabel"):
                failures.append({"source_id": source_id, "reason": "rendered card missing source figure label"})
            min_width = int(item.get("min_render_width") or 0)
            min_height = int(item.get("min_render_height") or 0)
            if min_width and float(card.get("width") or 0) < min_width:
                failures.append({"source_id": source_id, "reason": "rendered evidence width below threshold", "width": card.get("width"), "min_width": min_width})
            if min_height and float(card.get("height") or 0) < min_height:
                failures.append({"source_id": source_id, "reason": "rendered evidence height below threshold", "height": card.get("height"), "min_height": min_height})
    return {"passed": not failures, "checked": len(active_figure_decisions(mindmap)), "failures": failures}


def check_bottom_learning_band(root: dict[str, Any], browser: dict[str, Any]) -> dict[str, Any]:
    if browser.get("skipped"):
        return {"passed": True, "skipped": True, "reason": browser.get("reason", "browser skipped")}
    if browser.get("layoutMode") != "balanced_two_sided":
        return {"passed": True, "skipped": True, "reason": "bottom learning band applies to balanced poster layouts"}
    expected_ids = {
        str(node.get("id"))
        for node, _ in flatten_nodes(root)
        if str(node.get("title") or "").startswith("[*]") and (node.get("derived") or node.get("grounded_hint"))
    }
    data = browser.get("bottomLearningBand") or {}
    rendered_ids = {str(item) for item in data.get("nodeIds", []) or [] if item}
    failures: list[str] = []
    if expected_ids and not data.get("present"):
        failures.append("bottom learning band is missing")
    missing = sorted(expected_ids - rendered_ids)
    if missing:
        failures.append("derived learning nodes missing from bottom band: " + ", ".join(missing))
    scattered = [item for item in data.get("scatteredEnhancements", []) or [] if item]
    if scattered:
        failures.append("derived learning nodes are scattered outside bottom band: " + ", ".join(scattered))
    height_ratio = float(data.get("heightRatio") or 0)
    if expected_ids and (height_ratio <= 0 or height_ratio > 0.15):
        failures.append(f"bottom band height ratio {height_ratio:.3f} is outside 0-0.15")
    numbered = []
    for node, _ in flatten_nodes(root):
        if str(node.get("id")) in expected_ids and section_id_from_heading(str(node.get("title") or "").replace("[*]", "").strip()):
            numbered.append(str(node.get("id")))
    if numbered:
        failures.append("derived nodes use source-style numbering: " + ", ".join(numbered))
    return {"passed": not failures, "expected_ids": sorted(expected_ids), "rendered_ids": sorted(rendered_ids), "metrics": data, "failures": failures}


def check_connector_noise(browser: dict[str, Any]) -> dict[str, Any]:
    if browser.get("skipped"):
        return {"passed": True, "skipped": True, "reason": browser.get("reason", "browser skipped")}
    if browser.get("layoutMode") != "balanced_two_sided":
        return {"passed": True, "skipped": True, "reason": "connector noise applies to balanced poster layouts"}
    metrics = browser.get("connectorMetrics") or {}
    failures: list[str] = []
    count = int(metrics.get("count") or 0)
    if browser.get("layoutMode") == "balanced_two_sided" and not count:
        failures.append("balanced poster has no connector paths")
    if count > 18:
        failures.append(f"connector count {count} is too high")
    if float(metrics.get("maxStrokeWidth") or 0) > 4.0:
        failures.append(f"connector stroke {metrics.get('maxStrokeWidth')} is too thick")
    if float(metrics.get("maxOpacity") or 0) > 0.45:
        failures.append(f"connector opacity {metrics.get('maxOpacity')} is too strong")
    if int(metrics.get("rootIntersections") or 0) > 0:
        failures.append("connector path intersects the center card body")
    return {"passed": not failures, "metrics": metrics, "failures": failures}


def check_poster_packing(browser: dict[str, Any]) -> dict[str, Any]:
    if browser.get("skipped"):
        return {"passed": True, "skipped": True, "reason": browser.get("reason", "browser skipped")}
    if browser.get("layoutMode") != "balanced_two_sided":
        return {"passed": True, "skipped": True, "reason": "poster packing applies to balanced poster layouts"}
    metrics = browser.get("layoutAesthetics") or {}
    failures: list[str] = []

    def num(key: str, default: float = 0.0) -> float:
        value = metrics.get(key)
        return default if value is None else float(value)

    aspect = num("posterAspectRatio") or num("aspectRatio")
    if not (1.45 <= aspect <= 1.90):
        failures.append(f"poster_aspect_ratio {aspect:.3f} is not close enough to 16:9 poster range")
    if num("contentBBoxRatio") < 0.72:
        failures.append(f"content_bbox_ratio {num('contentBBoxRatio'):.3f} is too low")
    if num("topBlankRatio", 1.0) > 0.04:
        failures.append(f"top_blank_ratio {num('topBlankRatio'):.3f} is too high")
    if num("edgeBlankRatio", 1.0) > 0.04:
        failures.append(f"edge_blank_ratio {num('edgeBlankRatio'):.3f} is too high")
    if num("centerVoidRatio", 1.0) > 0.16:
        failures.append(f"center_void_ratio {num('centerVoidRatio'):.3f} is too high")
    if num("blankRatio", 1.0) > 0.62:
        failures.append(f"occupied-area blank ratio {num('blankRatio'):.3f} is too high for a poster")
    return {"passed": not failures, "metrics": metrics, "failures": failures}


def check_batch_height_compactness(browser: dict[str, Any]) -> dict[str, Any]:
    if browser.get("skipped"):
        return {"passed": True, "skipped": True, "reason": browser.get("reason", "browser skipped")}
    if browser.get("layoutMode") != "balanced_two_sided":
        return {"passed": True, "skipped": True, "reason": "batch height compactness applies to balanced poster layouts"}
    metrics = browser.get("layoutAesthetics") or {}
    table_metrics = browser.get("tableMetrics") or []
    evidence_grids = browser.get("evidenceGrids") or []
    failures: list[str] = []
    left_ratio = float(metrics.get("leftBranchHeightRatio") or 0)
    if left_ratio <= 0 or left_ratio > 0.90:
        failures.append(f"left_branch_height_ratio {left_ratio:.3f} is too high")
    for table in table_metrics:
        avg_row = float(table.get("avgRowHeight") or 0)
        max_row = float(table.get("maxRowHeight") or 0)
        if avg_row > 25 or max_row > 30:
            failures.append(f"table_compactness failed: avg_row={avg_row:.1f}, max_row={max_row:.1f}")
    for grid in evidence_grids:
        if int(grid.get("cardCount") or 0) < 2:
            continue
        if float(grid.get("heightRatio") or 0) > 0.22 or float(grid.get("avgCardHeight") or 0) > 235:
            failures.append(
                "evidence_grid_compactness failed: "
                f"height_ratio={float(grid.get('heightRatio') or 0):.3f}, "
                f"avg_card_height={float(grid.get('avgCardHeight') or 0):.1f}"
            )
    return {
        "passed": not failures,
        "metrics": {
            "left_branch_height_ratio": left_ratio,
            "table_compactness": table_metrics,
            "evidence_grid_compactness": evidence_grids,
        },
        "failures": failures,
    }


def check_evidence_compactness(browser: dict[str, Any]) -> dict[str, Any]:
    if browser.get("skipped"):
        return {"passed": True, "skipped": True, "reason": browser.get("reason", "browser skipped")}
    cards = browser.get("evidenceCards") or []
    failures: list[dict[str, Any]] = []
    for card in cards:
        source_id = str(card.get("sourceId") or "")
        if not card.get("evidenceTitleVisible"):
            failures.append({"source_id": source_id, "reason": "evidence_title_visible failed"})
        if not card.get("evidenceCalloutVisible"):
            failures.append({"source_id": source_id, "reason": "evidence_callout_visible failed"})
        if float(card.get("mediaAreaRatio") or 0) < 0.24:
            failures.append({"source_id": source_id, "reason": "evidence_media_area_ratio too low", "ratio": card.get("mediaAreaRatio")})
        if float(card.get("cardHeightRatio") or 0) > 0.19 or float(card.get("cardHeight") or 0) > 245:
            failures.append(
                {
                    "source_id": source_id,
                    "reason": "evidence_card_not_too_tall failed",
                    "height": card.get("cardHeight"),
                    "height_ratio": card.get("cardHeightRatio"),
                }
            )
    return {"passed": not failures, "checked": len(cards), "cards": cards, "failures": failures}


def check_learning_band_compactness(browser: dict[str, Any]) -> dict[str, Any]:
    if browser.get("skipped"):
        return {"passed": True, "skipped": True, "reason": browser.get("reason", "browser skipped")}
    if browser.get("layoutMode") != "balanced_two_sided":
        return {"passed": True, "skipped": True, "reason": "learning band compactness applies to balanced poster layouts"}
    data = browser.get("bottomLearningBand") or {}
    failures: list[str] = []
    if int(data.get("columnCount") or 0) != 3:
        failures.append(f"learning_band_column_count is {data.get('columnCount')}, expected 3")
    if int(data.get("keywordRendered") or 0) > 10:
        failures.append(f"learning_band_keyword_limit failed: rendered {data.get('keywordRendered')} keywords")
    height_ratio = float(data.get("heightRatio") or 0)
    if height_ratio <= 0 or height_ratio > 0.15:
        failures.append(f"learning_band_height_ratio {height_ratio:.3f} is outside 0-0.15")
    return {"passed": not failures, "metrics": data, "failures": failures}


def check_source_fidelity(checks: dict[str, Any]) -> dict[str, Any]:
    required = [
        "heading_coverage",
        "section_numbering",
        "forbidden_section_numbers",
        "table_checks",
        "formula_coverage",
        "image_decisions",
        "figure_decision_values",
        "derived_node_labeling",
        "text_compression",
    ]
    failures = [name for name in required if not checks.get(name, {}).get("passed", False)]
    return {
        "passed": not failures,
        "depends_on": required,
        "failed_checks": failures,
    }


def check_tips_grounding(flat: list[tuple[dict[str, Any], int]]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    tip_pattern = re.compile(r"(tips?|takeaway|实践|调参|启示|建议|小贴士|注意事项)", re.I)
    for node, _ in flat:
        title = str(node.get("title") or "")
        is_tips = str(node.get("type") or "") == "tips" or bool(tip_pattern.search(title))
        if is_tips and not str(node.get("source_quote") or "").strip():
            failures.append({"id": node.get("id"), "title": title, "reason": "tips node requires source_quote"})
    return {"passed": not failures, "failures": failures}


def is_derived_node(node: dict[str, Any]) -> bool:
    title = str(node.get("title") or "")
    return (
        bool(node.get("derived"))
        or bool(node.get("grounded_hint"))
        or title.startswith("[*]")
        or "派生" in title
    )


def check_derived_node_labeling(root: dict[str, Any]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    for node, path in flatten_nodes_with_path(root):
        if not is_derived_node(node):
            continue
        title = str(node.get("title") or "")
        if section_id_from_heading(title.replace("[*]", "").strip()):
            failures.append({"id": node.get("id"), "title": title, "reason": "derived node must not use source-style section number"})
        if not (node.get("derived") is True or node.get("grounded_hint") is True):
            failures.append({"id": node.get("id"), "title": title, "reason": "derived node requires derived=true or grounded_hint=true"})
        if not (node.get("derived_from") or node.get("derived_from_summary")):
            failures.append({"id": node.get("id"), "title": title, "reason": "derived node requires derived_from or derived_from_summary"})
    return {"passed": not failures, "failures": failures}


def check_text_compression(root: dict[str, Any]) -> dict[str, Any]:
    half_word_failures: list[dict[str, Any]] = []
    auto_span_failures: list[dict[str, Any]] = []
    for node, path in flatten_nodes_with_path(root):
        title = str(node.get("title") or "")
        quote = str(node.get("source_quote") or "")
        if title.endswith("...") and quote:
            prefix = title[:-3]
            if quote.startswith(prefix) and len(quote) > len(prefix):
                if prefix and prefix[-1].isascii() and prefix[-1].isalnum() and quote[len(prefix)].isascii() and quote[len(prefix)].isalnum():
                    half_word_failures.append({"id": node.get("id"), "title": title, "source_quote": quote})
        if not node.get("auto_density"):
            continue
        span = node.get("source_span") or {}
        parent_span = None
        for ancestor in reversed(path[:-1]):
            if isinstance(ancestor.get("source_span"), dict):
                parent_span = ancestor["source_span"]
                break
        if not parent_span:
            auto_span_failures.append({"id": node.get("id"), "title": title, "reason": "auto node has no source_span ancestor"})
            continue
        start = int(span.get("line_start") or 0)
        end = int(span.get("line_end") or start)
        parent_start = int(parent_span.get("line_start") or 0)
        parent_end = int(parent_span.get("line_end") or parent_start)
        if start < parent_start or end > parent_end:
            auto_span_failures.append(
                {
                    "id": node.get("id"),
                    "title": title,
                    "source_span": span,
                    "parent_source_span": parent_span,
                    "reason": "auto density node crosses owning section span",
                }
            )
    failures = half_word_failures + auto_span_failures
    return {
        "passed": not failures,
        "half_word_truncation": half_word_failures,
        "auto_span_failures": auto_span_failures,
    }


def check_summary_sentences(root: dict[str, Any]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    verb_re = re.compile(r"(是|为|通过|引入|依赖|参考|产生|实现|带来|提升|克服|负责|善用|增添|更新|缩短|改善|帮助|解释|折中|取舍|形成)")
    nominal_ending_re = re.compile(r"(?:的)?(?:机制|概念|方向|能力|影响|对比)$")
    for node, path in flatten_nodes_with_path(root):
        title = str(node.get("title") or "")
        is_summary = str(node.get("type") or "") in {"summary", "note"} and re.search(r"(小结|总结|summary)", title, re.I)
        if not is_summary:
            continue
        children = [child for child in node.get("children", []) or [] if isinstance(child, dict)]
        for child in children:
            child_title = str(child.get("title") or "")
            if visible_len(child_title) < 15:
                failures.append({"id": child.get("id"), "title": child_title, "reason": "summary detail must be >= 15 visible characters"})
            elif not verb_re.search(child_title):
                failures.append({"id": child.get("id"), "title": child_title, "reason": "summary detail must contain a verb-like predicate"})
            elif nominal_ending_re.search(child_title):
                failures.append({"id": child.get("id"), "title": child_title, "reason": "summary detail must not remain a nominal phrase"})
    return {"passed": not failures, "failures": failures}


def check_keywords_rendered(root: dict[str, Any], html_text: str, source_text: str) -> dict[str, Any]:
    source_terms = [
        term
        for term in [
            "Batch Size",
            "Epoch",
            "Shuffle",
            "Noisy Gradient",
            "Local Minima",
            "Saddle Points",
            "Flat Minima",
            "Sharp Minima",
            "Momentum",
            "Gradient",
            "Loss",
            "GPU",
        ]
        if term.lower() in source_text.lower() or (term == "Saddle Points" and "saddle point" in source_text.lower())
    ]
    keyword_nodes = [node for node, _ in flatten_nodes(root) if node.get("type") == "keywords"]
    pill_count = len(re.findall(r"class=[\"'][^\"']*\bkeywords-pill\b", html_text))
    expected = min(8, len(source_terms))
    passed = bool(keyword_nodes) and pill_count >= expected
    return {
        "passed": passed,
        "source_term_count": len(source_terms),
        "expected_min_pills": expected,
        "keyword_node_count": len(keyword_nodes),
        "pill_count": pill_count,
    }


def check_h3_density(root: dict[str, Any]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    for node, path in flatten_nodes_with_path(root):
        section_id = node_section_id(node)
        if section_id.count(".") < 2:
            continue
        children = [child for child in node.get("children", []) or [] if isinstance(child, dict)]
        density = len(children)
        if node.get("equations"):
            density += len(node.get("equations", []) or [])
        if node.get("table"):
            density += len((node.get("table") or {}).get("rows", []) or [])
        if density < 4:
            failures.append({"id": node.get("id"), "section_id": section_id, "title": node.get("title"), "detail_count": density})
    return {"passed": not failures, "failures": failures}


def find_node(node_arg: str | None) -> str | None:
    if node_arg:
        return node_arg
    return os.environ.get("MIND_MASTER_NODE") or shutil.which("node")


def node_env(node_path: str | None) -> dict[str, str]:
    env = os.environ.copy()
    if "NODE_PATH" not in env:
        bundled = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "node_modules"
        if bundled.exists():
            env["NODE_PATH"] = str(bundled)
    return env


def check_browser(html_path: Path, node_path: str | None, timeout_ms: int) -> dict[str, Any]:
    node = find_node(node_path)
    if not node:
        return {"passed": False, "skipped": True, "reason": "Node.js not found for Playwright browser validation."}

    script = r"""
const { chromium } = require('playwright');
const htmlPath = process.argv[2];
const timeout = Number(process.argv[3] || 60000);
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1800, height: 1200 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', err => errors.push(err.message));
  await page.goto('file:///' + htmlPath.replace(/\\/g, '/'), { waitUntil: 'networkidle', timeout });
  await page.waitForFunction(() => {
    return window.MIND_MASTER_READY ||
      document.querySelector('.balanced-layout') ||
      document.querySelector('.markmap svg');
  }, { timeout });
  await page.waitForTimeout(5000);
    const result = await page.evaluate(() => {
    const layoutMode = document.body.dataset.layoutMode || 'vertical';
    const target = layoutMode === 'balanced_two_sided'
      ? document.querySelector('.balanced-layout')
      : document.querySelector('.markmap svg');
    const box = target ? target.getBoundingClientRect() : null;
    const layout = document.querySelector('.balanced-layout');
    const root = layout ? layout.querySelector('.balanced-root') : null;
    const bottomBand = layout ? layout.querySelector('.balanced-learning-band') : null;
    const rectObj = (rect) => rect ? ({
      left: Math.round(rect.left),
      top: Math.round(rect.top),
      right: Math.round(rect.right),
      bottom: Math.round(rect.bottom),
      width: Math.round(rect.width),
      height: Math.round(rect.height),
      cx: Math.round(rect.left + rect.width / 2),
      cy: Math.round(rect.top + rect.height / 2)
    }) : null;
    const unionRect = (elements) => {
      const rects = elements
        .map((el) => el.getBoundingClientRect())
        .filter((rect) => rect.width > 0 && rect.height > 0);
      if (!rects.length) return null;
      const left = Math.min(...rects.map((rect) => rect.left));
      const top = Math.min(...rects.map((rect) => rect.top));
      const right = Math.max(...rects.map((rect) => rect.right));
      const bottom = Math.max(...rects.map((rect) => rect.bottom));
      return { left, top, right, bottom, width: right - left, height: bottom - top };
    };
    const layoutRect = layout ? layout.getBoundingClientRect() : null;
    const rootRect = root ? root.getBoundingClientRect() : null;
    const bottomRect = bottomBand ? bottomBand.getBoundingClientRect() : null;
    const posterNodes = layout ? Array.from(layout.querySelectorAll('.balanced-root, .balanced-node, .balanced-learning-band')) : [];
    const contentRect = unionRect(posterNodes);
    const occupiedArea = posterNodes.reduce((sum, el) => {
      const r = el.getBoundingClientRect();
      return sum + Math.max(0, r.width) * Math.max(0, r.height);
    }, 0);
    const layoutArea = layoutRect ? layoutRect.width * layoutRect.height : 0;
    const leftContentRect = layout ? unionRect(Array.from(layout.querySelectorAll('.balanced-side.left .balanced-node'))) : null;
    const nonRootNodes = layout ? Array.from(layout.querySelectorAll('.balanced-side .balanced-node')) : [];
    const leftMaxRight = rootRect ? Math.max(...nonRootNodes.filter((el) => {
      const r = el.getBoundingClientRect();
      return r.right <= rootRect.left;
    }).map((el) => el.getBoundingClientRect().right), layoutRect ? layoutRect.left : 0) : 0;
    const rightMinLeft = rootRect ? Math.min(...nonRootNodes.filter((el) => {
      const r = el.getBoundingClientRect();
      return r.left >= rootRect.right;
    }).map((el) => el.getBoundingClientRect().left), layoutRect ? layoutRect.right : 0) : 0;
    const centerGap = layoutRect && rootRect ? (
      Math.max(0, rootRect.left - leftMaxRight) + Math.max(0, rightMinLeft - rootRect.right)
    ) : 0;
    const rootCenterOffset = layoutRect && rootRect ? {
      x: Math.abs((rootRect.left + rootRect.width / 2) - (layoutRect.left + layoutRect.width / 2)),
      y: Math.abs((rootRect.top + rootRect.height / 2) - (layoutRect.top + layoutRect.height / 2)),
      xRatio: Math.abs((rootRect.left + rootRect.width / 2) - (layoutRect.left + layoutRect.width / 2)) / layoutRect.width,
      yRatio: Math.abs((rootRect.top + rootRect.height / 2) - (layoutRect.top + layoutRect.height / 2)) / layoutRect.height
    } : null;
    const branchDistances = layout && rootRect ? Array.from(layout.querySelectorAll('.balanced-hub')).map((hub) => {
      const r = hub.getBoundingClientRect();
      const dx = Math.abs((r.left + r.width / 2) - (rootRect.left + rootRect.width / 2));
      const dy = Math.abs((r.top + r.height / 2) - (rootRect.top + rootRect.height / 2));
      return Math.round(Math.sqrt(dx * dx + dy * dy));
    }) : [];
    const enhancementIds = ['n_keywords', 'n_tuning_hints', 'n_momentum_advantages'];
    const scatteredEnhancements = layout ? enhancementIds.filter((id) => {
      const el = layout.querySelector(`[data-node-id="${id}"]`);
      return el && !el.closest('.balanced-learning-band');
    }) : [];
    const evidenceCards = Array.from(document.querySelectorAll('.balanced-evidence-card')).map((figure) => {
      const media = figure.querySelector('img, svg');
      const cardRect = figure.getBoundingClientRect();
      const rect = media ? media.getBoundingClientRect() : figure.getBoundingClientRect();
      const titleRect = figure.querySelector('.balanced-evidence-title')?.getBoundingClientRect();
      const calloutRect = figure.querySelector('.balanced-image-callouts')?.getBoundingClientRect();
      return {
        sourceId: figure.dataset.sourceId || '',
        kind: figure.dataset.imageKind || '',
        cardWidth: Math.round(cardRect.width),
        cardHeight: Math.round(cardRect.height),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        area: Math.round(rect.width * rect.height),
        mediaAreaRatio: cardRect.width && cardRect.height ? Number(((rect.width * rect.height) / (cardRect.width * cardRect.height)).toFixed(3)) : 0,
        cardHeightRatio: layoutRect ? Number((cardRect.height / layoutRect.height).toFixed(3)) : 0,
        hasEvidenceTitle: !!figure.querySelector('.balanced-evidence-title'),
        evidenceTitleVisible: !!titleRect && titleRect.width > 0 && titleRect.height > 0,
        calloutCount: figure.querySelectorAll('.balanced-image-callouts li[data-source-quote]').length,
        evidenceCalloutVisible: !!calloutRect && calloutRect.width > 0 && calloutRect.height > 0,
        hasSourceLabel: !!figure.querySelector('.balanced-source-label')
      };
    });
    const evidenceGrids = Array.from(document.querySelectorAll('.balanced-node.has-multiple-visuals .balanced-evidence-grid')).map((grid) => {
      const rect = grid.getBoundingClientRect();
      const cards = Array.from(grid.querySelectorAll('.balanced-evidence-card')).map((card) => card.getBoundingClientRect());
      return {
        cardCount: cards.length,
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        avgCardHeight: cards.length ? Math.round(cards.reduce((sum, card) => sum + card.height, 0) / cards.length) : 0,
        heightRatio: layoutRect ? Number((rect.height / layoutRect.height).toFixed(3)) : 0
      };
    });
    const tableMetrics = Array.from(document.querySelectorAll('.balanced-table-wrap table')).map((table) => {
      const rect = table.getBoundingClientRect();
      const rows = Array.from(table.querySelectorAll('tbody tr')).map((row) => row.getBoundingClientRect());
      const header = table.querySelector('thead tr')?.getBoundingClientRect();
      return {
        rowCount: rows.length,
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        avgRowHeight: rows.length ? Number((rows.reduce((sum, row) => sum + row.height, 0) / rows.length).toFixed(1)) : 0,
        maxRowHeight: rows.length ? Math.round(Math.max(...rows.map((row) => row.height))) : 0,
        headerHeight: header ? Math.round(header.height) : 0
      };
    });
    const connectors = Array.from(document.querySelectorAll('.balanced-live-connectors path')).map((path) => {
      const width = Number(path.getAttribute('stroke-width') || 0);
      const opacity = Number(path.getAttribute('opacity') || getComputedStyle(path).opacity || 0);
      let intersectsRoot = false;
      if (rootRect && layoutRect && path.getBBox) {
        const b = path.getBBox();
        const inner = {
          left: rootRect.left - layoutRect.left + 10,
          right: rootRect.right - layoutRect.left - 10,
          top: rootRect.top - layoutRect.top + 10,
          bottom: rootRect.bottom - layoutRect.top - 10
        };
        intersectsRoot = b.x < inner.right && b.x + b.width > inner.left && b.y < inner.bottom && b.y + b.height > inner.top;
      }
      return {
        kind: path.dataset.kind || '',
        strokeWidth: width,
        opacity,
        intersectsRoot
      };
    });
    const imageReadability = Array.from(document.querySelectorAll('[data-image-kind]')).map((figure) => {
      const media = figure.querySelector('img, svg');
      const rect = media ? media.getBoundingClientRect() : figure.getBoundingClientRect();
      return {
        sourceId: figure.dataset.sourceId || '',
        kind: figure.dataset.imageKind || '',
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        minWidth: Number(figure.dataset.minWidth || 0),
        minHeight: Number(figure.dataset.minHeight || 0)
      };
    });
    return {
      layoutMode,
      katexErrors: document.querySelectorAll('.katex-error').length,
      katexCount: document.querySelectorAll('.katex').length,
      imageCount: document.querySelectorAll('.mind-master-render image, .mind-master-render img, .balanced-layout img').length,
      connectorCount: document.querySelectorAll('.balanced-live-connectors path').length,
      svgWidth: box ? Math.round(box.width) : 0,
      svgHeight: box ? Math.round(box.height) : 0,
      textLength: document.body.innerText.length,
      imageReadability,
      layoutAesthetics: {
        layout: rectObj(layoutRect),
        root: rectObj(rootRect),
        bottomBand: rectObj(bottomRect),
        aspectRatio: layoutRect ? Number((layoutRect.width / layoutRect.height).toFixed(3)) : 0,
        posterAspectRatio: layoutRect ? Number((layoutRect.width / layoutRect.height).toFixed(3)) : 0,
        blankRatio: layoutArea ? Number(Math.max(0, 1 - Math.min(occupiedArea / layoutArea, 1)).toFixed(3)) : 1,
        contentBBox: rectObj(contentRect),
        contentBBoxRatio: layoutArea && contentRect ? Number(((contentRect.width * contentRect.height) / layoutArea).toFixed(3)) : 0,
        topBlankRatio: layoutRect && contentRect ? Number(((contentRect.top - layoutRect.top) / layoutRect.height).toFixed(3)) : 1,
        edgeBlankRatio: layoutRect && contentRect ? Number((Math.max(contentRect.left - layoutRect.left, layoutRect.right - contentRect.right) / layoutRect.width).toFixed(3)) : 1,
        centerVoidRatio: layoutRect ? Number((centerGap / layoutRect.width).toFixed(3)) : 1,
        leftBranchHeightRatio: layoutRect && leftContentRect ? Number((leftContentRect.height / layoutRect.height).toFixed(3)) : 0,
        rootCenterOffset,
        branchDistances,
        maxBranchDistance: branchDistances.length ? Math.max(...branchDistances) : 0,
        maxBranchDistanceRatio: layoutRect && branchDistances.length ? Number((Math.max(...branchDistances) / layoutRect.width).toFixed(3)) : 0,
        bottomBandHeightRatio: layoutRect && bottomRect ? Number((bottomRect.height / layoutRect.height).toFixed(3)) : 0
      },
      evidenceCards,
      evidenceGrids,
      tableMetrics,
      bottomLearningBand: {
        present: !!bottomBand,
        nodeIds: bottomBand ? Array.from(bottomBand.querySelectorAll('[data-node-id]')).map((el) => el.dataset.nodeId || '') : [],
        scatteredEnhancements,
        heightRatio: layoutRect && bottomRect ? Number((bottomRect.height / layoutRect.height).toFixed(3)) : 0,
        columnCount: bottomBand ? getComputedStyle(bottomBand).gridTemplateColumns.split(' ').filter(Boolean).length : 0,
        keywordRendered: bottomBand ? Number(bottomBand.querySelector('[data-keyword-rendered]')?.dataset.keywordRendered || 0) : 0,
        keywordTotal: bottomBand ? Number(bottomBand.querySelector('[data-keyword-total]')?.dataset.keywordTotal || 0) : 0
      },
      connectorMetrics: {
        count: connectors.length,
        maxStrokeWidth: connectors.length ? Math.max(...connectors.map(c => c.strokeWidth)) : 0,
        maxOpacity: connectors.length ? Math.max(...connectors.map(c => c.opacity)) : 0,
        rootIntersections: connectors.filter(c => c.intersectsRoot && c.kind !== 'root-branch').length,
        connectors
      }
    };
  });
  result.pageErrors = errors;
  await browser.close();
  console.log(JSON.stringify(result));
})().catch(err => {
  console.error(err.stack || err.message || String(err));
  process.exit(1);
});
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as handle:
        handle.write(script)
        script_path = handle.name
    try:
        completed = subprocess.run(
            [node, script_path, str(html_path.resolve()), str(timeout_ms)],
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env=node_env(node),
            timeout=max(timeout_ms / 1000 + 10, 20),
        )
    finally:
        Path(script_path).unlink(missing_ok=True)
    if completed.returncode != 0:
        return {"passed": False, "error": completed.stderr.strip() or completed.stdout.strip()}
    data = json.loads(completed.stdout.strip().splitlines()[-1])
    connector_ok = data.get("layoutMode") != "balanced_two_sided" or data.get("connectorCount", 0) > 0
    data["passed"] = (
        data["katexErrors"] == 0
        and data["svgWidth"] > 0
        and data["svgHeight"] > 0
        and connector_ok
        and not data["pageErrors"]
    )
    if not connector_ok:
        data["reason"] = "balanced_two_sided layout requires visible connector paths."
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate rendered Mind-Master artifacts.")
    parser.add_argument("project", type=Path, help="Mind-Master project path.")
    parser.add_argument("--section-id", help="Validate one maps/<section_id>/ workspace.")
    parser.add_argument("--skip-browser", action="store_true", help="Skip Playwright browser checks.")
    parser.add_argument("--node", help="Node.js executable for Playwright fallback.")
    parser.add_argument("--browser-timeout-ms", type=int, default=60000)
    args = parser.parse_args(argv)

    ctx = resolve_context(args)
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {}

    try:
        outline = load_json(ctx["outline"], {})
        mindmap = load_json(ctx["mindmap"])
        markdown = ctx["markdown"].read_text(encoding="utf-8")
        source_text = ctx["source"].read_text(encoding="utf-8") if ctx["source"].exists() else ""
        html_path = ctx["html"]
        html_text = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
        images_index = load_json(ctx["images_index"], [])
        root = mindmap.get("root", {})
        flat = flatten_nodes(root)

        checks["schema"] = {"passed": bool(root and mindmap.get("style") and html_path.exists()), "html": str(html_path)}
        checks["max_depth"] = {"passed": node_depth(root) <= int(outline.get("max_depth", 4)) + 1, "depth": node_depth(root), "limit": int(outline.get("max_depth", 4)) + 1}
        checks["node_length"] = check_node_lengths(flat)
        checks["source_quote"] = {
            "passed": True,
            "missing": [],
            "not_found": [],
        }
        for node, _ in flat:
            if node is root:
                continue
            leaf = not node.get("children")
            if leaf or node.get("type") in {"table", "formula", "image"}:
                quote = str(node.get("source_quote", ""))
                if not quote:
                    checks["source_quote"]["missing"].append(node.get("id"))
                elif source_text and not source_quote_found(quote, source_text):
                    checks["source_quote"]["not_found"].append({"id": node.get("id"), "source_quote": quote})
        checks["source_quote"]["passed"] = not checks["source_quote"]["missing"] and not checks["source_quote"]["not_found"]

        checks["heading_coverage"] = check_heading_coverage(source_text, outline, mindmap) if source_text else {"passed": True, "skipped": True}
        checks["section_numbering"] = check_section_numbering(source_text, root) if source_text else {"passed": True, "skipped": True}
        checks["forbidden_section_numbers"] = check_forbidden_section_numbers(source_text, root) if source_text else {"passed": True, "skipped": True}
        checks["no_extra_section_numbers"] = checks["forbidden_section_numbers"]
        checks["table_checks"] = check_tables(flat, source_text)
        checks["formula_coverage"] = check_formula_coverage(root, source_text)
        checks["math_delimiter_checks"] = check_math_delimiters(root, markdown)
        checks["image_decisions"] = check_image_decisions(source_text, outline, mindmap) if source_text else {"passed": True, "skipped": True}
        checks["figure_decision_values"] = check_figure_decision_values(outline, mindmap, ctx["project"])
        checks["crop_metadata"] = check_crop_metadata(mindmap, ctx["project"])
        checks["image_callout_grounding"] = check_image_callout_grounding(mindmap, source_text)
        checks["image_readability"] = check_image_readability_static(mindmap, ctx["project"])
        checks["rendered_images"] = check_rendered_images(markdown, ctx["exports"])
        checks["source_image_policy"] = check_source_image_policy(markdown, html_text, outline, mindmap, images_index)
        checks["placeholder_curve_detection"] = check_placeholder_curve_detection(html_text)
        checks["layout_profile_checks"] = check_layout_profile(mindmap, root)
        checks["layout_readability"] = check_layout_readability(mindmap, ctx)
        if checks["layout_readability"].get("skipped"):
            warnings.append("Layout readability export ratio check skipped because PNG/SVG exports are not present yet.")
        checks["tips_grounding"] = check_tips_grounding(flat)
        checks["derived_node_labeling"] = check_derived_node_labeling(root)
        checks["text_compression"] = check_text_compression(root)
        checks["source_fidelity"] = check_source_fidelity(checks)
        checks["summary_sentence_checks"] = check_summary_sentences(root)
        checks["keywords_rendered"] = check_keywords_rendered(root, html_text, source_text)
        checks["h3_density"] = check_h3_density(root)
        if args.skip_browser:
            checks["browser"] = {"passed": True, "skipped": True}
            warnings.append("Browser validation skipped by --skip-browser.")
        else:
            checks["browser"] = check_browser(html_path, args.node, args.browser_timeout_ms)
            if checks["browser"].get("imageReadability") is not None:
                checks["image_readability"] = check_image_readability_browser(checks["browser"])
            if (
                checks["formula_coverage"].get("source_display_formula_count", 0) > 0
                and not checks["browser"].get("skipped")
                and checks["browser"].get("katexCount", 0) < 1
            ):
                checks["browser"]["passed"] = False
                checks["browser"]["reason"] = "Source contains display formulas but rendered HTML has no KaTeX nodes."
            if checks["browser"].get("skipped"):
                warnings.append(str(checks["browser"].get("reason", "Browser validation skipped.")))

        checks["layout_aesthetics"] = check_layout_aesthetics(checks["browser"])
        checks["evidence_card_quality"] = check_evidence_card_quality(mindmap, source_text, checks["browser"])
        checks["bottom_learning_band"] = check_bottom_learning_band(root, checks["browser"])
        checks["connector_noise"] = check_connector_noise(checks["browser"])
        checks["poster_packing"] = check_poster_packing(checks["browser"])
        checks["batch_height_compactness"] = check_batch_height_compactness(checks["browser"])
        checks["evidence_compactness"] = check_evidence_compactness(checks["browser"])
        checks["learning_band_compactness"] = check_learning_band_compactness(checks["browser"])

        for name, check in checks.items():
            if isinstance(check, dict) and not check.get("passed", False):
                errors.append(f"{name} failed")
    except Exception as exc:
        errors.append(str(exc))

    report = {
        "passed": not errors,
        "project": ctx["project"].name,
        "section_id": args.section_id,
        "checked_at": utc_now(),
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
    }
    write_json(ctx["validation"], report)

    if errors:
        print("GATE 7 ❌ Formula and image validation failed.")
        print(f"- validation report: {project_relative(ctx['project'], ctx['validation'])}")
        for error in errors:
            print(f"- ERROR: {error}")
        return 1

    print("GATE 7 ✅ Formula and image validation passed.")
    print("Deliverables:")
    print(f"- validation report: {project_relative(ctx['project'], ctx['validation'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

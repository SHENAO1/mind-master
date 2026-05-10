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

try:
    from PIL import Image, ImageChops
except ImportError:  # pragma: no cover - surfaced as an omit fallback for crop_preserve
    Image = None  # type: ignore[assignment]
    ImageChops = None  # type: ignore[assignment]

try:  # Keep checkpoint symbols printable on Windows consoles.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:  # pragma: no cover
    pass


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_PATH = SKILL_DIR / "templates" / "markmap.html"
SVG_TEMPLATE_DIR = SKILL_DIR / "assets" / "svg_templates"
MATH_DELIMITER_RE = re.compile(r"^\s*(?:\$.*\$\s*|\$\$.*\$\$\s*|\\\(.*\\\)\s*|\\\[.*\\\]\s*)$", re.S)
SECTION_ID_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\s*(.*)$")
LAYOUT_MODES = {"vertical", "balanced_two_sided", "compact_radial"}
FINAL_IMAGE_DECISIONS = {"preserve_full", "preserve_crop", "redraw_high_fidelity", "redraw_concept", "omit"}
PRESERVE_IMAGE_DECISIONS = {"preserve_full", "preserve", "image", "embed_source", "keep"}
CROP_IMAGE_DECISIONS = {"preserve_crop", "crop_preserve", "crop", "crop-preserve"}
REDRAW_IMAGE_DECISIONS = {"redraw_high_fidelity", "redraw_concept", "redraw", "redraw_svg"}
IMAGE_LAYOUT_DECISIONS = (FINAL_IMAGE_DECISIONS - {"omit"}) | PRESERVE_IMAGE_DECISIONS | CROP_IMAGE_DECISIONS | REDRAW_IMAGE_DECISIONS
SCREENSHOT_EMBED_BLOCK_TYPES = {"screenshot", "slide", "photo"}
REGISTERED_TEMPLATES = {
    "loss_landscape_sharp_vs_flat": SVG_TEMPLATE_DIR / "loss_landscape_sharp_vs_flat.svg",
    "gradient_vs_momentum_vector": SVG_TEMPLATE_DIR / "gradient_vs_momentum_vector.svg",
    "batch_size_update_comparison": SVG_TEMPLATE_DIR / "batch_size_update_comparison.svg",
}
NODE_TYPE_WEIGHTS = {"table": 3, "formula": 2, "image": 3}
BRANCH_COLORS = ["#2563d8", "#17813b", "#f97316", "#7c3aed", "#be185d", "#0f766e"]
LESSON05_CALLOUTS = {
    "fig_p32_003": [
        {
            "text": "Full Batch 处理完 20 笔才更新一次",
            "source_quote": "左图所示模型必须把这 20 笔训练数据全部处理完，才能计算一次Loss及梯度",
        },
        {
            "text": "Batch=1 在单个 Epoch 中更新 20 次",
            "source_quote": "如果总共有 20 批资料，那么在每一在单个 Epoch 中参数会更新 20 次",
        },
    ],
    "fig_p38_004": [
        {
            "text": "大 Batch 在单个 Epoch 上更快",
            "source_quote": "在一个 Epoch 中，较大的 Batch Size 反而能缩短训练时间",
        },
        {
            "text": "1~1000 单次更新时间近似相同",
            "source_quote": "Batch Size 的范围是 1~1000，所需的时间几乎是一样的",
        },
    ],
    "fig_p46_006": [
        {
            "text": "Small Batch 更倾向 Flat Minima",
            "source_quote": "小 Batch 倾向于引导模型走到平坦的极小值区域（Flat Minima）",
        },
        {
            "text": "Flat Minima 对测试集更稳健",
            "source_quote": "平坦区域具有更强的鲁棒性，从而提升泛化能力",
        },
    ],
    "fig_p56_007": [
        {
            "text": "惯性帮助越过平坦洼地或鞍点",
            "source_quote": "即便遇到平坦的洼地或鞍点，由于“惯性”的存在，球依然有动量冲过去",
        }
    ],
    "fig_p63_008": [
        {
            "text": "Momentum 结合历史方向与当前梯度",
            "source_quote": "Momentum 会将“前一次的更新方向”与“当前梯度”加权求和",
        },
        {
            "text": "动量积累能冲出微小局部最优",
            "source_quote": "借助积累的动量“冲”出去",
        },
    ],
}
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


def source_image_absolute(project_path: Path, image_path: str) -> Path:
    raw = Path(image_path)
    return raw if raw.is_absolute() else project_path / raw


def clamp_crop_box(crop_box: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int] | None:
    left, top, right, bottom = crop_box
    left = max(0, min(width - 1, left))
    top = max(0, min(height - 1, top))
    right = max(left + 1, min(width, right))
    bottom = max(top + 1, min(height, bottom))
    if right - left < 20 or bottom - top < 20:
        return None
    return left, top, right, bottom


def parse_crop_box(value: Any, width: int, height: int) -> tuple[int, int, int, int] | None:
    if isinstance(value, dict):
        left = int(value.get("left", value.get("x", 0)) or 0)
        top = int(value.get("top", value.get("y", 0)) or 0)
        if "right" in value or "bottom" in value:
            right = int(value.get("right", width) or width)
            bottom = int(value.get("bottom", height) or height)
        else:
            right = left + int(value.get("width", width - left) or width - left)
            bottom = top + int(value.get("height", height - top) or height - top)
        return clamp_crop_box((left, top, right, bottom), width, height)
    if isinstance(value, (list, tuple)) and len(value) == 4:
        return clamp_crop_box(tuple(int(float(part)) for part in value), width, height)
    return None


def auto_trim_box(image: Any) -> tuple[int, int, int, int] | None:
    if ImageChops is None:
        return None
    background = Image.new(image.mode, image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, background)
    bbox = diff.getbbox()
    if not bbox:
        return None
    left, top, right, bottom = bbox
    pad = 12
    return clamp_crop_box((left - pad, top - pad, right + pad, bottom + pad), image.width, image.height)


def crop_image_for_visual(project_path: Path, raw: dict[str, Any], asset: dict[str, Any], source_id: str) -> str:
    if Image is None:
        return ""
    image_path = raw.get("path") or asset.get("path")
    if not image_path:
        return ""
    absolute = source_image_absolute(project_path, str(image_path))
    if not absolute.exists():
        return ""
    crops_dir = project_path / "assets" / "images" / "crops"
    crops_dir.mkdir(parents=True, exist_ok=True)
    crop_path = crops_dir / f"{source_id}_crop.png"
    with Image.open(absolute) as image:
        working = image.convert("RGBA")
        crop_box = parse_crop_box(raw.get("crop_box") or asset.get("crop_box"), working.width, working.height)
        if not crop_box:
            crop_box = auto_trim_box(working) or (0, 0, working.width, working.height)
        working.crop(crop_box).save(crop_path)
        raw["crop_box"] = list(crop_box)
    raw["crop_path"] = project_relative(project_path, crop_path)
    raw["crop_source_id"] = source_id
    raw.setdefault("crop_focus", raw.get("reason") or asset.get("decision_hint_reason") or "focus on the source-backed visual evidence")
    raw.setdefault("crop_reason", raw["crop_focus"])
    return raw["crop_path"]


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


def truthy(value: Any) -> bool:
    return value is True or str(value).lower() in {"true", "1", "yes"}


def asset_kind(raw: dict[str, Any], asset: dict[str, Any]) -> str:
    return str(
        raw.get("type")
        or asset.get("type")
        or raw.get("figure_kind")
        or asset.get("figure_kind")
        or raw.get("kind")
        or asset.get("kind")
        or ""
    ).lower()


def visual_source_id(raw: dict[str, Any]) -> str:
    return str(raw.get("id") or raw.get("source_id") or "")


def template_path(template_id: str) -> Path | None:
    path = REGISTERED_TEMPLATES.get(template_id)
    if path and path.exists():
        return path
    return None


def template_id_for(raw: dict[str, Any], asset: dict[str, Any]) -> str:
    explicit = str(raw.get("redraw_template_id") or raw.get("template_id") or asset.get("redraw_template_id") or "").strip()
    if explicit:
        return explicit
    hint = str(raw.get("decision_hint") or asset.get("decision_hint") or "")
    if hint.startswith(("redraw:", "redraw_high_fidelity:", "redraw_concept:")):
        return hint.split(":", 1)[1].strip()
    return ""


def effective_visual_decision(raw: dict[str, Any], asset: dict[str, Any]) -> tuple[str, str]:
    """Return one of the five final visual decisions and optional template id."""
    decision = str(raw.get("decision") or "").lower()
    hint = str(raw.get("decision_hint") or asset.get("decision_hint") or "").lower()
    template_id = template_id_for(raw, asset)

    if decision in {"omitted", "omit", "no image"}:
        return "omit", ""
    if decision in FINAL_IMAGE_DECISIONS:
        if decision.startswith("redraw") and template_id and template_path(template_id):
            return decision, template_id
        if not decision.startswith("redraw"):
            return decision, ""
        return "omit", ""
    if hint in FINAL_IMAGE_DECISIONS:
        if hint.startswith("redraw") and template_id and template_path(template_id):
            return hint, template_id
        if not hint.startswith("redraw"):
            return hint, ""
        return "omit", ""
    if decision in CROP_IMAGE_DECISIONS or hint in CROP_IMAGE_DECISIONS:
        return "preserve_crop", ""
    if hint == "preserve" or asset_kind(raw, asset) == "data_chart":
        return "preserve_full", ""
    if decision in {"preserve", "image", "embed_source", "keep", "crop"}:
        if template_id and template_path(template_id):
            return "redraw_concept", template_id
        if asset_kind(raw, asset) == "data_chart":
            return "preserve_full", ""
        return "omit", ""
    if decision in {"redraw", "redraw_svg"}:
        if template_id and template_path(template_id):
            fidelity = str(raw.get("redraw_fidelity") or asset.get("redraw_fidelity") or "").lower()
            return ("redraw_high_fidelity" if fidelity == "high" else "redraw_concept"), template_id
        return "omit", ""
    if hint.startswith(("redraw_high_fidelity:", "redraw_high_fidelity")) and template_id and template_path(template_id):
        return "redraw_high_fidelity", template_id
    if hint.startswith(("redraw_concept:", "redraw:", "redraw_concept")) and template_id and template_path(template_id):
        return "redraw_concept", template_id
    return "omit", ""


def redraw_instruction(raw: dict[str, Any], asset: dict[str, Any]) -> str:
    return str(
        raw.get("redraw_instruction")
        or raw.get("semantic_description")
        or raw.get("reason")
        or asset.get("redraw_instruction")
        or asset.get("caption")
        or asset.get("alt")
        or "Use a registered SVG template for this source visual."
    )


def source_id_from(raw: dict[str, Any]) -> str:
    return str(raw.get("source_id") or raw.get("id") or "")


def ensure_visual_callouts(raw: dict[str, Any], asset: dict[str, Any]) -> list[dict[str, str]]:
    existing = raw.get("callouts") or raw.get("image_callouts") or asset.get("callouts") or []
    normalized: list[dict[str, str]] = []
    if isinstance(existing, str):
        existing = [{"text": existing, "source_quote": raw.get("source_quote") or asset.get("source_context") or ""}]
    for item in existing:
        if isinstance(item, str):
            item = {"text": item, "source_quote": item}
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("title") or item.get("summary") or "").strip()
        quote = str(item.get("source_quote") or item.get("quote") or text).strip()
        if text and quote:
            normalized.append({"text": text, "source_quote": quote})
    if not normalized:
        normalized.extend(LESSON05_CALLOUTS.get(source_id_from(raw), []))
    raw["callouts"] = normalized[:2]
    return raw["callouts"]


def readability_tier_for(source_id: str, decision: str, raw: dict[str, Any], asset: dict[str, Any]) -> str:
    explicit = str(raw.get("readability_tier") or asset.get("readability_tier") or "").strip().lower()
    if explicit:
        return explicit
    text = " ".join(
        str(value)
        for value in [
            source_id,
            raw.get("alt"),
            asset.get("alt"),
            raw.get("reason"),
            asset.get("source_context"),
        ]
        if value
    ).lower()
    if source_id in {"fig_p38_004", "fig_p46_006", "fig_p56_007", "fig_p63_008"}:
        return "dense"
    if re.search(r"(formula|公式|axis|坐标|gradient|movement|箭头|曲线|plot|chart|loss)", text):
        return "dense"
    if decision.startswith("redraw"):
        return "medium"
    return "standard"


def readability_threshold(tier: str, decision: str) -> tuple[int, int]:
    if tier == "dense":
        return (230, 135) if decision.startswith("preserve") else (210, 120)
    if tier == "medium":
        return 200, 115
    return 170, 96


def apply_image_policy(outline: dict[str, Any], images_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Normalize figure decisions according to the five-way learning image policy."""
    report = {
        "preserve_full": [],
        "preserve_crop": [],
        "redraw_high_fidelity": [],
        "redraw_concept": [],
        "omit": [],
        "redraw_template_missing": [],
    }
    for item in outline.get("figure_decisions", []) or []:
        if not isinstance(item, dict):
            continue
        source_id = source_id_from(item)
        asset = images_by_id.get(source_id, {})
        original_decision = str(item.get("decision") or "")
        effective, template_id = effective_visual_decision(item, asset)
        if original_decision and original_decision != effective:
            item.setdefault("original_decision", original_decision)
        item["decision"] = effective
        item["effective_decision"] = effective
        item["type"] = asset_kind(item, asset) or str(asset.get("type") or "unknown")
        item["decision_hint"] = item.get("decision_hint") or asset.get("decision_hint") or "omit"
        tier = readability_tier_for(source_id, effective, item, asset)
        min_width, min_height = readability_threshold(tier, effective)
        item["readability_tier"] = tier
        item["min_render_width"] = min_width
        item["min_render_height"] = min_height
        if effective in {"preserve_full", "preserve_crop", "redraw_high_fidelity", "redraw_concept"}:
            ensure_visual_callouts(item, asset)
        if effective == "preserve_full":
            item["redraw_required"] = False
            report["preserve_full"].append(source_id)
        elif effective == "preserve_crop":
            item["redraw_required"] = False
            item["decision"] = "preserve_crop"
            item["effective_decision"] = "preserve_crop"
            item.setdefault("crop_focus", item.get("reason") or asset.get("decision_hint_reason") or "focus on the evidence-bearing region")
            report["preserve_crop"].append(source_id)
        elif effective in {"redraw_high_fidelity", "redraw_concept"}:
            item["redraw_required"] = True
            item["redraw_template_id"] = template_id
            item.setdefault("redraw_instruction", redraw_instruction(item, asset))
            report[effective].append({"source_id": source_id, "template_id": template_id})
        else:
            item["redraw_required"] = False
            item["decision"] = "omit"
            item["effective_decision"] = "omit"
            report["omit"].append(source_id)
            if original_decision in {"redraw", "redraw_svg"} or str(asset.get("decision_hint") or "").startswith("redraw:"):
                report["redraw_template_missing"].append(source_id)

    coverage = outline.get("coverage_report")
    if not isinstance(coverage, dict):
        return report
    decisions = {
        str(item.get("source_id") or item.get("id")): item
        for item in outline.get("figure_decisions", []) or []
        if isinstance(item, dict) and (item.get("source_id") or item.get("id"))
    }
    for item in coverage.get("figures", []) or []:
        if not isinstance(item, dict):
            continue
        decision = decisions.get(str(item.get("source_id") or item.get("id") or ""))
        if decision:
            item["action"] = decision.get("decision") or "omit"
            item["redraw_required"] = str(decision.get("decision") or "").startswith("redraw")
    return report


def section_id_from_heading(value: str) -> str:
    match = SECTION_ID_RE.match(str(value or ""))
    return match.group(1) if match else ""


def source_heading_title(value: str) -> str:
    match = SECTION_ID_RE.match(str(value or "").strip())
    if not match:
        return str(value or "").strip()
    section_id = match.group(1)
    rest = match.group(2).strip()
    return f"{section_id} {rest}".strip()


def strip_section_prefix(value: str) -> str:
    match = SECTION_ID_RE.match(str(value or "").strip())
    if match:
        return match.group(2).strip()
    return str(value or "").strip()


def comparable_label(value: str) -> str:
    return re.sub(r"[\s>：:（）()《》【】\[\]·\-_/]+", "", strip_section_prefix(value)).lower()


def labels_match(left: str, right: str) -> bool:
    left_key = comparable_label(left)
    right_key = comparable_label(right)
    return bool(left_key and right_key and (left_key == right_key or left_key in right_key or right_key in left_key))


def find_node_by_outline_path(nodes: list[Any], node_path: str) -> dict[str, Any] | None:
    parts = [part.strip() for part in str(node_path or "").split(">") if part.strip()]
    if parts and comparable_label(parts[0]) == comparable_label("root"):
        parts = parts[1:]
    current_nodes = [node for node in nodes if isinstance(node, dict)]
    current: dict[str, Any] | None = None
    for part in parts:
        current = next(
            (node for node in current_nodes if labels_match(str(node.get("title") or node.get("id") or ""), part)),
            None,
        )
        if current is None:
            return None
        current_nodes = [child for child in current.get("children", []) or [] if isinstance(child, dict)]
    return current


def apply_section_fidelity(outline: dict[str, Any]) -> None:
    """Use coverage_report.sections to keep source section IDs visible in rendered nodes."""
    coverage = outline.get("coverage_report")
    if not isinstance(coverage, dict):
        return
    for section in coverage.get("sections", []) or []:
        if not isinstance(section, dict):
            continue
        source_heading = str(section.get("source_heading") or section.get("source") or "")
        section_id = section_id_from_heading(source_heading)
        if not section_id:
            continue
        node = find_node_by_outline_path(outline.get("nodes", []) or [], str(section.get("node_path") or section.get("path") or ""))
        if not node:
            continue
        node["section_id"] = section_id
        if isinstance(section.get("source_span"), dict):
            node["source_span"] = section["source_span"]
        title = str(node.get("title") or "")
        if not title.startswith(section_id):
            node["title"] = source_heading_title(source_heading)


def visible_text_len(value: Any) -> int:
    return len(re.sub(r"\s+", "", str(value or "")))


def is_summary_node(node: dict[str, Any]) -> bool:
    title = str(node.get("title") or "")
    return str(node.get("type") or "") in {"summary", "note"} and re.search(r"(小结|总结|summary)", title, re.I) is not None


def source_lines_for_span(source_text: str, span: dict[str, Any] | None) -> list[str]:
    if not source_text or not isinstance(span, dict):
        return []
    lines = source_text.splitlines()
    start = max(1, int(span.get("line_start") or 1))
    end = min(len(lines), int(span.get("line_end") or start))
    return [line.strip() for line in lines[start - 1 : end] if line.strip()]


def find_source_sentence(source_text: str, key: str) -> str:
    key = str(key or "").split("：", 1)[0].split(":", 1)[0].strip()
    if not key:
        return ""
    for line in source_text.splitlines():
        stripped = line.strip()
        if stripped.startswith(key) and visible_text_len(stripped) >= 15:
            return stripped
    return ""


def apply_summary_fidelity(outline: dict[str, Any], source_text: str = "") -> None:
    for node in iter_nodes(outline.get("nodes", []) or []):
        if not is_summary_node(node):
            continue
        for child in node.get("children", []) or []:
            if not isinstance(child, dict):
                continue
            title = str(child.get("title") or "")
            source_quote = str(child.get("source_quote") or "").strip()
            replacement = find_source_sentence(source_text, source_quote or title) or source_quote
            if replacement and visible_text_len(title) < 15:
                child["title"] = replacement
                child["source_quote"] = replacement
                child["summary_sentence"] = True


KNOWN_TERMS = [
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


def ensure_keywords_node(outline: dict[str, Any], source_text: str) -> None:
    if any(node.get("type") == "keywords" for node in iter_nodes(outline.get("nodes", []) or [])):
        return
    terms: list[str] = []
    source_lower = source_text.lower()
    for term in KNOWN_TERMS:
        variants = [term.lower()]
        if term == "Saddle Points":
            variants.append("saddle point")
        if any(variant in source_lower for variant in variants):
            terms.append(term)
    if len(terms) < 8:
        return
    first_quote = find_source_sentence(source_text, terms[0]) or terms[0]
    outline.setdefault("nodes", []).append(
        {
            "id": "n_keywords",
            "type": "keywords",
            "title": "[*] 关键词",
            "terms": terms[:12],
            "source_quote": first_quote,
        }
    )


def smart_truncate(value: str, limit: int = 70) -> str:
    value = re.sub(r"\s+", " ", str(value or "").strip())
    if visible_text_len(value) <= limit:
        return value
    cutoff = min(len(value), limit)
    while cutoff > 0 and value[cutoff - 1].isascii() and value[cutoff - 1].isalnum():
        if cutoff >= len(value) or not (value[cutoff].isascii() and value[cutoff].isalnum()):
            break
        cutoff -= 1
    if cutoff < max(12, limit // 2):
        space = value.rfind(" ", 0, limit)
        cutoff = space if space >= max(12, limit // 2) else limit
    return value[:cutoff].rstrip(" ，,、；;:：") + "..."


def source_lines_with_numbers_for_span(source_text: str, span: dict[str, Any] | None) -> list[tuple[int, str]]:
    if not source_text or not isinstance(span, dict):
        return []
    lines = source_text.splitlines()
    start = max(1, int(span.get("line_start") or 1))
    end = min(len(lines), int(span.get("line_end") or start))
    return [
        (line_number, line.strip())
        for line_number, line in enumerate(lines[start - 1 : end], start=start)
        if line.strip()
    ]


def split_candidate_parts(cleaned: str) -> list[str]:
    primary = [part.strip(" ，,") for part in re.split(r"[。；;]", cleaned) if part.strip(" ，,")]
    if len(primary) == 1 and visible_text_len(primary[0]) > 45:
        clause_parts = [part.strip(" ，,") for part in re.split(r"[，,]", primary[0]) if part.strip(" ，,")]
        if len(clause_parts) >= 3:
            return clause_parts
    return primary


def candidate_bullets_from_lines(lines: list[str]) -> list[str]:
    candidates: list[str] = []
    for line in lines:
        if line.startswith("#") or line.startswith("!") or line.startswith("图") or line.startswith("|"):
            continue
        cleaned = re.sub(r"^[-*]\s*", "", line).strip()
        for value in split_candidate_parts(cleaned):
            if visible_text_len(value) >= 8:
                candidates.append(smart_truncate(value))
    return candidates


def candidate_bullets_from_span(source_text: str, span: dict[str, Any] | None) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for line_number, line in source_lines_with_numbers_for_span(source_text, span):
        if line.startswith("#") or line.startswith("!") or line.startswith("图") or line.startswith("|"):
            continue
        cleaned = re.sub(r"^[-*]\s*", "", line).strip()
        for value in split_candidate_parts(cleaned):
            if visible_text_len(value) < 8:
                continue
            candidates.append(
                {
                    "title": smart_truncate(value),
                    "source_quote": value,
                    "source_span": {"line_start": line_number, "line_end": line_number},
                }
            )
    return candidates


def child_count_for_density(node: dict[str, Any]) -> int:
    count = len([child for child in node.get("children", []) or [] if isinstance(child, dict)])
    if node.get("equations"):
        count += len(node.get("equations", []) or [])
    if node.get("table"):
        count += len((node.get("table") or {}).get("rows", []) or [])
    return count


def density_keywords_for_node(node: dict[str, Any]) -> list[str]:
    title = str(node.get("title") or "").lower()
    keywords: list[str] = []
    if "momentum" in title or "动量" in title:
        keywords.extend(["momentum", "动量", "惯性", "鞍点", "历史方向", "梯度"])
    if "batch" in title or "批" in title:
        keywords.extend(["batch", "批次", "batch size", "epoch", "梯度", "loss"])
    return keywords


def apply_h3_density(outline: dict[str, Any], source_text: str, min_points: int = 4, max_points: int = 6) -> None:
    for node in iter_nodes(outline.get("nodes", []) or []):
        section_id = str(node.get("section_id") or "")
        if section_id.count(".") < 2:
            continue
        if child_count_for_density(node) >= min_points:
            continue
        candidates = candidate_bullets_from_span(source_text, node.get("source_span"))
        existing = {compact_compare_text(child.get("title", "")) for child in node.get("children", []) or [] if isinstance(child, dict)}
        node.setdefault("children", [])
        for candidate in candidates:
            key = compact_compare_text(candidate["title"])
            if not key or any(key in existing_key or existing_key in key for existing_key in existing):
                continue
            child_id = f"{node.get('id', 'n')}_auto_{len(node['children']) + 1}"
            node["children"].append(
                {
                    "id": child_id,
                    "title": candidate["title"],
                    "source_quote": candidate["source_quote"],
                    "source_span": candidate["source_span"],
                    "auto_density": True,
                }
            )
            existing.add(key)
            if child_count_for_density(node) >= min_points or len(node["children"]) >= max_points:
                break


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


def node_visuals(
    node: dict[str, Any],
    outline: dict[str, Any],
    images_by_id: dict[str, dict[str, Any]],
    project_path: Path,
    exports_dir: Path,
) -> list[dict[str, str]]:
    resolved: list[dict[str, str]] = []
    raw_images = list(node.get("images", []) or [])
    for decision in figure_decisions_by_node(outline).get(str(node.get("id")), []):
        if str(decision.get("decision") or "") in IMAGE_LAYOUT_DECISIONS:
            raw_images.append(decision)

    for raw in raw_images:
        if isinstance(raw, str):
            raw = {"id": raw}
        if not isinstance(raw, dict):
            continue
        source_id = str(raw.get("id") or raw.get("source_id") or "")
        asset = images_by_id.get(source_id, {})
        alt = raw.get("alt") or asset.get("alt") or source_id or "mind map image"
        effective, template_id = effective_visual_decision(raw, asset)
        if effective == "omit":
            continue
        callouts = ensure_visual_callouts(raw, asset) if effective != "omit" else []
        tier = readability_tier_for(source_id, effective, raw, asset)
        min_width, min_height = readability_threshold(tier, effective)
        if effective == "preserve_crop":
            crop_path = crop_image_for_visual(project_path, raw, asset, source_id or "source")
            if not crop_path:
                continue
            resolved.append(
                {
                    "kind": "preserve_crop",
                    "id": source_id,
                    "path": image_path_for_markdown(project_path, exports_dir, crop_path),
                    "alt": str(alt),
                    "source_path": str(raw.get("path") or asset.get("path") or ""),
                    "callouts": callouts,
                    "readability_tier": tier,
                    "min_width": str(min_width),
                    "min_height": str(min_height),
                }
            )
            continue
        if effective in {"redraw_high_fidelity", "redraw_concept"}:
            template = template_path(template_id)
            if not template:
                continue
            resolved.append(
                {
                    "kind": effective,
                    "id": source_id,
                    "alt": str(alt),
                    "instruction": redraw_instruction(raw, asset),
                    "asset_type": asset_kind(raw, asset) or "screenshot",
                    "template_id": template_id,
                    "svg": template.read_text(encoding="utf-8"),
                    "callouts": callouts,
                    "readability_tier": tier,
                    "min_width": str(min_width),
                    "min_height": str(min_height),
                }
            )
            continue
        path = raw.get("path") or asset.get("path")
        if not path:
            continue
        resolved.append(
            {
                "kind": "preserve_full",
                "id": source_id,
                "path": image_path_for_markdown(project_path, exports_dir, str(path)),
                "alt": str(alt),
                "callouts": callouts,
                "readability_tier": tier,
                "min_width": str(min_width),
                "min_height": str(min_height),
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


def append_callouts(lines: list[str], callouts: list[dict[str, str]]) -> None:
    for callout in callouts:
        text = markdown_escape(callout.get("text") or "")
        if text:
            lines.append(f"- 图像结论：{text}")


def node_terms(node: dict[str, Any]) -> list[str]:
    raw_terms = node.get("terms") or node.get("keywords") or []
    if isinstance(raw_terms, str):
        raw_terms = [raw_terms]
    return [markdown_escape(term) for term in raw_terms if str(term).strip()]


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
    if node.get("type") == "keywords":
        terms = node_terms(node)
        if terms:
            append_bullet(lines, level, "关键词：" + " / ".join(terms))

    for visual in node_visuals(node, outline, images_by_id, project_path, exports_dir):
        if visual.get("kind") in {"preserve_full", "preserve_crop", "preserve", "crop_preserve"}:
            append_render_heading(lines, level + 1, f"![{markdown_escape(visual['alt'])}]({visual['path']})")
            append_callouts(lines, visual.get("callouts", []) or [])
        else:
            append_render_heading(lines, level + 1, f"SVG重绘：{markdown_escape(visual['alt'])}")
            append_bullet(lines, level + 2, "重绘语义：" + markdown_escape(visual.get("instruction", "")))
            append_callouts(lines, visual.get("callouts", []) or [])

    for child in node.get("children", []) or []:
        if isinstance(child, dict):
            append_node(lines, child, level + 1, outline, images_by_id, project_path, exports_dir)


def html_text(value: Any) -> str:
    return html.escape(markdown_escape(value), quote=True)


def compact_compare_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


def semantically_redundant(left: Any, right: Any) -> bool:
    left_text = compact_compare_text(left)
    right_text = compact_compare_text(right)
    if len(left_text) < 6 or len(right_text) < 6:
        return False
    return left_text in right_text or right_text in left_text


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


def render_template_redraw_html(visual: dict[str, str]) -> str:
    source_id = html.escape(str(visual.get("id") or ""), quote=True)
    alt = html_text(visual.get("alt") or "SVG redraw")
    instruction = html_text(visual.get("instruction") or "")
    asset_type = html.escape(str(visual.get("asset_type") or "screenshot"), quote=True)
    template_id = html.escape(str(visual.get("template_id") or ""), quote=True)
    kind = html.escape(str(visual.get("kind") or "redraw_concept"), quote=True)
    min_width = html.escape(str(visual.get("min_width") or "200"), quote=True)
    min_height = html.escape(str(visual.get("min_height") or "115"), quote=True)
    svg = str(visual.get("svg") or "")
    callouts = render_image_callouts(visual.get("callouts", []) or [])
    return (
        f'<figure class="balanced-redraw-card" data-source-id="{source_id}" '
        f'data-image-kind="{kind}" data-asset-type="{asset_type}" data-template-id="{template_id}" '
        f'data-min-width="{min_width}" data-min-height="{min_height}" data-redraw-required="true">'
        f"{svg}"
        f"<figcaption>{instruction}</figcaption>"
        f"{callouts}"
        "</figure>"
    )


def render_image_callouts(callouts: list[dict[str, str]]) -> str:
    items = []
    for callout in callouts:
        text = html_text(callout.get("text") or "")
        quote = html.escape(str(callout.get("source_quote") or ""), quote=True)
        if text and quote:
            items.append(f'<li data-source-quote="{quote}">{text}</li>')
    if not items:
        return ""
    return '<ul class="balanced-image-callouts">' + "".join(items[:2]) + "</ul>"


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
    section_id = str(node.get("section_id") or "").strip()
    visuals = node_visuals(node, outline, images_by_id, project_path, exports_dir)
    classes = ["balanced-node", f"depth-{min(depth, 4)}", f"type-{node_type}"]
    if visuals:
        classes.append("has-visual")
    if extra_class:
        classes.append(extra_class)
    attrs = [
        f'class="{" ".join(classes)}"',
        f'data-node-id="{node_id}"',
        f'data-node-type="{node_type}"',
    ]
    if section_id:
        attrs.append(f'data-section-id="{html.escape(section_id, quote=True)}"')
    parts = [f"<article {' '.join(attrs)}>"]
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

    terms = node_terms(node)
    if node.get("type") == "keywords" and terms:
        parts.append(
            '<div class="balanced-keyword-pills">'
            + "".join(f'<span class="keywords-pill">{html_text(term)}</span>' for term in terms)
            + "</div>"
        )

    equations = [normalize_latex(str(equation)) for equation in node.get("equations", []) or []]
    if equations:
        parts.append('<div class="balanced-equations">')
        for equation in equations:
            parts.append(f'<div class="balanced-equation">公式：{html.escape(equation, quote=False)}</div>')
        parts.append("</div>")

    if node.get("type") == "table" or node.get("table"):
        parts.append(render_table_html(node))

    images = [visual for visual in visuals if visual.get("kind") in {"preserve_full", "preserve_crop", "preserve", "crop_preserve"}]
    if images:
        parts.append('<div class="balanced-images">')
        for image in images:
            src = html.escape(image["path"], quote=True)
            alt = html_text(image["alt"])
            kind = html.escape(str(image.get("kind") or "preserve"), quote=True)
            source_id = html.escape(str(image.get("id") or ""), quote=True)
            min_width = html.escape(str(image.get("min_width") or "170"), quote=True)
            min_height = html.escape(str(image.get("min_height") or "96"), quote=True)
            callouts = render_image_callouts(image.get("callouts", []) or [])
            parts.append(
                f'<figure class="balanced-preserve-image is-{kind}" data-source-id="{source_id}" '
                f'data-image-kind="{kind}" data-min-width="{min_width}" data-min-height="{min_height}">'
                f'<img src="{src}" alt="{alt}"><figcaption>{alt}</figcaption>{callouts}</figure>'
            )
        parts.append("</div>")
    redraws = [visual for visual in visuals if visual.get("kind") in {"redraw_high_fidelity", "redraw_concept", "redraw"}]
    if redraws:
        parts.append('<div class="balanced-redraws">')
        for visual in redraws:
            parts.append(render_template_redraw_html(visual))
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
            visible_children = list(children)
            if len(visible_children) == 1 and description and semantically_redundant(
                visible_children[0].get("title", ""), node.get("description", "")
            ):
                visible_children = []
            if len(visible_children) == 1:
                child = visible_children[0]
                child_id = html.escape(str(child.get("id") or ""), quote=True)
                parts.append(
                    f'<p class="balanced-leaf-list is-plain" data-node-id="{child_id}">'
                    f'{html_text(child.get("title") or child.get("id") or "")}</p>'
                )
            elif visible_children:
                parts.append('<ol class="balanced-leaf-list">')
                for child in visible_children:
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


TERM_RE = re.compile(
    r"\b(?:Batch Size|Noisy Gradient|Local Minima|Saddle Points|Flat Minima|Sharp Minima|Epoch|Shuffle|Momentum|Batch|Gradient|Loss)\b",
    re.I,
)


def collect_root_terms(outline: dict[str, Any]) -> list[str]:
    explicit = outline.get("core_terms") or outline.get("keywords") or []
    if isinstance(explicit, str):
        explicit = [explicit]
    terms = [str(term).strip() for term in explicit if str(term).strip()]

    if not terms:
        for node in iter_nodes(outline.get("nodes", []) or []):
            if node.get("type") == "keywords":
                terms.extend(node_terms(node))
        if not terms:
            text = " ".join(
                str(value)
                for node in iter_nodes(outline.get("nodes", []) or [])
                for key, value in node.items()
                if key in {"title", "description", "source_quote"} and isinstance(value, str)
            )
            terms.extend(match.group(0) for match in TERM_RE.finditer(text))

    first_level_titles = {
        compact_compare_text(strip_section_prefix(str(node.get("title") or "")))
        for node in outline.get("nodes", []) or []
        if isinstance(node, dict)
    }
    unique: list[str] = []
    seen: set[str] = set()
    for term in terms:
        key = compact_compare_text(term)
        if not key or key in seen or key in first_level_titles:
            continue
        seen.add(key)
        unique.append(term)
        if len(unique) == 3:
            break
    return unique


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
    bottom_nodes: list[dict[str, Any]] = []
    for node in outline.get("nodes", []) or []:
        if not isinstance(node, dict):
            continue
        if node.get("type") in {"keywords", "tips"} and str(node.get("title") or "").startswith("[*]"):
            bottom_nodes.append(node)
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

    def render_bottom(nodes: list[dict[str, Any]]) -> str:
        if not nodes:
            return ""
        body = "".join(
            render_node_html(node, 1, outline, images_by_id, project_path, exports_dir, extra_class="balanced-bottom-node")
            for node in nodes
        )
        return f'<section class="balanced-bottom" aria-label="derived grounded strips">{body}</section>'

    root_summary = html_text(outline.get("core_question") or outline.get("description") or outline.get("source_title") or "")
    root_terms = collect_root_terms(outline)
    root_items = "".join(f"<li>{html_text(term)}</li>" for term in root_terms)
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
    parts.extend(["</section>", render_side(right_nodes, "right"), render_bottom(bottom_nodes), "</section>"])
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
    image_policy_report: dict[str, Any],
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
        "image_policy_report": image_policy_report,
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
        source_text = ctx["source"].read_text(encoding="utf-8") if ctx["source"].exists() else ""
        apply_section_fidelity(outline)
        apply_summary_fidelity(outline, source_text)
        ensure_keywords_node(outline, source_text)
        apply_h3_density(outline, source_text)
        image_policy_report = apply_image_policy(outline, images_by_id)

        ctx["intermediate"].mkdir(parents=True, exist_ok=True)
        ctx["exports"].mkdir(parents=True, exist_ok=True)
        base_name = args.section_id or manifest.get("project_name") or ctx["project"].name
        markdown_path = ctx["intermediate"] / "mindmap.md"
        mindmap_path = ctx["intermediate"] / "mindmap.json"
        layout_self_check_path = ctx["intermediate"] / "layout_self_check.md"
        image_policy_report_path = ctx["intermediate"] / "image_policy_report.json"
        html_path = ctx["exports"] / f"{base_name}.html"

        layout_profile, layout_stats = resolve_layout_profile(outline, manifest)
        markdown = build_markdown(outline, images_by_id, ctx["project"], ctx["exports"])
        markdown_path.write_text(markdown, encoding="utf-8")

        mindmap = build_mindmap_json(outline, manifest, markdown_path, html_path, layout_profile, image_policy_report)
        write_json(mindmap_path, mindmap)
        write_json(image_policy_report_path, image_policy_report)
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
    print(f"- image policy report: {project_relative(ctx['project'], image_policy_report_path)}")
    print(f"- html: {project_relative(ctx['project'], html_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

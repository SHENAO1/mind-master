#!/usr/bin/env python
"""Build and enrich the Mind-Master image asset index."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError:  # pragma: no cover - surfaced by CLI warning
    Image = None  # type: ignore[assignment]

try:  # Keep checkpoint symbols printable on Windows consoles.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:  # pragma: no cover
    pass


GENERIC_ALT_RE = re.compile(r"^image extracted from\b", re.I)
DECORATIVE_RE = re.compile(r"(logo|cover|banner|校牌|封面|装饰|水印)", re.I)
DATA_CHART_RE = re.compile(
    r"(data|chart|plot|curve|heatmap|roc|loss|gradient|accuracy|trend|数据|曲线|趋势|热力|坐标|实验|对比图)",
    re.I,
)
SCREENSHOT_RE = re.compile(r"(screenshot|screen shot|slide|ppt|截图|课件|幻灯|白板|页面)", re.I)
DOC_SCREENSHOT_MIN_EDGE = 900
DOC_SCREENSHOT_MIN_AREA = 700_000
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SVG_TEMPLATE_DIR = SKILL_DIR / "assets" / "svg_templates"
REGISTERED_TEMPLATES = {
    "loss_landscape_sharp_vs_flat": SVG_TEMPLATE_DIR / "loss_landscape_sharp_vs_flat.svg",
    "gradient_vs_momentum_vector": SVG_TEMPLATE_DIR / "gradient_vs_momentum_vector.svg",
    "batch_size_update_comparison": SVG_TEMPLATE_DIR / "batch_size_update_comparison.svg",
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


def as_image_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        images = payload.get("images", [])
    else:
        images = payload
    return [dict(item) for item in images if isinstance(item, dict)]


def image_size(project_path: Path, item: dict[str, Any]) -> tuple[int | None, int | None]:
    width = item.get("width")
    height = item.get("height")
    if isinstance(width, int) and isinstance(height, int):
        return width, height
    if Image is None:
        return None, None
    raw_path = item.get("path") or item.get("source_path")
    if not raw_path:
        return None, None
    path = Path(str(raw_path))
    absolute = path if path.is_absolute() else project_path / path
    if not absolute.exists():
        return None, None
    try:
        with Image.open(absolute) as image:
            return image.width, image.height
    except Exception:
        return None, None


def truthy(value: Any) -> bool:
    return value is True or str(value).lower() in {"true", "1", "yes"}


def source_context_for_asset(source_text: str, item: dict[str, Any], radius: int = 4) -> str:
    path = str(item.get("path") or item.get("source_path") or "")
    if not path or not source_text:
        return ""
    lines = source_text.splitlines()
    for index, line in enumerate(lines):
        if path in line or Path(path).name in line:
            start = max(0, index - radius)
            end = min(len(lines), index + radius + 1)
            return "\n".join(lines[start:end])
    return ""


def match_svg_template(text: str) -> str:
    text_norm = " ".join(text.split())
    if re.search(r"(Sharp Minima|sharp minima)", text_norm) and re.search(r"(Flat Minima|flat minima)", text_norm):
        if re.search(r"(图\s*5-5|Sharp Minima\s*(?:与|vs\.?|和)\s*Flat Minima|Sharp\s+vs\.?\s+Flat)", text_norm, re.I):
            if REGISTERED_TEMPLATES["loss_landscape_sharp_vs_flat"].exists():
                return "loss_landscape_sharp_vs_flat"

    template_patterns = [
        (
            "gradient_vs_momentum_vector",
            [r"Momentum", r"梯度方向|梯度下降", r"历史方向", r"更新方向|方向改变", r"加权求和|v_\{t\+1\}"],
        ),
        (
            "batch_size_update_comparison",
            [r"Full Batch", r"Batch Size\s*为\s*1", r"20 组训练数据", r"更新 20 次"],
        ),
    ]
    for template_id, patterns in template_patterns:
        if template_id in REGISTERED_TEMPLATES and REGISTERED_TEMPLATES[template_id].exists():
            if sum(1 for pattern in patterns if re.search(pattern, text_norm, re.I)) >= 2:
                return template_id
    return ""


def looks_like_real_data_chart(text: str) -> bool:
    return bool(
        re.search(r"Batch Size.*(?:时间|更新时间|对比|time)|(?:时间|更新时间|对比|time).*Batch Size", text, re.I)
        and re.search(r"1~1000|10000|60000|坐标|实验|趋势|curve|plot|单次更新|epoch\s*时间|时间对比图", text, re.I)
    )


def decision_hint_for_asset(asset_type: str, is_data_chart: bool, context: str) -> tuple[str, str, str]:
    if asset_type == "data_chart" and is_data_chart and looks_like_real_data_chart(context):
        return "preserve", "", "contains source-backed experimental data trend and concrete numeric ranges"

    template_id = match_svg_template(context)
    if template_id:
        return f"redraw:{template_id}", template_id, "matches a registered SVG concept template"

    return "omit", "", "default omit: not a readable data chart and no registered redraw template matched"


def classify_asset(item: dict[str, Any], project_path: Path, source_text: str = "") -> dict[str, Any]:
    enriched = dict(item)
    explicit_type = str(enriched.get("type") or "").strip().lower()
    explicit_data_chart = bool(enriched.get("is_data_chart")) or explicit_type == "data_chart"
    alt = str(enriched.get("alt") or "")
    kind = str(enriched.get("kind") or enriched.get("figure_kind") or "")
    path_text = str(enriched.get("path") or enriched.get("source_path") or "")
    source_anchor = str(enriched.get("source_anchor") or "")
    context = str(enriched.get("source_context") or source_context_for_asset(source_text, enriched))
    text_blob = " ".join([alt, kind, path_text, source_anchor, str(enriched.get("ocr_text") or ""), context])
    width, height = image_size(project_path, enriched)
    if width is not None:
        enriched["width"] = width
    if height is not None:
        enriched["height"] = height

    if "source_kind" not in enriched:
        if "screenshots/" in path_text.replace("\\", "/") or kind == "screenshot":
            enriched["source_kind"] = "external_or_pdf_screenshot"
        else:
            enriched["source_kind"] = "docx_embedded"

    is_data_chart = bool(enriched.get("is_data_chart")) or bool(DATA_CHART_RE.search(text_blob)) or looks_like_real_data_chart(text_blob)
    if DECORATIVE_RE.search(text_blob):
        asset_type = "decorative"
    elif is_data_chart and not SCREENSHOT_RE.search(text_blob):
        asset_type = "data_chart"
    elif SCREENSHOT_RE.search(text_blob):
        asset_type = "screenshot"
    elif GENERIC_ALT_RE.search(alt) and enriched.get("source_kind") == "docx_embedded":
        asset_type = "screenshot"
    elif width and height and enriched.get("source_kind") == "docx_embedded":
        area = width * height
        if min(width, height) < DOC_SCREENSHOT_MIN_EDGE or area < DOC_SCREENSHOT_MIN_AREA:
            asset_type = "screenshot"
        else:
            asset_type = "illustration"
    else:
        asset_type = "illustration"

    if enriched.get("type"):
        asset_type = str(enriched["type"])
    if (
        is_data_chart
        and looks_like_real_data_chart(text_blob)
        and (not explicit_type or explicit_data_chart or explicit_type not in {"screenshot", "slide", "photo"})
    ):
        asset_type = "data_chart"

    decision_hint, template_id, decision_hint_reason = decision_hint_for_asset(asset_type, bool(is_data_chart), text_blob)
    redraw_required = decision_hint.startswith("redraw:")

    enriched["type"] = asset_type
    enriched["is_data_chart"] = bool(is_data_chart or asset_type == "data_chart")
    enriched["redraw_required"] = redraw_required
    enriched["decision_hint"] = decision_hint
    enriched["decision_hint_reason"] = decision_hint_reason
    if template_id:
        enriched["redraw_template_id"] = template_id
    else:
        enriched.pop("redraw_template_id", None)
    if context:
        enriched["source_context"] = context
    enriched.setdefault("decision", "candidate")
    if redraw_required:
        enriched.setdefault(
            "redraw_instruction",
            f"Use registered SVG template '{template_id}' for source visual '{enriched.get('id', '')}'.",
        )
    else:
        enriched.pop("redraw_instruction", None)
    enriched.setdefault("classified_at", utc_now())
    return enriched


def merge_existing(source_images: list[dict[str, Any]], existing_images: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {str(item.get("id")): item for item in existing_images if item.get("id")}
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in source_images:
        asset_id = str(item.get("id") or "")
        existing = by_id.get(asset_id, {})
        combined = {**item, **existing}
        merged.append(combined)
        if asset_id:
            seen.add(asset_id)
    for item in existing_images:
        asset_id = str(item.get("id") or "")
        if asset_id and asset_id not in seen:
            merged.append(item)
    return merged


def build_index(project_path: Path) -> list[dict[str, Any]]:
    source_assets_path = project_path / "intermediate" / "source_assets.json"
    index_path = project_path / "assets" / "images" / "index.json"
    source_path = project_path / "intermediate" / "source.md"
    source_assets = load_json(source_assets_path, {"images": []})
    existing = load_json(index_path, [])
    source_text = source_path.read_text(encoding="utf-8") if source_path.exists() else ""
    merged = merge_existing(as_image_list(source_assets), as_image_list(existing))
    return [classify_asset(item, project_path, source_text) for item in merged]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create/enrich assets/images/index.json.")
    parser.add_argument("project", type=Path, help="Mind-Master project path.")
    args = parser.parse_args(argv)
    project_path = args.project.resolve()
    try:
        index = build_index(project_path)
    except Exception as exc:
        print(f"Asset extraction failed: {exc}", file=sys.stderr)
        return 1

    index_path = project_path / "assets" / "images" / "index.json"
    write_json(index_path, index)
    preserve_count = sum(1 for item in index if item.get("decision_hint") == "preserve")
    redraw_count = sum(1 for item in index if str(item.get("decision_hint", "")).startswith("redraw:"))
    omit_count = sum(1 for item in index if item.get("decision_hint") == "omit")
    print("GATE 3 ✅ Assets extracted.")
    print("Deliverables:")
    print(f"- image index: {index_path}")
    print(f"- images indexed: {len(index)}")
    print(f"- preserve hints: {preserve_count}")
    print(f"- redraw_required: {redraw_count}")
    print(f"- omit hints: {omit_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

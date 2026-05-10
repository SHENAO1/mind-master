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
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
DISPLAY_MATH_RE = re.compile(r"\$\$(.+?)\$\$", re.S)
INLINE_MATH_RE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.S)
LATEX_LIKE_RE = re.compile(r"(?:_\{|[\^]\{|\\(?:frac|sum|nabla|theta|lambda|eta|sigma|alpha|beta|gamma|mu|Sigma)\b)")


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
    fields = ["title", "description", "summary", "source_quote"]
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


def image_decision_keys(outline: dict[str, Any], mindmap: dict[str, Any]) -> str:
    values: list[str] = []
    for item in (outline.get("figure_decisions") or []) + (mindmap.get("figure_decisions") or []):
        if isinstance(item, dict):
            values.extend(str(item.get(key, "")) for key in ("id", "source_id", "path", "source_path"))
    coverage = mindmap.get("coverage_report") or outline.get("coverage_report") or {}
    for item in coverage.get("figures", []) or []:
        if isinstance(item, dict):
            values.extend(str(item.get(key, "")) for key in ("id", "source_id", "path", "source_path"))
    return " ".join(values)


def check_image_decisions(source_text: str, outline: dict[str, Any], mindmap: dict[str, Any]) -> dict[str, Any]:
    images = source_images(source_text)
    keys = image_decision_keys(outline, mindmap)
    missing = [image for image in images if image["path"] not in keys and Path(image["path"]).name not in keys]
    return {"passed": not missing, "source_image_count": len(images), "missing": missing}


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
  await page.waitForSelector('.markmap svg', { timeout });
  await page.waitForTimeout(5000);
  const result = await page.evaluate(() => {
    const svg = document.querySelector('.markmap svg');
    const box = svg ? svg.getBoundingClientRect() : null;
    return {
      katexErrors: document.querySelectorAll('.katex-error').length,
      katexCount: document.querySelectorAll('.katex').length,
      imageCount: document.querySelectorAll('.markmap image, .markmap img').length,
      svgWidth: box ? Math.round(box.width) : 0,
      svgHeight: box ? Math.round(box.height) : 0,
      textLength: document.body.innerText.length
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
    data["passed"] = data["katexErrors"] == 0 and data["svgWidth"] > 0 and data["svgHeight"] > 0 and not data["pageErrors"]
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
        checks["table_checks"] = check_tables(flat, source_text)
        checks["formula_coverage"] = check_formula_coverage(root, source_text)
        checks["math_delimiter_checks"] = check_math_delimiters(root, markdown)
        checks["image_decisions"] = check_image_decisions(source_text, outline, mindmap) if source_text else {"passed": True, "skipped": True}
        checks["rendered_images"] = check_rendered_images(markdown, ctx["exports"])
        if args.skip_browser:
            checks["browser"] = {"passed": True, "skipped": True}
            warnings.append("Browser validation skipped by --skip-browser.")
        else:
            checks["browser"] = check_browser(html_path, args.node, args.browser_timeout_ms)
            if (
                checks["formula_coverage"].get("source_display_formula_count", 0) > 0
                and not checks["browser"].get("skipped")
                and checks["browser"].get("katexCount", 0) < 1
            ):
                checks["browser"]["passed"] = False
                checks["browser"]["reason"] = "Source contains display formulas but rendered HTML has no KaTeX nodes."
            if checks["browser"].get("skipped"):
                warnings.append(str(checks["browser"].get("reason", "Browser validation skipped.")))

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

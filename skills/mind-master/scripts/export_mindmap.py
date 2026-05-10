#!/usr/bin/env python
"""Export a rendered Mind-Master Markmap HTML file to SVG, PNG, and PDF."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment]

try:  # Keep checkpoint symbols printable on Windows consoles.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:  # pragma: no cover
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def project_relative(project_path: Path, path: Path) -> str:
    return path.resolve().relative_to(project_path.resolve()).as_posix()


def resolve_paths(args: argparse.Namespace) -> dict[str, Path]:
    project_path = args.project.resolve()
    manifest = load_json(project_path / "manifest.json")
    if args.section_id:
        exports_dir = project_path / "maps" / args.section_id / "exports"
        intermediate_dir = project_path / "maps" / args.section_id / "intermediate"
        base_name = args.section_id
    else:
        exports_dir = project_path / "exports"
        intermediate_dir = project_path / "intermediate"
        base_name = manifest.get("project_name") or project_path.name
    html_path = args.html or exports_dir / f"{base_name}.html"
    return {
        "project": project_path,
        "intermediate": intermediate_dir,
        "exports": exports_dir,
        "html": html_path,
        "svg": exports_dir / f"{base_name}.svg",
        "png": exports_dir / f"{base_name}.png",
        "pdf": exports_dir / f"{base_name}.pdf",
        "export_report": intermediate_dir / "export.json",
        "manifest": project_path / "manifest.json",
    }


def find_node(node_arg: str | None) -> str | None:
    if node_arg:
        return node_arg
    return os.environ.get("MIND_MASTER_NODE") or shutil.which("node")


def node_env() -> dict[str, str]:
    env = os.environ.copy()
    if "NODE_PATH" not in env:
        bundled = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "node_modules"
        if bundled.exists():
            env["NODE_PATH"] = str(bundled)
    return env


def export_with_node(paths: dict[str, Path], node: str, scale: float, timeout_ms: int) -> dict:
    script = r"""
const fs = require('fs');
const { chromium } = require('playwright');

const [htmlPath, svgPath, pngPath, pdfPath, scaleRaw, timeoutRaw] = process.argv.slice(2);
const scale = Number(scaleRaw || 2);
const timeout = Number(timeoutRaw || 60000);

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 2200, height: 1500 },
    deviceScaleFactor: Math.max(1, scale)
  });
  await page.goto('file:///' + htmlPath.replace(/\\/g, '/'), { waitUntil: 'networkidle', timeout });
  await page.waitForFunction(() => {
    return window.MIND_MASTER_READY ||
      document.querySelector('.balanced-layout') ||
      document.querySelector('.markmap svg');
  }, { timeout });
  await page.waitForTimeout(2200);
  await page.evaluate(() => {
    const shell = document.querySelector('.mind-master-shell') || document.body;
    shell.scrollIntoView();
  });
  const svg = await page.evaluate(() => {
    const mode = document.body.dataset.layoutMode || 'vertical';
    if (mode === 'balanced_two_sided') {
      const target = document.querySelector('.balanced-layout');
      const rect = target.getBoundingClientRect();
      const width = Math.ceil(rect.width);
      const height = Math.ceil(rect.height);
      const clone = target.cloneNode(true);
      const wrapper = document.createElement('div');
      wrapper.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml');
      const style = document.createElement('style');
      style.textContent = Array.from(document.querySelectorAll('style')).map(el => el.textContent || '').join('\\n');
      wrapper.appendChild(style);
      wrapper.appendChild(clone);
      const html = new XMLSerializer().serializeToString(wrapper);
      return '<svg xmlns="http://www.w3.org/2000/svg" width="' + width + '" height="' + height +
        '" viewBox="0 0 ' + width + ' ' + height + '"><foreignObject width="100%" height="100%">' +
        html + '</foreignObject></svg>';
    }
    const markmap = document.querySelector('.markmap svg');
    const clone = markmap.cloneNode(true);
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    return '<!doctype svg>\\n' + clone.outerHTML;
  });
  fs.writeFileSync(svgPath, svg, 'utf8');

  const target = await page.$('.mind-master-shell') || await page.$('body');
  const bounds = await target.boundingBox();
  await target.screenshot({ path: pngPath, omitBackground: false });
  await page.pdf({
    path: pdfPath,
    printBackground: true,
    preferCSSPageSize: false,
    width: Math.ceil((bounds && bounds.width) || 2200) + 'px',
    height: Math.ceil((bounds && bounds.height) || 1500) + 'px',
    margin: { top: '0px', right: '0px', bottom: '0px', left: '0px' }
  });
  const box = await page.evaluate(() => {
    const mode = document.body.dataset.layoutMode || 'vertical';
    const el = mode === 'balanced_two_sided'
      ? document.querySelector('.balanced-layout')
      : document.querySelector('.markmap svg');
    const rect = el.getBoundingClientRect();
    return { width: Math.round(rect.width), height: Math.round(rect.height) };
  });
  await browser.close();
  console.log(JSON.stringify(box));
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
            [
                node,
                script_path,
                str(paths["html"].resolve()),
                str(paths["svg"].resolve()),
                str(paths["png"].resolve()),
                str(paths["pdf"].resolve()),
                str(scale),
                str(timeout_ms),
            ],
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env=node_env(),
            timeout=max(timeout_ms / 1000 + 15, 30),
        )
    finally:
        Path(script_path).unlink(missing_ok=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    data = json.loads(completed.stdout.strip().splitlines()[-1])
    return data


def write_single_page_pdf_from_png(png_path: Path, pdf_path: Path) -> dict:
    if Image is None:
        return {"pdf_mode": "browser_pdf", "reason": "Pillow is not available."}
    with Image.open(png_path) as image:
        rgb = image.convert("RGB")
        rgb.save(pdf_path, "PDF", resolution=144.0)
        return {
            "pdf_mode": "single_page_png_pdf",
            "pdf_source": str(png_path),
            "pdf_page_pixels": {"width": image.width, "height": image.height},
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export Markmap HTML to SVG, PNG, and PDF.")
    parser.add_argument("project", type=Path, help="Mind-Master project path.")
    parser.add_argument("--section-id", help="Export one maps/<section_id>/ workspace.")
    parser.add_argument("--html", type=Path, help="Override HTML path.")
    parser.add_argument("--scale", type=float, default=2)
    parser.add_argument("--node", help="Node.js executable with Playwright available.")
    parser.add_argument("--timeout-ms", type=int, default=60000)
    args = parser.parse_args(argv)

    paths = resolve_paths(args)
    node = find_node(args.node)
    if not node:
        print("Export failed: Node.js is required when Python Playwright is unavailable.", file=sys.stderr)
        return 2
    if not paths["html"].exists():
        print(f"Export failed: missing HTML file: {paths['html']}", file=sys.stderr)
        return 2
    paths["exports"].mkdir(parents=True, exist_ok=True)
    paths["intermediate"].mkdir(parents=True, exist_ok=True)

    try:
        svg_box = export_with_node(paths, node, args.scale, args.timeout_ms)
        pdf_info = write_single_page_pdf_from_png(paths["png"], paths["pdf"])
        report = {
            "passed": True,
            "exported_at": utc_now(),
            "html": str(paths["html"]),
            "svg": str(paths["svg"]),
            "png": str(paths["png"]),
            "pdf": str(paths["pdf"]),
            "scale": args.scale,
            "svg_viewport": svg_box,
            **pdf_info,
        }
        write_json(paths["export_report"], report)
    except Exception as exc:
        report = {"passed": False, "exported_at": utc_now(), "error": str(exc)}
        write_json(paths["export_report"], report)
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1

    print("GATE 8 ✅ Export complete.")
    print("Deliverables:")
    print(f"- html: {project_relative(paths['project'], paths['html'])}")
    print(f"- svg: {project_relative(paths['project'], paths['svg'])}")
    print(f"- png: {project_relative(paths['project'], paths['png'])}")
    print(f"- pdf: {project_relative(paths['project'], paths['pdf'])}")
    print(f"- export report: {project_relative(paths['project'], paths['export_report'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

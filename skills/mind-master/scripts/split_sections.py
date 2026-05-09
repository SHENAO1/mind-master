#!/usr/bin/env python
"""Split a converted Markdown source into per-section mind map workspaces."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # Keep checkpoint symbols printable on Windows consoles.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:  # pragma: no cover - Python implementations without reconfigure
    pass


LESSON_RE = re.compile(r"第\s*([0-9０-９]+)\s*节")
ASCII_SAFE_RE = re.compile(r"[^a-z0-9]+")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def to_project_relative(project_path: Path, path: Path) -> str:
    return path.resolve().relative_to(project_path.resolve()).as_posix()


def normalize_digits(value: str) -> str:
    return value.translate(str.maketrans("０１２３４５６７８９", "0123456789"))


def slug_from_title(title: str, index: int) -> str:
    lesson_match = LESSON_RE.search(title)
    if lesson_match:
        number = int(normalize_digits(lesson_match.group(1)))
        return f"lesson_{number:02d}"

    ascii_title = title.lower().encode("ascii", errors="ignore").decode("ascii")
    slug = ASCII_SAFE_RE.sub("_", ascii_title).strip("_")
    if slug:
        return slug[:48].strip("_")
    return f"section_{index:03d}"


def unique_slug(base: str, used: set[str]) -> str:
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}_{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def heading_pattern(level: int) -> re.Pattern[str]:
    hashes = "#" * level
    return re.compile(rf"^{re.escape(hashes)}\s+(.+?)\s*$")


def split_sections(
    project_path: Path,
    source_path: Path,
    split_level: int,
    sections_dir: Path,
    maps_dir: Path,
    force: bool,
) -> dict[str, Any]:
    if not source_path.exists():
        raise FileNotFoundError(f"Missing source Markdown: {source_path}")

    lines = source_path.read_text(encoding="utf-8").splitlines(keepends=True)
    pattern = heading_pattern(split_level)
    headings: list[tuple[int, str]] = []
    for line_number, line in enumerate(lines, start=1):
        match = pattern.match(line.rstrip("\n\r"))
        if match:
            headings.append((line_number, match.group(1).strip()))

    if not headings:
        raise ValueError(f"No level-{split_level} headings found in {source_path}")

    sections_dir.mkdir(parents=True, exist_ok=True)
    maps_dir.mkdir(parents=True, exist_ok=True)

    used_slugs: set[str] = set()
    sections: list[dict[str, Any]] = []

    for index, (start_line, title) in enumerate(headings, start=1):
        end_line = headings[index][0] - 1 if index < len(headings) else len(lines)
        slug = unique_slug(slug_from_title(title, index), used_slugs)
        section_path = sections_dir / f"{slug}.md"
        section_map_dir = maps_dir / slug

        if section_path.exists() and not force:
            raise FileExistsError(f"Section file exists: {section_path}; pass --force to overwrite.")

        content = "".join(lines[start_line - 1 : end_line])
        section_path.write_text(content.rstrip() + "\n", encoding="utf-8")
        (section_map_dir / "intermediate").mkdir(parents=True, exist_ok=True)
        (section_map_dir / "exports").mkdir(parents=True, exist_ok=True)

        sections.append(
            {
                "id": slug,
                "title": title,
                "source": to_project_relative(project_path, section_path),
                "map_dir": to_project_relative(project_path, section_map_dir),
                "line_start": start_line,
                "line_end": end_line,
            }
        )

    payload = {
        "project": project_path.name,
        "source": to_project_relative(project_path, source_path),
        "split_level": split_level,
        "section_count": len(sections),
        "sections": sections,
        "generated_at": utc_now(),
    }
    index_path = sections_dir / "index.json"
    index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Split intermediate/source.md into one mind map workspace per heading section."
    )
    parser.add_argument("project", type=Path, help="Mind-Master project path.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("intermediate/source.md"),
        help="Markdown source path, relative to project unless absolute.",
    )
    parser.add_argument(
        "--level",
        type=int,
        default=1,
        help="Heading level used as one mind map unit. Default: 1 (#).",
    )
    parser.add_argument(
        "--sections-dir",
        type=Path,
        default=Path("intermediate/sections"),
        help="Output directory for per-section Markdown files.",
    )
    parser.add_argument(
        "--maps-dir",
        type=Path,
        default=Path("maps"),
        help="Output directory for per-section mind map workspaces.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing section files.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    project_path = args.project.resolve()
    source_path = args.source if args.source.is_absolute() else project_path / args.source
    sections_dir = args.sections_dir if args.sections_dir.is_absolute() else project_path / args.sections_dir
    maps_dir = args.maps_dir if args.maps_dir.is_absolute() else project_path / args.maps_dir

    try:
        payload = split_sections(
            project_path=project_path,
            source_path=source_path.resolve(),
            split_level=args.level,
            sections_dir=sections_dir.resolve(),
            maps_dir=maps_dir.resolve(),
            force=args.force,
        )
    except Exception as exc:
        print(f"Section split failed: {exc}", file=sys.stderr)
        return 1

    print("GATE split-sections ✅ Section workspaces created.")
    print("Deliverables:")
    print(f"- section index: {to_project_relative(project_path, sections_dir / 'index.json')}")
    for section in payload["sections"]:
        print(f"- {section['id']}: {section['source']} -> {section['map_dir']}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

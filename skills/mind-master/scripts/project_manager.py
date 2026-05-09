#!/usr/bin/env python
"""Project management CLI for Mind-Master."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from rich.console import Console
except ImportError:  # pragma: no cover - fallback for bootstrap environments
    Console = None  # type: ignore[assignment]


try:  # Keep required checkpoint symbols printable on Windows consoles.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:  # pragma: no cover - Python implementations without reconfigure
    pass


STYLE_CHOICES = ("classic", "logic", "org")
DEFAULT_CANVAS = {"width": 1600, "height": 1000}
REQUIRED_DIRS = (
    "sources",
    "assets",
    "assets/images",
    "assets/equations",
    "intermediate",
    "exports",
    "maps",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def console_print(message: str) -> None:
    try:
        if Console is None:
            print(message)
            return
        Console(legacy_windows=False).print(message)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        print(message.encode(encoding, errors="replace").decode(encoding))


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def resolve_project_path(name_or_path: str, projects_root: Path) -> Path:
    raw = Path(name_or_path)
    if raw.is_absolute() or len(raw.parts) > 1:
        return raw
    return projects_root / name_or_path


def ensure_project_dirs(project_path: Path) -> None:
    for relative in REQUIRED_DIRS:
        (project_path / relative).mkdir(parents=True, exist_ok=True)


def build_manifest(project_path: Path, style: str, model: str | None) -> dict[str, Any]:
    return {
        "project_name": project_path.name,
        "style": style,
        "canvas": DEFAULT_CANVAS,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "model": model or os.getenv("MODEL_NAME", ""),
        "pipeline": "mind-master",
        "sources": [],
        "design": {
            "palette": "mind-master-default",
            "font_stack": 'Inter, "Noto Sans SC", "Microsoft YaHei", "PingFang SC", Arial, sans-serif',
            "max_depth": 4,
            "node_limits": {
                "level_1": "12 Chinese chars or 8 English words",
                "level_2": "18 Chinese chars or 12 English words",
                "leaf": "30 Chinese chars or 20 English words",
            },
            "image_mode": "relative",
            "export_scale": 2,
        },
    }


def init_project(args: argparse.Namespace) -> int:
    project_path = resolve_project_path(args.name, args.projects_root).resolve()
    manifest_path = project_path / "manifest.json"

    if manifest_path.exists() and not args.force:
        console_print(
            f"[red]Project already has manifest:[/red] {manifest_path}\n"
            "Use --force only when you intentionally want to rewrite project metadata."
        )
        return 2

    ensure_project_dirs(project_path)
    manifest = build_manifest(project_path, args.style, args.model)
    if manifest_path.exists() and args.force:
        existing = load_json(manifest_path)
        manifest["created_at"] = existing.get("created_at", manifest["created_at"])
        manifest["sources"] = existing.get("sources", [])
    write_json(manifest_path, manifest)

    console_print("GATE project-init \u2705 Project initialized.")
    console_print("Deliverables:")
    console_print(f"- manifest: {manifest_path}")
    console_print(f"- sources: {project_path / 'sources'}")
    console_print(f"- assets: {project_path / 'assets'}")
    console_print(f"- intermediate: {project_path / 'intermediate'}")
    console_print(f"- exports: {project_path / 'exports'}")
    console_print(f"- maps: {project_path / 'maps'}")
    return 0


def move_source_file(source: Path, sources_dir: Path) -> dict[str, str]:
    if not source.exists():
        raise FileNotFoundError(f"Source file does not exist: {source}")
    if not source.is_file():
        raise ValueError(f"Source path is not a file: {source}")

    destination = sources_dir / source.name
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")

    original_path = source.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    return {
        "original_path": str(original_path),
        "path": str(destination.resolve()),
        "filename": destination.name,
        "imported_at": utc_now(),
    }


def import_sources(args: argparse.Namespace) -> int:
    project_path = Path(args.project).resolve()
    manifest_path = project_path / "manifest.json"
    if not manifest_path.exists():
        console_print(f"[red]Missing manifest:[/red] {manifest_path}")
        return 2

    ensure_project_dirs(project_path)
    manifest = load_json(manifest_path)
    moved: list[dict[str, str]] = []

    try:
        for source_text in args.move:
            moved.append(move_source_file(Path(source_text), project_path / "sources"))
    except Exception as exc:
        console_print(f"[red]Import failed:[/red] {exc}")
        return 1

    manifest.setdefault("sources", []).extend(moved)
    manifest["updated_at"] = utc_now()
    write_json(manifest_path, manifest)

    console_print("GATE import-sources \u2705 Sources moved into project.")
    console_print("Deliverables:")
    for item in moved:
        console_print(f"- moved: {item['path']}")
    console_print(f"- manifest: {manifest_path}")
    return 0


def validate_project(args: argparse.Namespace) -> int:
    project_path = Path(args.project).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    manifest_path = project_path / "manifest.json"
    if not manifest_path.exists():
        errors.append(f"Missing manifest: {manifest_path}")
    else:
        manifest = load_json(manifest_path)
        style = manifest.get("style")
        if style not in STYLE_CHOICES:
            errors.append(f"Invalid manifest style: {style!r}")

    for relative in REQUIRED_DIRS:
        path = project_path / relative
        if not path.exists() or not path.is_dir():
            errors.append(f"Missing directory: {path}")

    if not any((project_path / "sources").glob("*")):
        warnings.append(f"No source files found in {project_path / 'sources'}")

    report = {
        "project": str(project_path),
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "checked_at": utc_now(),
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        if errors:
            console_print("Project validation failed.")
            for error in errors:
                console_print(f"- ERROR: {error}")
        else:
            console_print("Project validation passed.")
        for warning in warnings:
            console_print(f"- WARNING: {warning}")

    return 0 if not errors else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Mind-Master projects.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a project skeleton.")
    init_parser.add_argument("name", help="Project name or project path.")
    init_parser.add_argument("--style", choices=STYLE_CHOICES, default="classic")
    init_parser.add_argument("--projects-root", type=Path, default=Path("projects"))
    init_parser.add_argument("--model", default=os.getenv("MODEL_NAME", ""))
    init_parser.add_argument("--force", action="store_true")
    init_parser.set_defaults(func=init_project)

    import_parser = subparsers.add_parser(
        "import-sources",
        help="Move source files into a project sources directory.",
    )
    import_parser.add_argument("project", help="Project path.")
    import_parser.add_argument(
        "--move",
        nargs="+",
        required=True,
        help="One or more source files to move into sources/.",
    )
    import_parser.set_defaults(func=import_sources)

    validate_parser = subparsers.add_parser("validate", help="Validate project layout.")
    validate_parser.add_argument("project", help="Project path.")
    validate_parser.add_argument("--json", action="store_true")
    validate_parser.set_defaults(func=validate_project)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

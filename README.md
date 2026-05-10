# Mind-Master

Mind-Master is a local, IDE-driven workflow for turning Word or PDF source documents into high-quality mind maps with editable LaTeX math and selectively embedded images or screenshots.

The project follows the same engineering shape as `ppt-master`: one skill entrypoint, reference specs loaded on demand, scriptable pipeline steps, and serial gates between roles. It is not a hosted SaaS. Source files, intermediate artifacts, extracted assets, and final exports stay on the user's disk.

## What It Produces

- Interactive single-file Markmap HTML
- KaTeX-rendered LaTeX equations
- Embedded or relative-path images from the original document
- Optional screenshots captured locally with Playwright after explicit URL confirmation
- SVG, PNG, and PDF exports generated from the HTML

## Project Workspace

Mind-Master is designed to keep each document or document set in its own project folder. If one document contains several lessons or chapters, keep the document in one project and create one map workspace per section:

```text
projects/<project_name>/
├── sources/          # original DOCX/PDF and normalized source material
├── assets/           # images, screenshots, and equation cache
├── intermediate/
│   ├── source.md
│   └── sections/     # optional per-lesson/per-chapter Markdown splits
├── exports/          # optional whole-document HTML, SVG, PNG, and PDF
└── maps/
    └── <section_id>/ # section-specific outline, mindmap, validation, exports
```

Create a project:

```bash
python skills/mind-master/scripts/project_manager.py init <project_name> --style classic
```

Move source files into that project:

```bash
python skills/mind-master/scripts/project_manager.py import-sources projects/<project_name> --move <path/to/document.docx>
```

`projects/*` is ignored by git by default so private source files, extracted images, and exports are not committed accidentally. Shareable finished examples should be copied into a dedicated examples directory rather than stored in the repository root.

Split a converted document into one workspace per H1 section, such as `# 第5节课` and `# 第6节课`:

```bash
python skills/mind-master/scripts/split_sections.py projects/<project_name>
```

## Repository Layout

```text
mind-master/
├── README.md
├── README_CN.md
├── requirements.txt
├── .env.example
├── skills/
│   └── mind-master/
│       ├── SKILL.md
│       ├── references/
│       └── scripts/
│           ├── project_manager.py
│           ├── source_to_md/
│           │   ├── doc_to_md.py
│           │   ├── pdf_to_md.py
│           │   └── web_to_md.py
│           ├── extract_assets.py
│           ├── omml_to_latex.py
│           ├── split_sections.py
│           ├── screenshot_capture.py
│           ├── render_mindmap.py
│           ├── export_mindmap.py
│           └── batch_validate.py
├── templates/
│   └── markmap.html
└── projects/
    └── <project_name>/
        ├── sources/
        ├── assets/
        │   ├── images/
        │   └── equations/
        ├── intermediate/
        │   ├── source.md
        │   └── sections/
        ├── exports/
        └── maps/
            └── <section_id>/
```

## Pipeline

```text
DOCX/PDF
  -> [1. Convert to Markdown]
  -> [2. Initialize Project]
  -> [3. Extract Assets]
  -> [3.5 Split Sections, optional]
  -> [4. Strategist Outline]
  -> [5. Image/Screenshot Decision]
  -> [6. Executor Render]
  -> [7. Formula and Image Validation]
  -> [8. Export]
```

Each step is serial. A step must print a `GATE` checkpoint with delivered paths before the next step starts.

## Core Rules

- No cloud upload by default.
- `project_manager.py import-sources` moves source files into `projects/<name>/sources/`; it does not copy them.
- Executor reads all relevant references in one batch before first generation.
- The first rendered map requires explicit design parameter confirmation.
- External URL screenshots require explicit user confirmation before Playwright opens the URL.
- Equations remain LaTeX text in HTML and are rendered by KaTeX in the browser.

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

System dependencies:

- `poppler` is required by `pdf2image`.
- `tesseract` is optional and enables OCR for image relevance scoring.

Copy `.env.example` to `.env` if you need model or optional OCR/image service configuration. The default local workflow does not require uploading source documents.

## Current Status

The repository now has the Skill entrypoint, reference specs, project management script, initial DOCX-to-Markdown conversion, OMML-to-LaTeX conversion, section splitting, formal Markmap rendering, batch validation, and browser-backed export scripts. PDF/Web input and OCR-backed asset enrichment are still pending.

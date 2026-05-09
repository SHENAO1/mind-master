# Project Workspace

`projects/` is the local workspace for per-document Mind-Master runs.

Each document or document set should get its own project folder:

```text
projects/<project_name>/
├── manifest.json
├── sources/          # original DOCX/PDF and normalized source material
├── assets/
│   ├── images/       # selected figures and screenshots
│   └── equations/    # editable LaTeX equation cache
├── intermediate/     # source.md, outline.json, mindmap.json, validation reports
└── exports/          # HTML, SVG, PNG, PDF for this document
```

Create a project with:

```bash
python skills/mind-master/scripts/project_manager.py init <project_name> --style classic
```

Then move source files into that project:

```bash
python skills/mind-master/scripts/project_manager.py import-sources projects/<project_name> --move <path/to/document.docx>
```

Notes:

- Generated project contents are ignored by git by default.
- This keeps different documents from mixing outputs in the repository root.
- If a result should be shared as a durable example, copy a cleaned version into a dedicated examples directory instead of committing active `projects/<project_name>/` work.

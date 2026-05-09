# Project Workspace

`projects/` is the local workspace for Mind-Master runs.

Each document or document set should get its own project folder. When one document contains multiple lessons or chapters, keep the document in one project and create one map workspace per section:

```text
projects/<project_name>/
├── manifest.json
├── sources/          # original DOCX/PDF and normalized source material
├── assets/
│   ├── images/       # selected figures and screenshots
│   └── equations/    # editable LaTeX equation cache
├── intermediate/
│   ├── source.md
│   └── sections/     # optional per-lesson/per-chapter Markdown splits
├── exports/          # optional whole-document exports
└── maps/
    └── <section_id>/ # section-specific outline, mindmap, validation, exports
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
- For course notes, split by H1 headings such as `# 第5节课` and create one mind map under `maps/lesson_05/`, one under `maps/lesson_06/`, and so on.
- If a result should be shared as a durable example, copy a cleaned version into a dedicated examples directory instead of committing active `projects/<project_name>/` work.

Create section workspaces from converted Markdown:

```bash
python skills/mind-master/scripts/split_sections.py projects/<project_name>
```

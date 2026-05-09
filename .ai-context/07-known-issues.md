# 07 · 已知问题与 Workaround

<!-- 准静态文档。遇到坑就记,解决了在条目下标注"已解决"而非删除。 -->

> **条目格式**:
>
> ### 问题标题
> - **症状**:
> - **定位**:
> - **Workaround**:
> - **状态**: 待解决 / 已解决(YYYY-MM-DD)

---

### 多个 README 中列出的脚本尚未存在
- **症状**: README 和 `SKILL.md` 提到 `pdf_to_md.py`、`web_to_md.py`、`extract_assets.py`、`screenshot_capture.py`、`render_mindmap.py`、`export_mindmap.py`、`batch_validate.py`，但仓库当前只实现了 `project_manager.py`、`doc_to_md.py`、`omml_to_latex.py`。
- **定位**: `skills/mind-master/scripts/` 和 `skills/mind-master/scripts/source_to_md/`。
- **Workaround**: 当前只运行已存在脚本；实现缺失脚本前，把 README 的“当前阶段”视为规划而非已完成能力。
- **状态**: 待解决

### `templates/markmap.html` 尚未实现
- **症状**: README 的结构图列出 `templates/markmap.html`，但当前 `templates/` 只有 `.gitkeep`。
- **定位**: `templates/`。
- **Workaround**: Step 6 渲染脚本实现时同步创建模板，或先在 README 中标注为待实现。
- **状态**: 待解决

### 缺少自动化测试和样例文档
- **症状**: 当前没有 `tests/` 目录，也没有可公开提交的 DOCX/PDF 样例来验证转换质量。
- **定位**: 仓库根目录。
- **Workaround**: 现阶段至少运行 `python -m compileall skills\mind-master\scripts`；后续用合成 DOCX/OMML 样例补测试。
- **状态**: 待解决

### Windows 控制台可能无法打印初始化脚本的勾号
- **症状**: `ai-handoff-init` 实际初始化写完文件后，在最终打印 `✓ wrote ...` 时可能因 GBK 编码报 `UnicodeEncodeError`。
- **定位**: 外部临时克隆的 `ai-handoff-init/scripts/init.py` 最终汇总输出。
- **Workaround**: 文件已写入时可继续；若需要重跑，先设置 `$env:PYTHONIOENCODING='utf-8'`。
- **状态**: 待解决

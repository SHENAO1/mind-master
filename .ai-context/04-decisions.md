# 04 · 决策日志(ADR)

<!-- 追加型文档。每次做出架构/技术/流程上的决策,在顶部加一条。 -->

> 删除决策 = 删历史。作废的决策写"推翻先前决策(见 YYYY-MM-DD 条目)"而不是移除。

## 模板(复制使用)

```markdown
## YYYY-MM-DD · 决策标题

**背景**: 为什么需要做这个决定?触发事件是什么?

**选项**:
- A: ...
- B: ...

**决策**: 选择 X。

**理由**: ...

**影响**: 哪些文件/模块会被改?哪些约定被确立?

**状态**: 生效 / 已推翻(见 YYYY-MM-DD)
```

---

## 2026-05-10 · Source-faithful learning poster 节点压缩与派生元数据

**背景**: 第 5 节已具备五类图片决策、裁剪、callout 和图片可读性校验，但节点仍偏“文档摘要”，中心主题、图标体系、短编号句和派生学习内容没有进入可验证数据结构。用户要求吸收 GPT Image 2 参考图的表达方式，同时禁止伪造原文不存在的 `5.2.3`、`5.4`、`5.5` 等章节编号。

**选项**:
- A: 继续让 prompt/reference 要求“写短一点”，不在 mindmap 数据或验证器中新增字段。
- B: 在 lesson/profile 层引入 source-backed learning points、icon metadata、derived/grounded_hint/derived_from 元数据，并用验证器阻塞未标记派生节点、伪章节编号、跨 section 自动补抽和半词硬截断。

**决策**: 选择 B。

**理由**: 学习型导图需要让短句、图标、派生提示和来源追踪成为结构化输出，而不是只靠视觉模板；验证器能防止为了接近参考图而把关键词、Momentum 优势或调参启示伪装成原文章节。

**影响**: 更新 `SKILL.md`、Strategist/Executor/Format/Image references、`render_mindmap.py`、`batch_validate.py`、`templates/markmap.html` 与回归测试。`lesson_05` 使用 `gpt_image2_inspired_source_faithful` profile：中心卡片强化为课程标题与核心主题，Batch 在左侧，Momentum/小结在右侧，关键词与调参启示为 `[*]` 派生区域；新增 `derived_node_labeling` 与 `text_compression` 校验。

**状态**: 生效

## 2026-05-10 · 学习型导图五类图片策略与可读性校验

**背景**: 第 5 节最新回归显示图片已经能嵌入节点，但整图缩小后教学价值不足；学习型导图需要判断图片是否该全图保留、裁剪、结构化高保真重绘、概念化重绘或省略，并在最终 PNG/PDF 中验证图像确实可读。

**选项**:
- A: 沿用 `preserve` / `crop_preserve` / `redraw` / `omit` 四分法，仅通过人工调整图片大小改善阅读。
- B: 升级为 `preserve_full` / `preserve_crop` / `redraw_high_fidelity` / `redraw_concept` / `omit` 五分法，同时要求每张保留或重绘图有 source-backed callout、crop metadata 和最终渲染尺寸校验。

**决策**: 选择 B。

**理由**: 五分法能区分“整图证据”“裁剪证据”“必须保留结构的重绘”和“只需概念示意”的不同学习用途；callout 与浏览器实测尺寸校验可以防止图片只是缩小塞进卡片而不可读。

**影响**: 更新 `SKILL.md`、Strategist/Executor/Image/Format references、`extract_assets.py`、`render_mindmap.py`、`batch_validate.py`、`templates/markmap.html` 与回归测试。`lesson_05` 最新决策为 `fig_p38_004=preserve_full`、`fig_p46_006/fig_p56_007/fig_p63_008=preserve_crop`、`fig_p32_003=redraw_high_fidelity`、`fig_p23_002/fig_p43_005=omit`；新增 `forbidden_section_numbers`、`image_readability`、`crop_metadata`、`image_callout_grounding` 校验。

**状态**: 生效

## 2026-05-10 · GPT Image 2 inspired source-faithful profile 与四分图像策略

**背景**: 第 5 节复盘确认 GPT Image 2 参考导图在中心锚点、左右分支、编号列表和视觉记忆点上更清晰，但参考图引入了原文不存在的 `5.2.3`、`5.4`、`5.5` 等章节编号。此前三分法也无法表达“原图有价值但应裁剪重点区域后嵌入”的学习导图需求。

**选项**:
- A: 继续 `preserve` / `redraw` / `omit` 三分法，并只用 SVG 重绘处理截图类教学图。
- B: 扩展为 `preserve` / `crop_preserve` / `redraw` / `omit` 四分法，同时新增 source-faithful 视觉 profile 和伪章节编号校验。

**决策**: 选择 B。

**理由**: `crop_preserve` 能保留关键原文证据和视觉记忆点，同时避免整页截图占据过多画布；章节编号白名单和 source_span 约束可以防止为了 GPT Image 2 式视觉组织而牺牲原文真实性。

**影响**: 更新 `SKILL.md`、Strategist/Executor/Image/Format references、`extract_assets.py`、`render_mindmap.py`、`batch_validate.py`、`templates/markmap.html` 与回归测试。`lesson_05` 使用 Batch 左侧、Momentum/小结右侧、关键词底部胶囊条，图像决策为 1 preserve、3 crop_preserve、1 redraw、2 omit。

**状态**: 已推翻(见 2026-05-10 · 学习型导图五类图片策略与可读性校验)

## 2026-05-10 · 图像策略改为 preserve/redraw/omit 三分法

**背景**: 第二轮把 DOCX 截图禁止直嵌后,5 张截图被替换成高度相似的通用曲线占位图,没有真实信息价值。对比纯文字导图后确认:思维导图应以结构化文字为主,图像只作为少量例外。

**选项**:
- A: 继续截图默认重绘,逐步丰富重绘提示。
- B: 改为 `preserve` / `redraw:<template_id>` / `omit` 三分法,默认 `omit`;只有真实数据图可 preserve,只有注册 SVG 模板可 redraw。

**决策**: 选择 B,并推翻先前“DOCX 截图默认作为 SVG 重绘语义引用”的默认重绘部分。

**理由**: 默认重绘会把低价值截图变成低价值占位 SVG;默认 omit 能强制节点文字承载信息。注册模板限制可以防止通用占位曲线再次进入最终 HTML。

**影响**: 更新 `image-policy.md`、`SKILL.md`、Strategist/Executor references、`extract_assets.py`、`render_mindmap.py`、`batch_validate.py`;新增 `assets/svg_templates/` 和 `tests/` 回归。验证新增 `placeholder_curve_detection`、keywords、summary、H3 density 等阻塞检查。

**状态**: 已推翻(见 2026-05-10 · GPT Image 2 inspired source-faithful profile 与四分图像策略)

## 2026-05-10 · DOCX 截图默认作为 SVG 重绘语义引用

**背景**: 第 5 节第二轮回归中,虽然 reference 写过“截图优先重绘”,但 6 张卡片里 5 张仍直接嵌入原 DOCX 截图,小图不可读且削弱脑图结构。

**选项**:
- A: 继续依赖 Strategist/Executor 的文字规则,由助手人工判断是否嵌图。
- B: 在资产索引、渲染器和验证器三层落地硬约束:资产写入 `type` / `redraw_required`,渲染器把截图类资产转为 `redraw`,验证器阻塞 `<img>` 直嵌。

**决策**: 选择 B。

**理由**: 失败根因是规则停在 reference 层,没有进入中间数据和脚本执行层。把分类字段写入 `assets/images/index.json` 并由 `render_mindmap.py`、`batch_validate.py` 消费,可以让策略可验证、可回归。

**影响**: 新增 `extract_assets.py`;更新 `render_mindmap.py`、`batch_validate.py`、`templates/markmap.html`、`SKILL.md` 和 references。截图类 DOCX/PDF/slide/photo 资产默认 `redraw_required: true`,除明确标为可读 `data_chart` 外不得直接嵌入。

**状态**: 已推翻(见 2026-05-10 · 图像策略改为 preserve/redraw/omit 三分法)

## 2026-05-10 · 密集导图采用 layout_profile 驱动的双侧语义布局

**背景**: 第 5 节课程内容包含 27 个导图节点、7 张教学图、1 张表和 1 个公式，默认 Markmap 容易导出为纵向长条，PNG/PDF 阅读体验差。

**选项**:
- A: 继续使用默认 Markmap 单向布局，并靠缩小画布或删减图片改善高度。
- B: 增加 `layout_profile` 密度画像，密集内容自动切换到 `balanced_two_sided`；HTML 用语义化左右双栏流式布局承载同一份 mindmap 数据，导出仍来自 HTML。

**决策**: 选择 B。

**理由**: `layout_profile` 可以把布局触发原因和分支权重写入可验证数据结构；双侧流式布局避免固定坐标海报，也不需要为了美观删除 H2/H3、表格、公式或源图决策。

**影响**: 更新 `render_mindmap.py`、`templates/markmap.html`、`export_mindmap.py`、`batch_validate.py` 和 Skill references；第 5 节回归产物新增 `layout_self_check.md`，校验新增布局画像、长宽比、左右权重和 source fidelity 检查。

**状态**: 生效

## 2026-05-09 · 初始化跨助手上下文

**背景**: 项目需要让 Codex、Claude Code 和 GitHub Copilot 共享当前完成度、架构说明、决策与下一步，避免每次切换助手都重新说明。

**选项**:
- A: 只在 README 中记录状态。
- B: 使用 `ai-handoff-init` 生成 `.ai-context/` 和三个薄入口文件。

**决策**: 选择 B。

**理由**: `.ai-context/` 把静态架构、动态状态、会话日志、决策和已知问题拆开，适合多助手交接；薄入口文件能兼容 Codex、Claude Code 和 Copilot。

**影响**: 新增 `.ai-context/`、`AGENTS.md`、`CLAUDE.md`、`.github/copilot-instructions.md`，后续助手进入和结束会话时都必须维护这些文件。

**状态**: 生效

## 2026-05-09 · 采用 local-first 串行 GATE 流水线

**背景**: Mind-Master 处理的输入可能是用户本地 Word/PDF 文档，内容可能敏感；同时文档转导图涉及转换、资产、规划、渲染、验证、导出多个阶段。

**选项**:
- A: 构建云端托管服务并并行执行阶段。
- B: 构建本地优先、串行推进、每步 GATE 交接的脚本化流水线。

**决策**: 选择 B。

**理由**: 本地优先降低隐私风险；串行 GATE 让每一步的输入输出可审计，方便 AI 助手和用户确认后继续。

**影响**: `SKILL.md`、README 和 references 都以八步流水线组织；脚本输出需要列出交付物路径。

**状态**: 生效

## 2026-05-09 · 公式保持 LaTeX 文本并由 KaTeX 渲染

**背景**: Word/PDF 转思维导图时，公式需要在导图中可读且可编辑，不能只作为低质量截图嵌入。

**选项**:
- A: 把公式转换为图片。
- B: 将 OMML 等来源转换为 LaTeX 文本，在 HTML 中用 KaTeX 渲染。

**决策**: 选择 B。

**理由**: LaTeX 文本便于审查、修改和版本控制，KaTeX 在浏览器中渲染稳定，也符合导出前验证需求。

**影响**: 已实现 `omml_to_latex.py`，DOCX 转换脚本会写入 `.tex` 缓存；后续渲染和验证必须检查 KaTeX 错误。

**状态**: 生效

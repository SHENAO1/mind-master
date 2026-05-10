# 06 · 会话日志

<!-- 动态文档。每次会话结束在最上方追加一条。**新的在上**。 -->

> **条目格式 / Entry format**:
>
> ```
> ## YYYY-MM-DD · <助手名 / Assistant name>
> **完成 / Done**: ...
> **进行中 / In progress**: ...
> **下一步建议 / Next**: ...
> **注意 / Watch out**: ...
> ```
>
> **归档规则**:当本文件条目超过 20 条时,把较早的一半移动到 `06-session-log-archive.md`
> (或按月切片到 `archive/YYYY-MM.md`)。这是为了避免文件超过 Claude Code 单文件 40 000
> 字符上限,同时降低 Codex 的 `project_doc_max_bytes` 截断风险。归档的助手请同时在
> 本文件底部留一行链接指向归档文件。
---


## 2026-05-10 · Codex
**完成 / Done**: 将 `lesson_05` 从可读学习导图继续压缩为 16:9 成品级学习海报：导出裁切到 `.balanced-layout`，SVG 从 `2100x1627` 改为 `2360x1331`；H2 主牌增强，图证卡改为媒体 + 结论栏，`fig_p32_003` 与 `fig_p38_004` 并排，`fig_p46_006` 裁剪收紧，表 5-1 改为 compact comparison matrix，`5.3 本章小结` 做成橙色总结区，底部学习增强带固定三栏且最多渲染 10 个关键词。
**进行中 / In progress**: 已重新运行 `extract_assets.py`、`render_mindmap.py`、`export_mindmap.py`、`batch_validate.py` 和 unittest。`poster_packing`、`batch_height_compactness`、`evidence_compactness`、`learning_band_compactness` 以及既有 source fidelity / layout / evidence / bottom band / connector 校验全部通过。
**下一步建议 / Next**: 将新增 poster packing 与 evidence compactness 规则推广到第 6-8 节，重点观察多公式、多图章节是否需要章节级阈值或更多证据卡模板。
**注意 / Watch out**: 新增布局指标依赖浏览器实测；跳过浏览器时会标记 skipped。`projects/ml_theory2_test/` 仍是 ignored 回归产物，不会出现在普通 `git status` 中。

## 2026-05-10 · Codex
**完成 / Done**: 将 `lesson_05` 从 source-faithful 导图继续升级为 `compact_learning_poster`：中心卡片更强，左右分支收拢，图片节点改为带 `evidence_title`、图号、图像/重绘和 source-backed callout 的图证卡；关键词、调参启示和 Momentum 优势合并为单条底部学习增强带；连接线变细并降低透明度。
**进行中 / In progress**: 已重新抽取素材、渲染、导出并验证 `projects/ml_theory2_test/maps/lesson_05`；HTML/SVG/PNG/PDF 均生成。新增 `layout_aesthetics`、`evidence_card_quality`、`bottom_learning_band`、`connector_noise` 校验全部通过，既有 source fidelity 校验也全部通过。
**下一步建议 / Next**: 将 compact poster 规则推广到第 6-8 节，重点复核不同章节的图证卡阈值、底栏高度和连接线是否需要章节级参数。
**注意 / Watch out**: `layout_aesthetics` 依赖浏览器实测；跳过浏览器时该类版面检查会标记 skipped。当前生成产物仍在 ignored 的 `projects/ml_theory2_test/`。

## 2026-05-10 · Codex
**完成 / Done**: 根据用户最新导图截图、源 Word 第 5 节和联网思维导图样例做优化复盘。确认当前版本已完成 source-faithful、图片裁剪、callout、派生节点和可读性校验；下一步重点应转向 poster compaction、图证卡设计、中心锚点强化、连接线降噪和版面质量自动检测。
**进行中 / In progress**: 本轮未修改生成代码；给出下一步 Skill 优化方向和可直接使用的提示词。
**下一步建议 / Next**: 新增 layout aesthetics/readability gates：空白率、中心偏移、节点到中心距离、图证卡最小面积、底栏密度、连接线覆盖率；将 `lesson_05` 专用规则抽象为跨章节策略后回归第 6-8 节。
**注意 / Watch out**: 继续禁止把联网样例或 GPT Image 2 的派生内容伪装成原文章节；外部样例只作为视觉结构参考。

## 2026-05-10 · Codex
**完成 / Done**: 继续优化 Mind-Master 为 source-faithful 学习型 poster：`lesson_05` 节点压缩为可追溯 source_quote/source_span 的编号短句，中心卡片强化为课程标题与核心主题；新增图标 metadata 与 HTML 线性图标渲染；Momentum 优势、关键词、调参启示改为 `[*]` 派生/grounded hint 节点并记录 `derived_from`，禁止伪装成原文章节。
**进行中 / In progress**: 已重新抽取素材、渲染、导出并验证 `projects/ml_theory2_test/maps/lesson_05`；HTML/SVG/PNG/PDF 均已生成，`batch_validate.py` 通过。最新图片决策：`fig_p38_004=preserve_crop`，`fig_p46_006=preserve_crop`，`fig_p56_007=preserve_crop`，`fig_p63_008=preserve_crop`，`fig_p32_003=redraw_high_fidelity`，`fig_p23_002/fig_p43_005=omit`。
**下一步建议 / Next**: 将短句压缩、图标 metadata、派生节点标记和图片 callout/readability 规则推广到第 6-8 节；减少 `lesson_05` 专用映射，沉淀为通用 Strategist/Executor 生成逻辑。
**注意 / Watch out**: 新增校验 `derived_node_labeling` 与 `text_compression` 已纳入 source_fidelity；派生节点必须带 `derived`/`grounded_hint` 和来源，自动补抽不得跨 section。生成产物仍在 ignored 的 `projects/ml_theory2_test/`。

## 2026-05-10 · Codex
**完成 / Done**: 将 Mind-Master 升级为学习型导图图片策略：Skill/reference/scripts/tests 统一到 `preserve_full` / `preserve_crop` / `redraw_high_fidelity` / `redraw_concept` / `omit` 五类；保留/重绘图新增 source-backed callout，裁剪图新增 `crop_focus`/`crop_reason`，验证器新增 `forbidden_section_numbers`、`image_readability`、`crop_metadata`、`image_callout_grounding`。同时收紧 `source_faithful_poster`/GPT Image 2 inspired 双侧布局，图片学习卡横跨子网格并降低连接线视觉重量。
**进行中 / In progress**: 已重新抽取素材、渲染、导出并验证 `projects/ml_theory2_test/maps/lesson_05`；HTML/SVG/PNG/PDF 均已生成，`batch_validate.py` 通过。最终图片决策：`fig_p38_004=preserve_full`，`fig_p46_006/fig_p56_007/fig_p63_008=preserve_crop`，`fig_p32_003=redraw_high_fidelity`，`fig_p23_002/fig_p43_005=omit`。
**下一步建议 / Next**: 将同一五类图片策略应用到第 6-8 节；继续把 outline 生成产品化，减少手工 outline 维护，并扩展更多高保真 redraw template。
**注意 / Watch out**: 新策略已推翻上一轮四分法命名；旧 `preserve` / `crop_preserve` / `redraw` 只能作为兼容输入，最终输出和校验必须使用五类决策。生成产物仍在 ignored 的 `projects/ml_theory2_test/`。

## 2026-05-10 · Codex
**完成 / Done**: 实现 “GPT Image 2 inspired but source-faithful” Mind-Master profile：Skill/reference 同步四分图像策略 `preserve` / `crop_preserve` / `redraw` / `omit`，渲染器新增裁剪派生产物，验证器新增伪章节编号白名单和 figure decision value 检查，自动密度补抽改为只使用所属 `source_span` 且不硬截断英文词。
**进行中 / In progress**: 已重新生成 `projects/ml_theory2_test/maps/lesson_05` 并导出 HTML/SVG/PNG/PDF；`batch_validate.py` 完整通过，浏览器检查 `katexErrors=0`、`imageCount=4`、`connectorCount=11`。图片决策为 `fig_p38_004=preserve`，`fig_p46_006/fig_p56_007/fig_p63_008=crop_preserve`，`fig_p32_003=redraw`，`fig_p23_002/fig_p43_005=omit`。
**下一步建议 / Next**: 用同一 profile 回归第 6-8 节；如需更高图片可读性，可为每类教学截图补充更精细的 per-figure `crop_box` 或注册 SVG 模板。
**注意 / Watch out**: `crop_preserve` 会生成 `assets/images/crops/*_crop.png` 派生产物；原始 screenshot/slide/photo 仍不得作为 raw `<img>` 直嵌。关键词和调参启示必须保持 `[*]` 派生节点，不得伪装成源文章节。

## 2026-05-10 · Codex
**完成 / Done**: 复盘第 5 节 Word 原文、当前 Skill 导图和用户提供的 GPT Image 2 参考导图。确认当前版本覆盖原文 5.1/5.2/5.3、表 5-1、公式 5-1 和图片决策，源保真优于参考图；同时指出 GPT Image 2 风格在中心主题、图标、编号列表和紧凑横向阅读上更成熟。
**进行中 / In progress**: 本轮未改生成代码；结论是下一版应走 “GPT Image 2 inspired but source-faithful” 混合方案，把关键原文截图/裁剪图嵌入高层节点，同时保留 source_quote 和校验。
**下一步建议 / Next**: 优先实现图像 salience 评分与 crop/callout 机制，重点保留或高保真重绘 `fig_p38_004`、`fig_p46_006`、`fig_p56_007`、`fig_p63_008`，可选加入 `fig_p32_003`；修复自动密度补抽跨 section 和硬截断问题。
**注意 / Watch out**: GPT Image 2 参考图含原文不存在的 `5.2.3 Momentum 的优势`、`5.4 关键词`、`5.5 调参启示` 等编号；若加入关键词/调参启示，应作为非编号派生节点并标记来源。

## 2026-05-10 · Codex
**完成 / Done**: 完成第三轮 Mind-Master 迭代：将图像策略从“直嵌 vs 重绘”改为 `preserve` / `redraw:<template_id>` / `omit` 三分法且默认 omit；新增 `assets/svg_templates/` 三个注册模板；`extract_assets.py` 产出 `decision_hint` / `redraw_template_id`，`render_mindmap.py` 删除通用占位曲线并按模板/omit 执行，`batch_validate.py` 新增占位曲线、keywords、小结完整句、H3 密度等阻塞检查。同步更新 SKILL 与 references，新增 unittest 回归和 `pipeline_regression_fixture.docx`。
**进行中 / In progress**: 已用最新链路重跑 `projects/ml_theory2_test` 的 `lesson_05`：决策矩阵为 `fig_p38_004=preserve`，`fig_p32_003/fig_p46_006/fig_p63_008=redraw:<template>`，`fig_p23_002/fig_p43_005/fig_p56_007=omit`；浏览器校验通过，PNG/PDF 已导出，`python -m unittest discover -s skills/mind-master/tests -p "test_*.py"` 7 项通过。
**下一步建议 / Next**: 用同一三分法重跑第 6-8 节，重点观察真实数据图误判、模板覆盖不足和 H3 自动补抽是否需要章节级微调；继续把 outline 生成产品化。
**注意 / Watch out**: 新策略推翻了“截图默认重绘”的默认行为；没有注册模板的截图会 omit，所以节点文字密度必须足够。生成产物仍在 ignored 的 `projects/ml_theory2_test/`。

## 2026-05-10 · Codex
**完成 / Done**: 基于第 5 节第二轮失败案例继续迭代 Mind-Master Skill：新增 `extract_assets.py` 生成 `type` / `is_data_chart` / `redraw_required`；`render_mindmap.py` 会把 screenshot/slide/photo 或 `redraw_required=true` 的资产转为 `redraw` 并渲染 SVG 重绘占位；`batch_validate.py` 新增 `source_image_policy`、`section_numbering`、`tips_grounding`、`summary_sentence_checks` 等阻塞校验。同步更新 SKILL 和 references，强化截图不得直嵌、章节编号保真、H2/H3 两级结构、紧凑卡片、keywords/tips 和小结完整句规则。
**进行中 / In progress**: 已完整回归 `projects/ml_theory2_test` 的 `lesson_05`：Step 3/6/7/8 通过，浏览器校验 `balanced_two_sided`、`connectorCount=11`、`katexErrors=0`、`imageCount=0`；7 张第 5 节源图均转为 `redraw`，PNG 4400x3040，PDF 仍为 `single_page_png_pdf`。
**下一步建议 / Next**: 将本轮新增校验拆成最小 fixtures/单元测试，尤其覆盖截图拦截、section_id 层级、无 tips 段落不生成 tips；再用第 6-8 节回归确认多图/多公式章节不会误拦截真实 data_chart。
**注意 / Watch out**: `extract_assets.py` 当前使用启发式分类；真实数据图若需要保留原图，需在资产索引中显式设为 `type: "data_chart"`, `is_data_chart: true`, `redraw_required: false`。生成产物位于 ignored 的 `projects/ml_theory2_test/`。

## 2026-05-10 · Codex
**完成 / Done**: 针对用户指出的 PDF 跨页和连接线断开问题做修正：连接线从静态百分比路径改为浏览器按真实 DOM 位置动态计算；PDF 导出从 Chromium 打印页改为高分辨率 PNG 生成单页 PDF。重新生成 `lesson_05` 并验证通过，`export.json` 记录 `pdf_mode=single_page_png_pdf`、PNG 4400x2412、SVG 2200x1120，`validation.json` 记录 `connectorCount=11`、7 张图、2 个 KaTeX 节点。
**进行中 / In progress**: 最新第 5 节导出位于 `projects/ml_theory2_test/maps/lesson_05/exports/`；本地预览服务仍可用于查看。
**下一步建议 / Next**: 如果用户希望更像参考图，可继续优化连接线层级和分支分布：增加分支图标、粗细渐变、关键词带，以及将源图可选压缩/裁剪成更小的教学图块。
**注意 / Watch out**: 单页 PDF 是 PNG 栅格化 PDF，优势是不会分页且视觉稳定；若后续需要可复制文本的矢量 PDF，需要再做打印 CSS 的单页 page-size 修复。

## 2026-05-10 · Codex
**完成 / Done**: 根据用户反馈继续优化第 5 节导图视觉形式：将双栏卡片改为横向中心放射式布局，新增根节点到分支、分支到子卡片的 SVG 连接曲线；叶子节点改成紧凑列表，图片缩略图缩小，Batch 子内容用网格围绕 Batch 枢纽分布。重新生成并导出 `lesson_05`，验证通过：SVG 2200x1120，PNG 高宽比约 0.55，`connectorCount=12`，7 张图和 KaTeX 均通过。
**进行中 / In progress**: 本地预览服务仍在 `http://127.0.0.1:8765/maps/lesson_05/exports/lesson_05.png`；浏览器对带缓存参数的 PNG URL 报 `ERR_BLOCKED_BY_CLIENT`，但原始 URL 本地 HTTP 返回 200，用户手动刷新即可看新版。
**下一步建议 / Next**: 用户查看新版后，继续按参考图微调分支曲线粗细、中心卡片尺寸、图片缩略图取舍或是否增加“关键词/调参启示”类源内节点。
**注意 / Watch out**: 仍需避免新增源文档不存在的章节；当前输出没有凭空添加 5.4/5.5，保留原 H2/H3、表格、公式和图片决策。

## 2026-05-10 · Codex
**完成 / Done**: 按用户要求重新生成第 5 节导图：运行 `render_mindmap.py`、`export_mindmap.py`、`batch_validate.py`，产物更新到 `projects/ml_theory2_test/maps/lesson_05/`；验证通过并在本地 HTTP 预览中确认 `balanced_two_sided` 页面结构。
**进行中 / In progress**: 本地预览服务运行在 `http://127.0.0.1:8765/maps/lesson_05/exports/lesson_05.html`，进程 PID 49784；该服务只用于查看静态导出。
**下一步建议 / Next**: 用户查看第 5 节效果后，根据反馈微调双侧布局密度、图片大小或表格宽度。
**注意 / Watch out**: 回归产物位于 ignored 的 `projects/ml_theory2_test/maps/lesson_05/`；代码和 reference 改动仍未提交。

## 2026-05-10 · Codex
**完成 / Done**: 为 Mind-Master 增加 `layout_profile` 自适应布局能力：更新格式/Executor/Image Policy references；`render_mindmap.py` 可生成密度画像、分支权重和 `layout_self_check.md`，密集内容切换为双侧语义 HTML；`export_mindmap.py` 兼容双侧布局导出；`batch_validate.py` 新增 layout profile、长宽比、左右权重和 source fidelity 检查。用 `lesson_05` 重跑 Step 6-8，触发 `balanced_two_sided`，PNG 比例 0.91、SVG 比例 1.2，7 张图、表 5-1、公式 5-1、H2/H3 覆盖均通过。
**进行中 / In progress**: 回归产物仍在 ignored 的 `projects/ml_theory2_test/maps/lesson_05/`；主代码和 reference 文件有未提交改动，等待用户确认或后续提交。
**下一步建议 / Next**: 用同一自适应链路重跑 `lesson_06`，观察多公式/多图章节是否需要调阈值或表格宽度策略；继续把 source-faithful outline 生成自动化。
**注意 / Watch out**: 双侧模式用 HTML 语义布局解决 Markmap 难控左右分布的问题，但主数据仍是 `mindmap.json`/`mindmap.md`；浏览器截图工具对当前大页面截图超时，脚本级 Playwright 导出和 browser validation 已通过。

---

历史归档 / Archive: [06-session-log-archive.md](06-session-log-archive.md)

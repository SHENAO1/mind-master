import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = REPO_ROOT / "skills" / "mind-master"
SCRIPTS_DIR = SKILL_DIR / "scripts"


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_png(path: Path, label: str, size=(640, 360)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, size[0] - 16, size[1] - 16), outline=(45, 105, 180), width=4)
    draw.line((60, size[1] - 70, 180, size[1] - 130, 320, size[1] - 100, size[0] - 70, 70), fill=(45, 105, 180), width=5)
    draw.text((32, 32), label, fill=(25, 35, 55))
    image.save(path)


def build_fixture_project(base_dir: Path) -> Path:
    project = base_dir / "fixture_project"
    images_dir = project / "assets" / "images"
    section_dir = project / "intermediate" / "sections"
    map_intermediate = project / "maps" / "lesson_05" / "intermediate"

    for directory in [images_dir, section_dir, map_intermediate, project / "maps" / "lesson_05" / "exports"]:
        directory.mkdir(parents=True, exist_ok=True)

    write_png(images_dir / "data_curve.png", "Batch Size vs Time", (640, 360))
    write_png(images_dir / "slide_screen.png", "Slide Screenshot", (520, 340))
    write_png(images_dir / "sharp_flat.png", "Sharp vs Flat", (520, 340))
    write_png(images_dir / "momentum_ball.png", "Momentum physical analogy", (720, 520))

    source = """# 第5节课 测试

本节围绕 Batch Size、Epoch、Shuffle、Noisy Gradient、Local Minima、Saddle Points、Flat Minima、Sharp Minima、Momentum、Gradient、Loss 与 GPU 展开。

## 5.1 Batch

Batch 说明训练时把数据拆成批次，并用 Loss 与 Gradient 更新参数。

### 5.1.1 Batch的定义

Batch Size 指单次迭代中用于计算梯度并更新参数的训练样本数量。
Epoch 指训练过程完整遍历一遍所有训练数据集。
Shuffle 会在每个 Epoch 开始前打乱数据顺序。
训练流程是取一个 Batch、计算 Loss 和 Gradient、更新参数，然后处理下一个 Batch。

![data](assets/images/data_curve.png)

图5-1 不同 Batch Size 下的单次更新时间&单个epoch时间对比图，范围包含 1~1000、10000 与 60000。

![slide](assets/images/slide_screen.png)

图5-2 课程截图，文字已经覆盖其含义。

![concept](assets/images/sharp_flat.png)

图5-3 Sharp Minima vs Flat Minima registered template。

### 5.1.2 Batch的作用

较大的 Batch Size 借助 GPU 平行计算可以缩短一个 Epoch 的训练时间。
小 Batch Size 产生的 Noisy Gradient 更容易跳出 Local Minima。
小 Batch Size 也有助于跨过 Saddle Points。
Flat Minima 比 Sharp Minima 更有利于泛化。

## 5.2 Momentum

Momentum 通过模拟物理惯性，使参数更新参考历史方向。

### 5.2.1 Momentum概念

Momentum 的目的是帮助梯度下降克服鞍点或局部最优解。
物理类比是小球滚下斜坡时会借助惯性越过洼地。
历史方向会和当前梯度共同影响更新方向。
这种方向积累能帮助模型继续向较优区域移动。

![momentum](assets/images/momentum_ball.png)

图5-4 Momentum物理类比图

## 5.3本章小结

Batch Size 是训练效率与泛化能力之间的折中。
Momentum 通过引入历史方向，为训练过程增添惯性。
"""
    (project / "intermediate").mkdir(parents=True, exist_ok=True)
    (project / "intermediate" / "source.md").write_text(source, encoding="utf-8")
    (section_dir / "lesson_05.md").write_text(source, encoding="utf-8")
    write_json(section_dir / "index.json", {"sections": [{"id": "lesson_05", "title": "第5节课 测试"}]})

    write_json(
        project / "manifest.json",
        {
            "project_name": "fixture_project",
            "style": "classic",
            "canvas": {"width": 1600, "height": 1000},
            "design": {"palette": "mind-master-default"},
        },
    )
    write_json(
        project / "intermediate" / "source_assets.json",
        {
            "images": [
                {
                    "id": "data_fig",
                    "path": "assets/images/data_curve.png",
                    "alt": "Batch Size vs Time data chart",
                    "source_anchor": "p1",
                    "type": "data_chart",
                    "is_data_chart": True,
                },
                {
                    "id": "slide_fig",
                    "path": "assets/images/slide_screen.png",
                    "alt": "Image extracted from slide",
                    "source_anchor": "p2",
                    "type": "screenshot",
                },
                {
                    "id": "concept_fig",
                    "path": "assets/images/sharp_flat.png",
                    "alt": "Image extracted from sharp flat concept",
                    "source_anchor": "p3",
                    "type": "screenshot",
                },
                {
                    "id": "momentum_fig",
                    "path": "assets/images/momentum_ball.png",
                    "alt": "Image extracted from Momentum physical analogy",
                    "source_anchor": "p4",
                    "type": "screenshot",
                },
            ]
        },
    )

    outline = {
        "root": "第5节课 测试",
        "source_title": "第5节课 测试",
        "style": "classic",
        "max_depth": 4,
        "description": "训练时如何在效率、泛化与方向惯性之间取舍。",
        "nodes": [
            {
                "id": "n_batch",
                "title": "Batch",
                "description": "Batch 说明训练时把数据拆成批次。",
                "source_quote": "Batch 说明训练时把数据拆成批次",
                "children": [
                    {
                        "id": "n_batch_def",
                        "title": "Batch定义",
                        "description": "Batch Size 定义单次迭代样本数量。",
                        "source_quote": "Batch Size 指单次迭代中用于计算梯度并更新参数的训练样本数量",
                        "children": [
                            {"id": "n_b1", "title": "Batch Size 定义样本数量", "source_quote": "Batch Size 指单次迭代中用于计算梯度并更新参数的训练样本数量"},
                            {"id": "n_b2", "title": "Epoch 是完整遍历数据", "source_quote": "Epoch 指训练过程完整遍历一遍所有训练数据集"},
                            {"id": "n_b3", "title": "Shuffle 会打乱数据顺序", "source_quote": "Shuffle 会在每个 Epoch 开始前打乱数据顺序"},
                        ],
                    },
                    {
                        "id": "n_batch_effect",
                        "title": "Batch作用",
                        "description": "Batch Size 会影响训练效率与泛化。",
                        "source_quote": "较大的 Batch Size 借助 GPU 平行计算可以缩短一个 Epoch 的训练时间",
                        "children": [
                            {"id": "n_e1", "title": "大 Batch 缩短 Epoch 时间", "source_quote": "较大的 Batch Size 借助 GPU 平行计算可以缩短一个 Epoch 的训练时间"},
                            {"id": "n_e2", "title": "Noisy 梯度跳出局部最小", "source_quote": "小 Batch Size 产生的 Noisy Gradient 更容易跳出 Local Minima"},
                            {"id": "n_e3", "title": "跨过 Saddle Points", "source_quote": "小 Batch Size 也有助于跨过 Saddle Points"},
                            {"id": "n_e4", "title": "Flat Minima 有利泛化", "source_quote": "Flat Minima 比 Sharp Minima 更有利于泛化"},
                        ],
                    },
                ],
            },
            {
                "id": "n_momentum",
                "title": "Momentum",
                "description": "Momentum 通过模拟物理惯性，使参数更新参考历史方向。",
                "source_quote": "Momentum 通过模拟物理惯性，使参数更新参考历史方向",
                "children": [
                    {
                        "id": "n_momentum_concept",
                        "title": "Momentum概念",
                        "description": "Momentum 帮助梯度下降克服鞍点。",
                        "source_quote": "Momentum 的目的是帮助梯度下降克服鞍点或局部最优解",
                        "children": [
                            {"id": "n_m1", "title": "帮助克服鞍点", "source_quote": "Momentum 的目的是帮助梯度下降克服鞍点或局部最优解"},
                            {"id": "n_m2", "title": "借助惯性越过洼地", "source_quote": "物理类比是小球滚下斜坡时会借助惯性越过洼地"},
                            {"id": "n_m3", "title": "历史方向影响更新", "source_quote": "历史方向会和当前梯度共同影响更新方向"},
                            {"id": "n_m4", "title": "方向积累继续移动", "source_quote": "这种方向积累能帮助模型继续向较优区域移动"},
                        ],
                    }
                ],
            },
            {
                "id": "n_summary",
                "type": "summary",
                "title": "5.3本章小结",
                "source_quote": "Batch Size 是训练效率与泛化能力之间的折中",
                "children": [
                    {"id": "n_s1", "title": "效率泛化折中", "source_quote": "Batch Size"},
                    {"id": "n_s2", "title": "加入方向惯性", "source_quote": "Momentum"},
                ],
            },
        ],
        "coverage_report": {
            "source": "intermediate/sections/lesson_05.md",
            "sections": [
                {"source_heading": "5.1 Batch", "node_path": "root > Batch", "action": "node", "source_span": {"line_start": 5, "line_end": 28}},
                {"source_heading": "5.1.1 Batch的定义", "node_path": "root > Batch > Batch定义", "action": "node", "source_span": {"line_start": 9, "line_end": 23}},
                {"source_heading": "5.1.2 Batch的作用", "node_path": "root > Batch > Batch作用", "action": "node", "source_span": {"line_start": 29, "line_end": 36}},
                {"source_heading": "5.2 Momentum", "node_path": "root > Momentum", "action": "node", "source_span": {"line_start": 38, "line_end": 49}},
                {"source_heading": "5.2.1 Momentum概念", "node_path": "root > Momentum > Momentum概念", "action": "node", "source_span": {"line_start": 42, "line_end": 49}},
                {"source_heading": "5.3本章小结", "node_path": "root > 5.3本章小结", "action": "node", "source_span": {"line_start": 51, "line_end": 54}},
            ],
            "figures": [
                {"source_id": "data_fig", "source_path": "assets/images/data_curve.png", "node_path": "root > Batch > Batch定义", "action": "image"},
                {"source_id": "slide_fig", "source_path": "assets/images/slide_screen.png", "node_path": "root > Batch > Batch定义", "action": "image"},
                {"source_id": "concept_fig", "source_path": "assets/images/sharp_flat.png", "node_path": "root > Batch > Batch作用", "action": "image"},
                {"source_id": "momentum_fig", "source_path": "assets/images/momentum_ball.png", "node_path": "root > Momentum > Momentum概念", "action": "image"},
            ],
            "tables": [],
            "formulas": [],
            "omitted": [],
        },
        "figure_decisions": [
            {
                "source_id": "data_fig",
                "source_path": "assets/images/data_curve.png",
                "decision": "image",
                "node_id": "n_batch_def",
                "node_path": "root > Batch > Batch定义",
                "alt": "Batch Size 时间数据图",
                "reason": "真实数据图",
                "callouts": [
                    {"text": "大 Batch 缩短 Epoch 时间", "source_quote": "较大的 Batch Size 借助 GPU 平行计算可以缩短一个 Epoch 的训练时间"}
                ],
            },
            {"source_id": "slide_fig", "source_path": "assets/images/slide_screen.png", "decision": "image", "node_id": "n_batch_def", "node_path": "root > Batch > Batch定义", "alt": "课程截图", "reason": "测试截图默认 omit"},
            {
                "source_id": "concept_fig",
                "source_path": "assets/images/sharp_flat.png",
                "decision": "image",
                "node_id": "n_batch_effect",
                "node_path": "root > Batch > Batch作用",
                "alt": "Sharp vs Flat Minima",
                "reason": "测试注册模板 redraw",
                "callouts": [
                    {"text": "Flat Minima 有利泛化", "source_quote": "Flat Minima 比 Sharp Minima 更有利于泛化"}
                ],
            },
            {
                "source_id": "momentum_fig",
                "source_path": "assets/images/momentum_ball.png",
                "decision": "image",
                "node_id": "n_momentum_concept",
                "node_path": "root > Momentum > Momentum概念",
                "alt": "Momentum 物理惯性类比",
                "reason": "测试 crop_preserve",
                "callouts": [
                    {"text": "惯性越过洼地", "source_quote": "物理类比是小球滚下斜坡时会借助惯性越过洼地"}
                ],
            },
        ],
    }
    write_json(map_intermediate / "outline.json", outline)
    return project


class PipelineRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.project = build_fixture_project(Path(cls.tmpdir.name))
        commands = [
            [sys.executable, str(SCRIPTS_DIR / "extract_assets.py"), str(cls.project)],
            [sys.executable, str(SCRIPTS_DIR / "render_mindmap.py"), str(cls.project), "--section-id", "lesson_05", "--style", "classic", "--image-mode", "relative"],
            [sys.executable, str(SCRIPTS_DIR / "batch_validate.py"), str(cls.project), "--section-id", "lesson_05", "--skip-browser"],
        ]
        for command in commands:
            result = subprocess.run(
                command,
                cwd=REPO_ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if result.returncode:
                raise AssertionError(
                    f"Command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                )
        cls.html_path = cls.project / "maps" / "lesson_05" / "exports" / "lesson_05.html"
        cls.validation_path = cls.project / "maps" / "lesson_05" / "intermediate" / "validation.json"
        cls.mindmap_path = cls.project / "maps" / "lesson_05" / "intermediate" / "mindmap.json"
        cls.image_index_path = cls.project / "assets" / "images" / "index.json"
        cls.html = cls.html_path.read_text(encoding="utf-8")
        cls.validation = json.loads(cls.validation_path.read_text(encoding="utf-8"))
        cls.mindmap = json.loads(cls.mindmap_path.read_text(encoding="utf-8"))
        cls.image_index = json.loads(cls.image_index_path.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmpdir.cleanup()

    def test_no_placeholder_curves(self):
        self.assertTrue(self.validation["checks"]["placeholder_curve_detection"]["passed"], "检测到占位曲线")

    def test_section_numbering(self):
        self.assertIn('data-section-id="5.1.1"', self.html)

    def test_keywords_node_rendered(self):
        pills = re.findall(r'class="keywords-pill"', self.html)
        self.assertGreaterEqual(len(pills), 8)

    def test_summary_completeness(self):
        self.assertTrue(self.validation["checks"]["summary_sentence_checks"]["passed"])

    def test_screenshot_not_embedded(self):
        srcs = re.findall(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']", self.html, flags=re.I)
        by_path = {item["path"].replace("\\", "/"): item for item in self.image_index}
        for src in srcs:
            normalized = src.replace("\\", "/")
            if "assets/images/" not in normalized:
                continue
            if "assets/images/crops/" in normalized:
                continue
            asset_path = "assets/images/" + normalized.rsplit("assets/images/", 1)[1]
            asset = by_path.get(asset_path)
            self.assertIsNotNone(asset, asset_path)
            self.assertNotEqual(asset.get("type"), "screenshot", f"screenshot embedded: {asset_path}")

    def test_h3_density(self):
        self.assertTrue(self.validation["checks"]["h3_density"]["passed"])

    def test_figure_triage(self):
        decisions = {item["source_id"]: item["decision"] for item in self.mindmap["figure_decisions"]}
        self.assertEqual(decisions["data_fig"], "preserve_full")
        self.assertEqual(decisions["slide_fig"], "omit")
        self.assertEqual(decisions["concept_fig"], "redraw_concept")
        self.assertEqual(decisions["momentum_fig"], "preserve_crop")

    def test_crop_preserve_creates_provenance_file(self):
        crops = [
            item for item in self.mindmap["figure_decisions"]
            if item.get("decision") == "preserve_crop"
        ]
        self.assertTrue(crops)
        for item in crops:
            crop_path = self.project / item["crop_path"]
            self.assertTrue(crop_path.exists(), crop_path)
            self.assertEqual(item.get("crop_source_id"), item["source_id"])

    def test_no_extra_section_numbers(self):
        self.assertTrue(self.validation["checks"]["forbidden_section_numbers"]["passed"])

    def test_image_learning_checks(self):
        self.assertTrue(self.validation["checks"]["image_readability"]["passed"])
        self.assertTrue(self.validation["checks"]["crop_metadata"]["passed"])
        self.assertTrue(self.validation["checks"]["image_callout_grounding"]["passed"])

    def test_auto_density_stays_inside_source_span(self):
        source_lines = (self.project / "intermediate" / "sections" / "lesson_05.md").read_text(encoding="utf-8").splitlines()
        for node in self.mindmap["root"]["children"]:
            if node.get("id") != "n_momentum":
                continue
            for child in node.get("children", []):
                for leaf in child.get("children", []):
                    if not leaf.get("auto_density"):
                        continue
                    span = leaf.get("source_span") or {}
                    self.assertGreaterEqual(span.get("line_start", 0), child["source_span"]["line_start"])
                    self.assertLessEqual(span.get("line_end", 10**9), child["source_span"]["line_end"])
                    quote = leaf.get("source_quote", "")
                    joined = "\n".join(source_lines[span["line_start"] - 1:span["line_end"]])
                    self.assertIn(quote, joined)


if __name__ == "__main__":
    unittest.main()

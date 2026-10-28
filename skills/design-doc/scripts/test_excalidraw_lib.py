"""Tests for excalidraw_lib: each layout defect is caught, a clean diagram passes, the palette stays light."""
import json
import random
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True  # a stray __pycache__ would fail the skill gate (.pyc is banned)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import excalidraw_lib as lib  # noqa: E402


def luminance(hex_colour):
    red, green, blue = (int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


class ExcalidrawLibTests(unittest.TestCase):
    def setUp(self):
        random.seed(7)
        lib.reset()

    def two_nodes(self):
        left = lib.node(0, 0, 160, 50, "left", *lib.APP)
        right = lib.node(400, 0, 160, 50, "right", *lib.WORKER)
        return left, right

    def kinds(self):
        return {problem.split(" ")[0] for problem in lib.problems()}

    def test_clean_diagram_passes_and_writes_a_valid_scene(self):
        lib.banner(0, -60, "Flow")
        left, right = self.two_nodes()
        lib.connect(left, "r", right, "l", lbl="call")
        self.assertTrue(lib.check())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "flow.excalidraw"
            count = lib.write(str(path))
            scene = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(count, len(scene["elements"]))
        self.assertEqual(scene["type"], "excalidraw")
        self.assertEqual(scene["appState"]["viewBackgroundColor"], lib.CANVAS)
        self.assertEqual({e["type"] for e in scene["elements"]}, {"rectangle", "text", "arrow"})

    def test_label_on_a_foreign_leaf_is_caught(self):
        self.two_nodes()
        lib.label(10, 10, "stray note")
        self.assertIn("LABEL-ON-LEAF", self.kinds())

    def test_label_with_a_declared_home_is_allowed(self):
        left, _ = self.two_nodes()
        lib.label(10, 10, "inside", home=left["id"])
        self.assertNotIn("LABEL-ON-LEAF", self.kinds())

    def test_overlapping_leaves_and_labels_are_caught(self):
        lib.node(0, 0, 160, 50, "one", *lib.APP)
        lib.node(40, 10, 160, 50, "two", *lib.APP)
        lib.label(500, 500, "same spot")
        lib.label(500, 500, "same spot")
        self.assertEqual(self.kinds() & {"LEAF-LEAF", "LABEL-LABEL"}, {"LEAF-LEAF", "LABEL-LABEL"})

    def test_arrow_through_a_node_that_is_not_its_endpoint_is_caught(self):
        left = lib.node(0, 0, 100, 50, "a", *lib.APP)
        lib.node(200, 0, 100, 50, "middle", *lib.APP)
        right = lib.node(400, 0, 100, 50, "c", *lib.APP)
        lib.connect(left, "r", right, "l")
        self.assertIn("ARROW-CROSS", self.kinds())

    def test_two_crossing_arrows_are_caught_and_arrows_sharing_an_end_are_not(self):
        lib.arrow([(0, 100), (300, 100)])
        lib.arrow([(150, 0), (150, 200)])
        self.assertIn("ARROW-CROSS-ARROW", self.kinds())
        lib.reset()
        lib.arrow([(0, 0), (100, 0)])
        lib.arrow([(100, 0), (100, 100)])
        self.assertNotIn("ARROW-CROSS-ARROW", self.kinds())

    def test_arrow_over_a_foreign_label_is_caught(self):
        left, right = self.two_nodes()
        lib.label(250, 17, "note", w=60)
        lib.connect(left, "r", right, "l")
        self.assertIn("ARROW-OVER-TEXT", self.kinds())

    def test_text_wider_than_its_box_is_caught(self):
        lib.label(0, 0, "a very long single line of text", w=20)
        self.assertIn("WRAP", self.kinds())

    def test_builders_refuse_text_that_cannot_fit(self):
        with self.assertRaises(AssertionError):
            lib.node(0, 0, 40, 20, "this label is far too long for the box", *lib.APP)
        with self.assertRaises(AssertionError):
            lib.container(0, 0, 60, 100, "a container title that is too wide", *lib.APP)
        with self.assertRaises(AssertionError):
            lib.rnode(0, 0, 60, "packages/ui", "ComponentWithALongName", *lib.APP)

    def test_check_raises_layout_error_listing_the_defects(self):
        self.two_nodes()
        lib.label(10, 10, "stray note")
        with self.assertRaises(lib.LayoutError) as caught:
            lib.check()
        self.assertIn("LABEL-ON-LEAF", str(caught.exception))
        self.assertIn("layout problems", str(caught.exception))

    def test_port_rejects_a_bad_side_and_connect_adds_elbows_only_when_needed(self):
        left, right = self.two_nodes()
        with self.assertRaises(ValueError):
            lib.port(left, "x")
        lib.connect(left, "r", right, "l")
        self.assertEqual(len(lib.ARROWS[-1][0]), 2)
        high = lib.node(400, 200, 160, 50, "lower", *lib.APP)
        lib.connect(left, "r", high, "l")
        self.assertEqual(len(lib.ARROWS[-1][0]), 4)
        lib.connect(left, "b", high, "t")
        self.assertEqual(len(lib.ARROWS[-1][0]), 4)
        lib.connect(left, "r", high, "t")
        self.assertEqual(len(lib.ARROWS[-1][0]), 3)

    def test_rect_of_gives_the_manifest_target_for_a_handle(self):
        handle = lib.node(10.4, 20.6, 160, 50, "left", *lib.APP)
        self.assertEqual(lib.rect_of(handle), [10, 21, 160, 50])

    def test_arrow_style_follows_the_line_grammar(self):
        left, right = self.two_nodes()
        for kwargs, style in (({}, "solid"), ({"dashed": True}, "dashed"), ({"dotted": True}, "dotted")):
            lib.connect(left, "r", right, "l", **kwargs)
            self.assertEqual([e for e in lib.els if e["type"] == "arrow"][-1]["strokeStyle"], style)

    def test_dashed_nodes_and_open_markers_are_distinct(self):
        proposed = lib.node(0, 0, 160, 50, "new", *lib.APP, dashed=True)
        lib.openmarker(300, 0, 200, "which queue")
        styles = {e["id"]: e["strokeStyle"] for e in lib.els if e["type"] == "rectangle"}
        self.assertEqual(styles[proposed["id"]], "dashed")
        self.assertEqual(len(styles), 2)
        texts = [e["text"] for e in lib.els if e["type"] == "text"]
        self.assertIn("? which queue", texts)

    def test_every_primitive_composes_into_a_clean_diagram(self):
        lib.banner(0, -60, "All primitives")
        outer = lib.container(0, 0, 900, 420, "apps/admin", *lib.APP)
        lib.band(20, 330, 860, 80, "trust boundary")
        a = lib.rnode(30, 50, 260, "apps/admin", "saveBooking()", *lib.APP)
        d = lib.cylinder(620, 50, 220, 80, "D1 bookings", *lib.STORE)
        decision = lib.diamond(450, 90, 140, 90, "valid?", *lib.OPEN)
        lib.ellipse(30, 180, 200, 70, "event", *lib.USER)
        lib.block(300, 180, 260, "Setup", ["secret A", "binding B"], *lib.CONFIG)
        lib.relaynum(330, 150, 1)
        lib.lifeline(900, 0, 400)
        lib.legend(950, 0, 220, "Legend", [("app", "app"), ("worker", "worker"), ("store", "store"), ("decision", "decision"),
                                          ("solid", "call"), ("dashed", "proposed"), ("dotted", "derived"), ("", "plain")])
        lib.connect(a, "r", decision, "l")
        lib.connect(decision, "r", d, "l", dashed=True)
        self.assertEqual(lib.problems(), [])
        self.assertTrue(outer["id"] in lib.CONTAINERS)

    def test_parallel_arrows_in_one_corridor_warn_without_failing(self):
        left = lib.node(0, 0, 100, 100, "wide", *lib.APP)
        right = lib.node(400, 0, 100, 100, "wide", *lib.APP)
        lib.connect(left, "r", right, "l", f1=0.4, f2=0.4)
        lib.connect(left, "r", right, "l", f1=0.45, f2=0.45)
        self.assertTrue(any(w.startswith("PARALLEL-H") for w in lib.warnings()))
        self.assertNotIn("PARALLEL", " ".join(lib.problems()))

    def test_reset_clears_all_state(self):
        self.two_nodes()
        lib.reset()
        self.assertEqual((lib.els, lib.ARROWS, lib.LEAVES, lib.CONTAINERS, lib.TEXT_HOME), ([], [], set(), set(), {}))

    def test_the_palette_is_light_only(self):
        for name in ("APP", "WORKER", "STORE", "EXTERNAL", "USER", "CONFIG", "RISK", "OPEN"):
            fill, stroke = getattr(lib, name)
            self.assertGreater(luminance(fill), 0.8, f"{name} fill must be light")
            self.assertLess(luminance(stroke), 0.6, f"{name} stroke must read on a light ground")
        self.assertGreater(luminance(lib.CANVAS), 0.9)
        self.assertLess(luminance(lib.INK), 0.2)


    def test_the_generator_in_the_diagram_guide_runs_as_written(self):
        guide = (Path(__file__).resolve().parent.parent / "references" / "diagram-guide.md").read_text(encoding="utf-8")
        code = re.search(r"```python\n(.*?)```", guide, re.S).group(1)
        code = code.replace("<skill-dir>", str(Path(__file__).resolve().parent.parent).replace("\\", "/"))
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, "-B", "-c", code], cwd=directory, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            scene = json.loads((Path(directory) / "overview.excalidraw").read_text(encoding="utf-8"))
        self.assertTrue(any(e.get("text") == "enqueue" for e in scene["elements"]))
        self.assertRegex(result.stdout, r"^\[\d+, \d+, \d+, \d+\] \[\d+, \d+, \d+, \d+\]")


if __name__ == "__main__":
    unittest.main()

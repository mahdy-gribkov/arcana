"""Tests for export_scene: a smoothed scene becomes a 1300 by 1040 PNG whose pixels follow the scene."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # a stray __pycache__ would fail the skill gate (.pyc is banned)
sys.path.insert(0, str(HERE))
import excalidraw_lib as lib  # noqa: E402
from export_scene import export, font_path  # noqa: E402
from smooth_scene import smooth  # noqa: E402

try:
    from PIL import Image
    font_path()
    SKIP = None
except ImportError:
    SKIP = "Pillow is not installed (python -m pip install pillow)"
except ValueError as error:
    SKIP = str(error)


def rgb(hex_colour):
    return tuple(int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))


@unittest.skipIf(SKIP is not None, SKIP)
class ExportSceneTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.dir = Path(self.directory.name)
        lib.reset()

    def tearDown(self):
        self.directory.cleanup()

    def scene(self, build):
        build()
        path = self.dir / "scene.excalidraw"
        lib.write(str(path))
        smooth(path)
        return path

    def test_exports_the_fixed_canvas_with_fills_where_the_scene_puts_them(self):
        path = self.scene(lambda: (lib.node(100, 100, 200, 80, "saveBooking", *lib.APP),
                                   lib.cylinder(600, 100, 200, 80, "D1", *lib.STORE)))
        out = self.dir / "out.png"
        export(path, out)
        image = Image.open(out).convert("RGB")
        self.assertEqual(image.size, (1300, 1040))
        self.assertEqual(image.getpixel((10, 10)), (255, 255, 255))
        self.assertEqual(image.getpixel((110, 110)), rgb(lib.APP[0]))
        self.assertEqual(image.getpixel((620, 140)), rgb(lib.STORE[0]))
        self.assertEqual(image.getpixel((300, 500)), (255, 255, 255))

    def test_solid_arrow_draws_a_line_and_dashed_arrow_leaves_gaps(self):
        def build():
            lib.arrow([(100, 300), (500, 300)], color="#000000")
            lib.arrow([(100, 400), (500, 400)], color="#000000", dashed=True)
        out = self.dir / "out.png"
        export(self.scene(build), out)
        image = Image.open(out).convert("RGB")
        solid = [image.getpixel((x, 300)) != (255, 255, 255) for x in range(120, 460)]
        dashed = [image.getpixel((x, 400)) != (255, 255, 255) for x in range(120, 460)]
        self.assertTrue(all(solid))
        self.assertTrue(any(dashed) and not all(dashed))

    def test_text_is_drawn_inside_its_node(self):
        out = self.dir / "out.png"
        export(self.scene(lambda: lib.node(100, 100, 300, 80, "saveBooking", *lib.APP)), out)
        image = Image.open(out).convert("RGB")
        inside = {image.getpixel((x, y)) for x in range(110, 390) for y in range(120, 160)}
        self.assertGreater(len(inside), 1, "the label must add pixels that differ from the fill")

    def test_refuses_what_it_cannot_draw(self):
        path = self.scene(lambda: lib.node(100, 100, 200, 80, "x", *lib.APP))
        scene = json.loads(path.read_text(encoding="utf-8"))
        cases = {
            "rotated": ("angle", 0.4, "unrotated solid"),
            "translucent": ("opacity", 50, "opaque baseline"),
            "rough": ("roughness", 1, "unrotated solid"),
        }
        for name, (key, value, message) in cases.items():
            broken = json.loads(json.dumps(scene))
            broken["elements"][0][key] = value
            broken_path = self.dir / f"{name}.excalidraw"
            broken_path.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaises(ValueError, msg=name) as caught:
                export(broken_path, self.dir / f"{name}.png")
            self.assertIn(message, str(caught.exception))

    def test_refuses_a_scene_that_leaves_the_canvas(self):
        path = self.scene(lambda: lib.node(1250, 100, 200, 80, "wide", *lib.APP))
        with self.assertRaises(ValueError) as caught:
            export(path, self.dir / "out.png")
        self.assertIn("leaves the fixed canvas", str(caught.exception))

    def test_refuses_the_hand_drawn_font(self):
        lib.node(100, 100, 200, 80, "x", *lib.APP)
        path = self.dir / "rough-font.excalidraw"
        lib.write(str(path))
        scene = json.loads(path.read_text(encoding="utf-8"))
        for element in scene["elements"]:
            element["roughness"] = 0
            element["fillStyle"] = "solid"
        path.write_text(json.dumps(scene), encoding="utf-8")
        with self.assertRaises(ValueError) as caught:
            export(path, self.dir / "out.png")
        self.assertIn("fontFamily 2", str(caught.exception))

    def test_font_path_reports_a_missing_explicit_font(self):
        with self.assertRaises(ValueError) as caught:
            font_path(str(self.dir / "missing.ttf"))
        self.assertIn("--font", str(caught.exception))


if __name__ == "__main__":
    unittest.main()

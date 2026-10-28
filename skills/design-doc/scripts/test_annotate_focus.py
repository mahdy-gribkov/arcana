"""Tests for annotate_focus: focused shapes keep full strength and a red outline, everything else fades."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True  # a stray __pycache__ would fail the skill gate (.pyc is banned)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from annotate_focus import FOCUS_RED, INACTIVE_OPACITY, annotate  # noqa: E402

# Pillow is pinned in requirements.txt; a missing install fails the run instead of skipping it.
from PIL import Image, ImageDraw  # noqa: E402

BLUE = (30, 60, 200)
FADED_BLUE = tuple(255 * (1 - INACTIVE_OPACITY) + channel * INACTIVE_OPACITY for channel in BLUE)  # Pillow truncates, so compare with a tolerance


def near(pixel, expected, tolerance=2):
    return all(abs(a - b) <= tolerance for a, b in zip(pixel, expected))


class AnnotateFocusTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.dir = Path(self.directory.name)
        image = Image.new("RGB", (400, 300), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle([40, 40, 160, 120], fill=BLUE)      # focused
        draw.rectangle([220, 40, 340, 120], fill=BLUE)     # not focused
        draw.rectangle([0, 0, 399, 20], fill=BLUE)         # header strip kept visible
        draw.ellipse([40, 160, 160, 260], fill=BLUE)       # focused ellipse
        draw.polygon([(280, 160), (340, 210), (280, 260), (220, 210)], fill=BLUE)  # focused diamond
        self.base = self.dir / "base.png"
        image.save(self.base)
        self.out = self.dir / "nested" / "focus.png"

    def tearDown(self):
        self.directory.cleanup()

    def run_annotate(self, targets, keep=()):
        annotate(self.base, self.out, targets, list(keep))
        return Image.open(self.out).convert("RGB")

    def test_focused_shape_stays_full_strength_and_others_fade(self):
        image = self.run_annotate([{"rect": [40, 40, 120, 80]}])
        self.assertEqual(image.size, (400, 300))
        self.assertEqual(image.getpixel((100, 80)), BLUE)
        self.assertTrue(near(image.getpixel((280, 80)), FADED_BLUE), image.getpixel((280, 80)))
        self.assertEqual(image.getpixel((200, 280)), (255, 255, 255))

    def test_focus_outline_is_red_on_the_edge(self):
        image = self.run_annotate([{"rect": [40, 40, 120, 80]}])
        edge = image.getpixel((100, 40))
        self.assertTrue(all(abs(a - b) <= 12 for a, b in zip(edge, FOCUS_RED)), f"edge pixel {edge}")
        self.assertTrue(near(image.getpixel((280, 44)), FADED_BLUE), "an unfocused shape has no outline")

    def test_keep_rectangles_stay_at_full_strength(self):
        image = self.run_annotate([{"rect": [40, 40, 120, 80]}], keep=[[0, 0, 400, 20]])
        self.assertEqual(image.getpixel((200, 10)), BLUE)

    def test_ellipse_and_diamond_targets_are_masked_and_outlined(self):
        targets = [{"rect": [40, 160, 120, 100], "shape": "ellipse"}, {"rect": [220, 160, 120, 100], "shape": "diamond"}]
        image = self.run_annotate(targets)
        self.assertEqual(image.getpixel((100, 210)), BLUE)
        self.assertEqual(image.getpixel((280, 210)), BLUE)
        top = image.getpixel((100, 160))
        self.assertTrue(all(abs(a - b) <= 40 for a, b in zip(top, FOCUS_RED)), f"ellipse top {top}")
        corner = image.getpixel((41, 161))
        self.assertEqual(corner, (255, 255, 255), "the ellipse bounding-box corner is outside the shape and stays faded white")

    def test_creates_missing_output_folders(self):
        self.run_annotate([{"rect": [40, 40, 120, 80]}])
        self.assertTrue(self.out.is_file())


if __name__ == "__main__":
    unittest.main()

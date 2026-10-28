"""Tests for smooth_scene: restyle a scene for export and report what cannot be exported."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # a stray __pycache__ would fail the skill gate (.pyc is banned)
sys.path.insert(0, str(HERE))
import excalidraw_lib as lib  # noqa: E402
from smooth_scene import smooth  # noqa: E402


class SmoothSceneTests(unittest.TestCase):
    def build_scene(self, directory):
        lib.reset()
        lib.container(0, 0, 400, 200, "apps/admin", *lib.APP)
        lib.node(30, 60, 140, 50, "saveBooking", *lib.WORKER)
        path = Path(directory) / "scene.excalidraw"
        lib.write(str(path))
        return path

    def test_restyles_roughness_font_and_fill_in_place(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.build_scene(directory)
            before = json.loads(path.read_text(encoding="utf-8"))["elements"]
            self.assertTrue(any(e["roughness"] == 1 for e in before))
            self.assertTrue(any(e["fillStyle"] == "cross-hatch" for e in before))
            self.assertEqual(smooth(path), [])
            after = json.loads(path.read_text(encoding="utf-8"))["elements"]
        self.assertTrue(all(e["roughness"] == 0 for e in after))
        self.assertTrue(all(e["fillStyle"] == "solid" for e in after))
        self.assertTrue(all(e["fontFamily"] == 2 for e in after if e["type"] == "text"))
        self.assertEqual(len(before), len(after))

    def test_reports_rotated_and_translucent_elements_without_dropping_them(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.build_scene(directory)
            scene = json.loads(path.read_text(encoding="utf-8"))
            scene["elements"][0]["angle"] = 0.5
            scene["elements"][1]["opacity"] = 40
            path.write_text(json.dumps(scene), encoding="utf-8")
            remaining = smooth(path)
        self.assertEqual(remaining, [scene["elements"][0]["id"], scene["elements"][1]["id"]])

    def test_deleted_elements_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.build_scene(directory)
            scene = json.loads(path.read_text(encoding="utf-8"))
            scene["elements"][0]["isDeleted"] = True
            scene["elements"][0]["angle"] = 1.0
            path.write_text(json.dumps(scene), encoding="utf-8")
            self.assertEqual(smooth(path), [])

    def test_command_line_exit_codes(self):
        script = str(HERE / "smooth_scene.py")
        with tempfile.TemporaryDirectory() as directory:
            path = self.build_scene(directory)
            ok = subprocess.run([sys.executable, script, str(path)], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertIn("Restyled", ok.stdout)
            scene = json.loads(path.read_text(encoding="utf-8"))
            scene["elements"][0]["angle"] = 0.5
            path.write_text(json.dumps(scene), encoding="utf-8")
            rotated = subprocess.run([sys.executable, script, str(path)], capture_output=True, text=True)
            self.assertEqual(rotated.returncode, 1)
            self.assertIn("rotated or translucent", rotated.stderr)
            missing = subprocess.run([sys.executable, script, str(Path(directory) / "none.excalidraw")], capture_output=True, text=True)
            self.assertEqual(missing.returncode, 1)


if __name__ == "__main__":
    unittest.main()

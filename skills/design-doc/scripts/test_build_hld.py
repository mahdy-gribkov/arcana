"""Tests for build_hld: manifest validation, focus images and their staleness check, Markdown and HTML rendering, the command line."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # a stray __pycache__ would fail the skill gate (.pyc is banned)
sys.path.insert(0, str(HERE))
import build_hld  # noqa: E402

try:
    from PIL import Image, ImageDraw
    SKIP = None
except ImportError:
    SKIP = "Pillow is not installed (python -m pip install pillow)"

EXAMPLE = HERE.parent / "assets" / "manifest.example.json"


@unittest.skipIf(SKIP is not None, SKIP)
class BuildHldTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        for directory in ("src", "research", "diagrams/source", "diagrams/steps"):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        self.data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        (self.root / "research/contract.md").write_text("Synthetic reviewed routes.\n", encoding="utf-8")
        (self.root / "diagrams/source/overview.excalidraw").write_text('{"type":"excalidraw","elements":[]}\n', encoding="utf-8")
        self.write_base("white")
        self.manifest = self.root / "src" / "hld.json"
        self.done = False
        self.save()

    def tearDown(self):
        self.temporary.cleanup()

    def write_base(self, colour):
        image = Image.new("RGB", (1300, 1040), colour)
        ImageDraw.Draw(image).rectangle([180, 280, 510, 450], outline="black", width=3)
        ImageDraw.Draw(image).rectangle([760, 280, 1090, 450], outline="black", width=3)
        image.save(self.root / "diagrams/source/overview.png")

    def save(self):
        self.manifest.write_text(json.dumps(self.data), encoding="utf-8")

    def annotated(self):
        if not self.done:
            build_hld.annotate(self.data, self.root)
            self.done = True
        return self.data

    def fails(self, message, mutate, annotate_first=True):
        data = copy.deepcopy(self.data)
        if annotate_first:
            self.annotated()
        mutate(data)
        with self.assertRaises(ValueError) as caught:
            build_hld.validate(data, self.root)
        self.assertIn(message, str(caught.exception))

    def test_the_shipped_example_validates_annotates_and_renders(self):
        build_hld.validate(self.data, self.root, require_images=False)
        self.annotated()
        build_hld.validate(self.data, self.root)
        for step in ("receive", "deliver"):
            with Image.open(self.root / f"diagrams/steps/{step}.png") as image:
                self.assertEqual(image.size, (1300, 1040))
            record = json.loads((self.root / f"diagrams/steps/{step}.focus.json").read_text(encoding="utf-8"))
            self.assertEqual(record["step_id"], step)

    def test_focus_image_fades_everything_but_the_focused_target(self):
        self.annotated()
        with Image.open(self.root / "diagrams/steps/receive.png") as opened:
            image = opened.convert("RGB")
        outline = image.getpixel((180, 365))
        self.assertTrue(all(abs(a - b) <= 16 for a, b in zip(outline, (224, 49, 49))), f"the focused box has the red outline, got {outline}")
        self.assertGreater(image.getpixel((762, 365))[0], 150, "the other box is faded toward white")

    def test_a_changed_base_image_makes_the_step_images_stale(self):
        self.annotated()
        self.write_base("#F6F8FA")  # the recorded base hash no longer matches
        with self.assertRaises(ValueError) as caught:
            build_hld.validate(self.data, self.root)
        self.assertIn("Stale or mismatched step image for receive", str(caught.exception))

    def test_a_missing_focus_record_is_reported(self):
        self.annotated()
        (self.root / "diagrams/steps/receive.focus.json").unlink()
        with self.assertRaises(ValueError) as caught:
            build_hld.validate(self.data, self.root)
        self.assertIn("Missing focus mapping for receive", str(caught.exception))

    def test_markdown_note_carries_every_section_and_a_route_table(self):
        self.annotated()
        text = build_hld.render_markdown(self.data, self.root, image_prefix="../hld")
        for needle in ("# Example: provider webhook intake", "Design status: proposed", "## Overview", "![Webhook intake architecture](../hld/diagrams/source/overview.png)",
                       "### RECEIVE. Accept the notification", "![receive: Accept the notification](../hld/diagrams/steps/receive.png)",
                       "**API calls:** `POST /hooks/provider`", "## API routes", "| RECEIVE | POST | `/hooks/provider` | Provider: Accept notifications | proposed |",
                       "## Setup, permissions, and resources", "| Webhook signing secret |", "## Open decisions and runtime proof",
                       "- Prove duplicate handling", "## Sources", "[Reviewed intake contract](../hld/research/contract.md)"):
            self.assertIn(needle, text)

    def test_markdown_fence_grows_when_the_pseudocode_holds_backticks(self):
        self.data["flow_groups"][0]["steps"][0]["pseudocode"] = "run ```x``` now"
        self.annotated()
        text = build_hld.render_markdown(self.data, self.root)
        self.assertIn("````text\nrun ```x``` now\n````", text)

    def test_table_cells_cannot_break_the_markdown_table(self):
        self.data["apis"][0]["purpose"] = "Accept | verify\nand queue"
        self.annotated()
        text = build_hld.render_markdown(self.data, self.root)
        self.assertIn("Accept \\| verify and queue", text)

    def test_html_preview_embeds_images_and_escapes_prose(self):
        self.data["flow_groups"][0]["steps"][0]["explanation"] = "Use <script>alert(1)</script> never"
        self.annotated()
        page = build_hld.render_html(self.data, self.root)
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn("data:image/png;base64,", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)
        self.assertNotIn("<script>", page)
        self.assertIn('id="api-provider-hook"', page)
        self.assertIn("color-scheme: light", page)

    def test_validation_errors(self):
        self.fails("schema_version must be 1", lambda d: d.update(schema_version=2))
        self.fails("Document status must be", lambda d: d.update(status="done"))
        self.fails("At least one evidence source", lambda d: d.update(sources=[]))
        self.fails("Source link does not resolve", lambda d: d["sources"][0].update(url="research/nope.md"))
        self.fails("Unsupported source link scheme", lambda d: d["sources"][0].update(url="ftp://example.test/x"))
        self.fails("Path leaves the project root", lambda d: d["sources"][0].update(url="../outside.md"))
        self.fails("invalid stable ID", lambda d: d["sources"][0].update(id="Bad Id"))
        self.fails("Duplicate source ID", lambda d: d["sources"].append(copy.deepcopy(d["sources"][0])))
        self.fails("references missing focus targets", lambda d: d["flow_groups"][0]["steps"][0].update(focus=["nowhere"]))
        self.fails("references an unknown API", lambda d: d["flow_groups"][0]["steps"][0].update(api_ids=["ghost"]))
        self.fails("unused routes", lambda d: d["flow_groups"][0]["steps"][1].update(api_ids=[]))
        self.fails("needs a concrete HTTP method", lambda d: d["apis"][0].update(method="FETCH"))
        self.fails("needs a route or an https URL", lambda d: d["apis"][0].update(path="hooks/provider"))
        self.fails("has missing evidence references", lambda d: d["apis"][0].update(source_ids=["unknown"]))
        self.fails("Step image filename must be receive.png", lambda d: d["flow_groups"][0]["steps"][0].update(image="diagrams/steps/other.png"))
        self.fails("may only use letters, digits", lambda d: d["flow_groups"][0]["steps"][0].update(image="diagrams/steps/a;b.png"))
        self.fails("needs [x, y, width, height]", lambda d: d["diagrams"][0]["targets"][0].update(rect=[1200, 0, 300, 10]))
        self.fails("unsupported shape", lambda d: d["diagrams"][0]["targets"][0].update(shape="star"))
        self.fails("open_items must be a list of strings", lambda d: d.update(open_items="none"))
        self.fails("contains a control character", lambda d: d.update(summary="bad\x01text"))
        self.fails("needs title, explanation, and concrete pseudocode", lambda d: d["flow_groups"][0]["steps"][0].update(pseudocode=""))
        self.fails("Setup rows need", lambda d: d["setup"][0].update(responsible=""))
        self.fails("Unknown overview_diagram", lambda d: d.update(overview_diagram="none"))

    def test_base_image_must_match_the_canvas(self):
        Image.new("RGB", (800, 600), "white").save(self.root / "diagrams/source/overview.png")
        with self.assertRaises(ValueError) as caught:
            build_hld.validate(self.data, self.root, require_images=False)
        self.assertIn("must be 1300 by 1040 pixels", str(caught.exception))

    def test_appendices_and_side_diagrams_render(self):
        self.data["appendices"] = [{"id": "research", "title": "Provider research", "content": "Settled answers.", "source_ids": ["contract"], "diagram_ids": ["main"]}]
        self.data["side_diagrams"] = [{"diagram": "main", "explanation": "Lifecycle view."}]
        self.annotated()
        text = build_hld.render_markdown(self.data, self.root)
        page = build_hld.render_html(self.data, self.root)
        self.assertIn("## Provider research", text)
        self.assertIn("Lifecycle view.", text)
        self.assertIn('<details id="appendix-research">', page)

    def test_pipeline_from_builder_scene_to_validated_manifest(self):
        """excalidraw_lib -> smooth_scene -> export_scene -> targets from rect_of -> annotate -> validate -> render."""
        import excalidraw_lib as lib
        from export_scene import export, font_path
        from smooth_scene import smooth
        try:
            font_path()
        except ValueError as error:
            self.skipTest(str(error))
        lib.reset()
        receiver = lib.rnode(180, 280, 330, "apps/portal", "POST /hooks/provider", *lib.APP)
        sink = lib.rnode(760, 280, 330, "packages/comms", "deliverEvent()", *lib.WORKER)
        lib.connect(receiver, "r", sink, "l", lbl="enqueue")
        lib.check()
        scene = self.root / "diagrams/source/overview.excalidraw"
        lib.write(str(scene))
        smooth(scene)
        export(scene, self.root / "diagrams/source/overview.png")
        self.data["diagrams"][0]["targets"] = [{"id": "receiver", "rect": lib.rect_of(receiver)}, {"id": "sink", "rect": lib.rect_of(sink)}]
        self.annotated()
        build_hld.validate(self.data, self.root)
        self.assertIn("### DELIVER. Deliver the normalized event", build_hld.render_markdown(self.data, self.root))

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(HERE / "build_hld.py"), *args], capture_output=True, text=True, encoding="utf-8")

    def test_command_line_flow(self):
        source_only = self.run_cli(str(self.manifest), "--validate-source")
        self.assertEqual(source_only.returncode, 0, source_only.stderr)
        stale = self.run_cli(str(self.manifest), "--validate-only")
        self.assertEqual(stale.returncode, 1)
        self.assertIn("run --annotate", stale.stderr)
        annotated = self.run_cli(str(self.manifest), "--annotate")
        self.assertEqual(annotated.returncode, 0, annotated.stderr)
        no_output = self.run_cli(str(self.manifest))
        self.assertEqual(no_output.returncode, 1)
        self.assertIn("--output", no_output.stderr)
        out = self.root / "out"
        built = self.run_cli(str(self.manifest), "--output", str(out))
        self.assertEqual(built.returncode, 0, built.stderr)
        self.assertTrue((out / "hld.md").read_text(encoding="utf-8").startswith("# Example: provider webhook intake"))
        self.assertIn("<h1>Example: provider webhook intake</h1>", (out / "hld.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

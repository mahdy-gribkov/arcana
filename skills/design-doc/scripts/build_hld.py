"""Validate a step-by-step HLD manifest, make its focus images, and render a Markdown note plus a standalone HTML preview.

The manifest (see references/hld-manifest.md) owns every heading, step, target rectangle, API route, pseudocode block and setup row.
Both outputs render from it, so they cannot drift apart. Nothing is published anywhere.

  python build_hld.py <manifest.json> --validate-source        before focus images exist
  python build_hld.py <manifest.json> --annotate               write focus images and their .focus.json records
  python build_hld.py <manifest.json> --validate-only          full validation, stale images included
  python build_hld.py <manifest.json> --output <dir> [--image-prefix <path>]   write hld.md and hld.html
"""
import argparse
import base64
import hashlib
import html
import json
import re
import struct
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.dont_write_bytecode = True  # a stray __pycache__ would fail the skill gate (.pyc is banned)
from annotate_focus import FOCUS_RED, FOCUS_STROKE, INACTIVE_OPACITY, annotate as annotate_focus

STATES = {"current", "proposed", "untested"}
ID = re.compile(r"^[a-z][a-z0-9-]*$")
METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
SAFE_PATH = re.compile(r"[A-Za-z0-9._/-]+")  # image paths end up in Markdown links and file names
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")
CANVAS = (1300, 1040)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(items, label):
    require(isinstance(items, list), f"{label} must be a list")
    result = {}
    for item in items:
        require(isinstance(item, dict), f"{label} entries must be objects")
        identifier = item.get("id", "")
        require(isinstance(identifier, str) and ID.fullmatch(identifier),
                f"{label} has an invalid stable ID: {identifier!r} (lowercase letters, digits and hyphens, starting with a letter)")
        require(identifier not in result, f"Duplicate {label} ID: {identifier}")
        result[identifier] = item
    return result


def local_path(root, name):
    require(isinstance(name, str) and name, "A file path is required")
    root = root.resolve()
    path = (root / name).resolve()
    require(path.is_relative_to(root), f"Path leaves the project root: {name}")
    return path


def image_path(root, name):
    require(isinstance(name, str) and SAFE_PATH.fullmatch(name),
            f"Image path {name!r} may only use letters, digits, dot, underscore, slash and hyphen")
    return local_path(root, name)


def png_size(path):
    require(path.is_file(), f"Missing PNG: {path.name}")
    with path.open("rb") as stream:
        header = stream.read(24)
    require(header[:8] == b"\x89PNG\r\n\x1a\n" and len(header) == 24, f"Not a valid PNG header: {path.name}")
    return struct.unpack(">II", header[16:24])


def reject_control_characters(value, where):
    if isinstance(value, str):
        require(not CONTROL.search(value), f"{where} contains a control character or an invalid code point")
    elif isinstance(value, dict):
        for key, item in value.items():
            reject_control_characters(key, where)
            reject_control_characters(item, f"{where}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_control_characters(item, f"{where}[{index}]")


def string_list(value):
    return isinstance(value, list) and all(isinstance(item, str) and item for item in value)


def rect_ok(rect):
    if not (isinstance(rect, list) and len(rect) == 4
            and all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in rect)):
        return False
    x, y, width, height = rect
    return x >= 0 and y >= 0 and width > 0 and height > 0 and x + width <= CANVAS[0] and y + height <= CANVAS[1]


def validate(data, root, require_images=True):
    """Raise ValueError naming the first problem. Returns (diagrams, apis, sources, steps)."""
    require(isinstance(data, dict), "The manifest must be a JSON object")
    reject_control_characters(data, "manifest")
    require(data.get("schema_version") == 1, "schema_version must be 1")
    for field in ("apis", "setup", "open_items"):
        require(field in data, f"{field} is required (use [] when there are none)")
    require(isinstance(data.get("title"), str) and data["title"].strip(), "A title is required")
    require(isinstance(data.get("summary"), str) and data["summary"].strip(), "A summary is required")
    require(data.get("status") in STATES, "Document status must be current, proposed, or untested")
    sources = unique(data.get("sources", []), "source")
    require(sources, "At least one evidence source is required")
    for source in sources.values():
        require(source.get("label"), f"Source {source['id']} needs a label")
        href = source.get("url", "")
        require(isinstance(href, str), f"Source {source['id']} url must be a string")
        parsed = urlparse(href)
        if parsed.scheme in {"https", "http"}:
            require(parsed.netloc, f"Invalid source URL: {href}")
        elif not parsed.scheme:
            require(local_path(root, unquote(parsed.path)).is_file(), f"Source link does not resolve to a file: {href}")
        else:
            raise ValueError(f"Unsupported source link scheme: {href}")
    diagrams = unique(data.get("diagrams", []), "diagram")
    require(diagrams, "At least one base diagram is required")
    require(data.get("overview_diagram") in diagrams, "Unknown overview_diagram")
    for diagram in diagrams.values():
        require(png_size(image_path(root, diagram.get("base_png"))) == CANVAS,
                f"Diagram {diagram['id']} must be {CANVAS[0]} by {CANVAS[1]} pixels")
        require(local_path(root, diagram.get("source")).is_file(), f"Missing editable diagram source: {diagram.get('source')}")
        require(diagram.get("label"), f"Diagram {diagram['id']} needs a label")
        require(diagram.get("source_ids") and set(diagram["source_ids"]) <= set(sources),
                f"Diagram {diagram['id']} has missing evidence references")
        targets = unique(diagram.get("targets", []), f"target in {diagram['id']}")
        for rect in diagram.get("always_visible", []):
            require(rect_ok(rect), f"Diagram {diagram['id']} has an invalid always_visible rectangle")
        for target in targets.values():
            require(target.get("shape", "roundedrect") in {"roundedrect", "ellipse", "diamond"},
                    f"Target {target['id']} has an unsupported shape")
            require(rect_ok(target.get("rect")), f"Target {target['id']} needs [x, y, width, height] inside the {CANVAS[0]} by {CANVAS[1]} canvas")
    apis = unique(data.get("apis", []), "API")
    for api in apis.values():
        require(api.get("method") in METHODS, f"API {api['id']} needs a concrete HTTP method")
        path = api.get("path")
        require(isinstance(path, str) and path.startswith(("/", "https://")), f"API {api['id']} needs a route or an https URL")
        require(api.get("kind") in {"internal", "external"}, f"API {api['id']} needs kind internal or external")
        require(api.get("status") in STATES, f"API {api['id']} needs an evidence status")
        require(api.get("source_ids") and set(api["source_ids"]) <= set(sources), f"API {api['id']} has missing evidence references")
        require(api.get("caller") and api.get("purpose"), f"API {api['id']} needs caller and purpose")
    groups = unique(data.get("flow_groups", []), "flow group")
    require(groups, "At least one flow group is required")
    steps = {}
    used_apis = set()
    used_images = set()
    for group in groups.values():
        require(group.get("title") and group.get("entrypoint"), f"Flow {group['id']} needs title and entrypoint")
        group_steps = unique(group.get("steps", []), "step")
        require(group_steps, f"Flow {group['id']} is empty")
        for step_id, step in group_steps.items():
            require(step_id not in steps, f"Duplicate step ID across groups: {step_id}")
            steps[step_id] = step
            require(step.get("title") and step.get("explanation") and step.get("pseudocode"),
                    f"Step {step_id} needs title, explanation, and concrete pseudocode")
            require(step.get("status") in STATES, f"Step {step_id} needs an evidence status")
            require(step.get("source_ids") and set(step["source_ids"]) <= set(sources), f"Step {step_id} has missing evidence references")
            require(step.get("diagram") in diagrams, f"Step {step_id} references an unknown diagram")
            target_ids = {target["id"] for target in diagrams[step["diagram"]].get("targets", [])}
            require(step.get("focus") and set(step["focus"]) <= target_ids, f"Step {step_id} references missing focus targets")
            require(len(step["focus"]) == len(set(step["focus"])), f"Step {step_id} repeats focus targets")
            api_ids = step.get("api_ids", [])
            require(isinstance(api_ids, list) and set(api_ids) <= set(apis), f"Step {step_id} references an unknown API")
            used_apis.update(api_ids)
            image = image_path(root, step.get("image"))
            require(image.name == f"{step_id}.png", f"Step image filename must be {step_id}.png")
            require(image not in used_images, f"Duplicate step image: {image.name}")
            used_images.add(image)
            if require_images:
                require(image.is_file(), f"Missing step image for {step_id}; run --annotate")
                require(png_size(image) == CANVAS, f"Step {step_id} image size changed")
                verify_focus_image(root, diagrams[step["diagram"]], step)
    require(used_apis == set(apis), f"API table has unused routes: {sorted(set(apis) - used_apis)}")
    require(isinstance(data["setup"], list), "setup must be a list")
    for item in data["setup"]:
        require(isinstance(item, dict), "Setup rows must be objects")
        require(all(isinstance(item.get(field), str) and item[field].strip() for field in ("resource", "requirement", "responsible", "status"))
                and string_list(item.get("source_ids")) and item["source_ids"],
                "Setup rows need resource, requirement, responsible, status, and source_ids")
        require(item["status"] in STATES and set(item["source_ids"]) <= set(sources),
                f"Setup resource {item['resource']} has invalid evidence")
    require(isinstance(data.get("side_diagrams", []), list), "side_diagrams must be a list")
    for side in data.get("side_diagrams", []):
        require(isinstance(side, dict) and side.get("diagram") in diagrams and side.get("explanation"),
                "Side diagrams must be objects with a known diagram and an explanation")
    require(string_list(data["open_items"]), "open_items must be a list of strings")
    appendices = unique(data.get("appendices", []), "appendix")
    for appendix in appendices.values():
        require(appendix.get("title") and appendix.get("content"), f"Appendix {appendix['id']} needs a title and content")
        require(appendix.get("source_ids") and set(appendix["source_ids"]) <= set(sources),
                f"Appendix {appendix['id']} has missing evidence references")
        require(isinstance(appendix.get("diagram_ids", []), list) and set(appendix.get("diagram_ids", [])) <= set(diagrams),
                f"Appendix {appendix['id']} has missing diagram references")
    return diagrams, apis, sources, steps


def focus_record(root, diagram, step):
    targets = {target["id"]: target for target in diagram.get("targets", [])}
    return {"step_id": step["id"], "diagram_id": diagram["id"],
            "base_sha256": hashlib.sha256(local_path(root, diagram["base_png"]).read_bytes()).hexdigest(),
            "style": {"inactive_opacity": INACTIVE_OPACITY, "red": list(FOCUS_RED), "stroke": FOCUS_STROKE},
            "always_visible": diagram.get("always_visible", []),
            "focus": [{"id": identifier, "rect": targets[identifier]["rect"],
                       "shape": targets[identifier].get("shape", "roundedrect"),
                       "radius": targets[identifier].get("radius", 10)} for identifier in step["focus"]]}


def verify_focus_image(root, diagram, step):
    path = local_path(root, step["image"])
    mapping_path = path.with_suffix(".focus.json")
    require(mapping_path.is_file(), f"Missing focus mapping for {step['id']}; run --annotate")
    recorded = json.loads(mapping_path.read_text(encoding="utf-8"))
    expected = focus_record(root, diagram, step)
    expected["image_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    require(recorded == expected, f"Stale or mismatched step image for {step['id']}; run --annotate")


def annotate(data, root):
    """Write every step's focus image and its .focus.json record."""
    diagrams, _, _, steps = validate(data, root, require_images=False)
    for step in steps.values():
        diagram = diagrams[step["diagram"]]
        record = focus_record(root, diagram, step)
        image = local_path(root, step["image"])
        annotate_focus(local_path(root, diagram["base_png"]), image, record["focus"], diagram.get("always_visible", []))
        record["image_sha256"] = hashlib.sha256(image.read_bytes()).hexdigest()
        image.with_suffix(".focus.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def escaped(value):
    return html.escape(str(value), quote=True)


def cell(value):
    """Markdown table cell: no pipes or line breaks."""
    return str(value).replace("|", "\\|").replace("\n", " ")


def fence(text):
    ticks = "`" * max(3, max((len(run) for run in re.findall(r"`+", text)), default=0) + 1)
    return f"{ticks}text\n{text}\n{ticks}"


def step_ids_by_api(data):
    return {api["id"]: [step["id"].upper() for group in data["flow_groups"] for step in group["steps"]
                        if api["id"] in step.get("api_ids", [])] for api in data["apis"]}


def render_markdown(data, root, image_prefix=""):
    """The note as Markdown. Image links are the manifest's paths with `image_prefix` in front."""
    diagrams, apis, sources, _ = validate(data, root)
    prefix = image_prefix.rstrip("/") + "/" if image_prefix else ""

    def source_link(source):
        return f"[{source['label']}]({source['url']})" if urlparse(source["url"]).scheme else f"[{source['label']}]({prefix}{source['url']})"

    def references(ids):
        return "Sources: " + ", ".join(source_link(sources[source_id]) for source_id in ids)

    def picture(path, label):
        return f"![{label}]({prefix}{path})"

    overview = diagrams[data["overview_diagram"]]
    out = [f"# {data['title']}", "", data["summary"], "", f"Design status: {data['status']}", "", "## Overview", "",
           picture(overview["base_png"], overview["label"]), "", references(overview["source_ids"]), ""]
    for group in data["flow_groups"]:
        out += [f"## {group['title']}", "", f"**Entrypoint:** {group['entrypoint']}", ""]
        for step in group["steps"]:
            out += [f"### {step['id'].upper()}. {step['title']}", "", picture(step["image"], f"{step['id']}: {step['title']}"), "",
                    f"Status: {step['status']}", "", step["explanation"], "", fence(step["pseudocode"]), ""]
            if step.get("api_ids"):
                out += ["**API calls:** " + ", ".join(f"`{apis[i]['method']} {apis[i]['path']}`" for i in step["api_ids"]), ""]
            out += [references(step["source_ids"]), ""]
    for side in data.get("side_diagrams", []):
        diagram = diagrams[side["diagram"]]
        out += [f"## {diagram['label']}", "", picture(diagram["base_png"], diagram["label"]), "", side["explanation"], "",
                references(diagram["source_ids"]), ""]
    used_in = step_ids_by_api(data)
    out += ["## API routes", "", "| Step | Method | Route | Caller and purpose | Status |", "| --- | --- | --- | --- | --- |"]
    out += [f"| {cell(', '.join(used_in[api['id']]))} | {api['method']} | `{cell(api['path'])}` | {cell(api['caller'])}: {cell(api['purpose'])} | {api['status']} |"
            for api in data["apis"]]
    out += ["", "## Setup, permissions, and resources", "", "| Resource | Requirement | Responsible | Status |", "| --- | --- | --- | --- |"]
    out += [f"| {cell(item['resource'])} | {cell(item['requirement'])} | {cell(item['responsible'])} | {item['status']} |" for item in data["setup"]]
    out += ["", "## Open decisions and runtime proof", ""]
    out += [f"- {item}" for item in data["open_items"]] or ["- None."]
    for appendix in data.get("appendices", []):
        out += ["", f"## {appendix['title']}", "", appendix["content"], ""]
        for diagram_id in appendix.get("diagram_ids", []):
            out += [picture(diagrams[diagram_id]["base_png"], diagrams[diagram_id]["label"]), ""]
        out += [references(appendix["source_ids"])]
    out += ["", "## Sources", ""] + [f"- {source_link(source)}" for source in data["sources"]]
    return "\n".join(out) + "\n"


def render_html(data, root):
    """A standalone HTML preview with the images embedded, styled by assets/preview.css."""
    diagrams, apis, sources, _ = validate(data, root)

    def image(path, label):
        encoded = base64.b64encode(local_path(root, path).read_bytes()).decode()
        return f'<figure><img width="900" height="720" alt="{escaped(label)}" src="data:image/png;base64,{encoded}"></figure>'

    def source_link(source):
        url = source["url"]
        if not urlparse(url).scheme:
            url = local_path(root, unquote(urlparse(url).path)).as_uri()
        return f'<a href="{escaped(url)}">{escaped(source["label"])}</a>'

    def references(ids):
        return '<p class="sources">Sources: ' + ", ".join(source_link(sources[source_id]) for source_id in ids) + "</p>"

    def paragraphs(value):
        return "".join(f"<p>{escaped(block)}</p>" for block in str(value).split("\n\n"))

    def table(headers, rows):
        return ("<table><thead><tr>" + "".join(f"<th>{escaped(header)}</th>" for header in headers) + "</tr></thead><tbody>"
                + "".join("<tr>" + "".join(f"<td>{item}</td>" for item in row) + "</tr>" for row in rows) + "</tbody></table>")

    overview = diagrams[data["overview_diagram"]]
    parts = [f"<h1>{escaped(data['title'])}</h1>", paragraphs(data["summary"]), f'<p class="status">Design status: {escaped(data["status"])}</p>',
             "<h2>Overview</h2>", image(overview["base_png"], overview["label"]), references(overview["source_ids"])]
    for group in data["flow_groups"]:
        parts += [f"<h2>{escaped(group['title'])}</h2>", f"<p><strong>Entrypoint:</strong> {escaped(group['entrypoint'])}</p>"]
        for step in group["steps"]:
            parts += [f'<h3 id="step-{escaped(step["id"])}">{escaped(step["id"].upper())}. {escaped(step["title"])}</h3>',
                      image(step["image"], f"{step['id']}: {step['title']}"), f'<p class="status">{escaped(step["status"])}</p>',
                      paragraphs(step["explanation"]), f"<pre><code>{escaped(step['pseudocode'])}</code></pre>"]
            if step.get("api_ids"):
                parts.append("<p><strong>API calls:</strong> " + ", ".join(
                    f'<a href="#api-{escaped(i)}">{escaped(apis[i]["method"] + " " + apis[i]["path"])}</a>' for i in step["api_ids"]) + "</p>")
            parts.append(references(step["source_ids"]))
    for side in data.get("side_diagrams", []):
        diagram = diagrams[side["diagram"]]
        parts += [f"<h2>{escaped(diagram['label'])}</h2>", image(diagram["base_png"], diagram["label"]), paragraphs(side["explanation"]),
                  references(diagram["source_ids"])]
    used_in = step_ids_by_api(data)
    parts += ["<h2>API routes</h2>", table(["Step", "Method", "Route", "Purpose"], [
        [escaped(", ".join(used_in[api["id"]])), escaped(api["method"]),
         f'<span id="api-{escaped(api["id"])}">{escaped(api["id"])}</span><br><code>{escaped(api["path"])}</code>',
         f"<strong>{escaped(api['caller'])}:</strong> {escaped(api['purpose'])}<br>"
         f'<span class="status">{escaped(api["status"])}</span>' + references(api["source_ids"])] for api in data["apis"]]),
        "<h2>Setup, permissions, and resources</h2>",
        table(["Resource", "Requirement", "Responsible", "Status", "Evidence"], [
            [escaped(item["resource"]), escaped(item["requirement"]), escaped(item["responsible"]), escaped(item["status"]),
             references(item["source_ids"])] for item in data["setup"]]),
        "<h2>Open decisions and runtime proof</h2>",
        "<ul>" + "".join(f"<li>{escaped(item)}</li>" for item in data["open_items"]) + "</ul>"]
    for appendix in data.get("appendices", []):
        content = paragraphs(appendix["content"]) + references(appendix["source_ids"])
        for diagram_id in appendix.get("diagram_ids", []):
            content += image(diagrams[diagram_id]["base_png"], diagrams[diagram_id]["label"])
        parts.append(f'<details id="appendix-{escaped(appendix["id"])}"><summary>{escaped(appendix["title"])}</summary>{content}</details>')
    parts.append("<h2>Sources</h2><ul>" + "".join(f'<li id="source-{escaped(s["id"])}">{source_link(s)}</li>' for s in data["sources"]) + "</ul>")
    css = (Path(__file__).resolve().parent.parent / "assets" / "preview.css").read_text(encoding="utf-8")
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{escaped(data["title"])}</title><style>{css}</style></head><body><main>' + "\n".join(parts) + "</main></body></html>\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--project-root", type=Path, help="Defaults to the parent of src/ when the manifest sits in src/, else its folder")
    parser.add_argument("--output", type=Path, help="Directory for hld.md and hld.html")
    parser.add_argument("--image-prefix", default="", help="Prefix for image links in hld.md, for example ../diagrams-root")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--validate-source", action="store_true", help="Validate before step images exist")
    parser.add_argument("--annotate", action="store_true")
    args = parser.parse_args()
    try:
        manifest = args.manifest.resolve()
        root = (args.project_root or (manifest.parent.parent if manifest.parent.name == "src" else manifest.parent)).resolve()
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if args.validate_source:
            validate(data, root, require_images=False)
            print("HLD source validation passed; focus images still need generating (--annotate).")
            return
        if args.annotate:
            annotate(data, root)
        validate(data, root)
        if args.annotate or args.validate_only:
            print("HLD validation passed: sources, step IDs, focus mapping, image dimensions, API references.")
            return
        require(args.output is not None, "Pass --output <dir> to write hld.md and hld.html")
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=True)
        (output / "hld.md").write_text(render_markdown(data, root, args.image_prefix), encoding="utf-8")
        (output / "hld.html").write_text(render_html(data, root), encoding="utf-8")
        print(f"Wrote {output / 'hld.md'} and {output / 'hld.html'}")
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as error:
        parser.exit(1, f"HLD error: {error}\n")


if __name__ == "__main__":
    main()

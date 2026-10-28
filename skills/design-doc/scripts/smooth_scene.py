"""Restyle an excalidraw_lib scene in place for export_scene.py: no roughness, Arial-style text, solid fills.

The editable source and the exported PNG then agree. Dashed and dotted strokes export as drawn. Prints any
element it cannot convert (rotated or translucent), which still needs native Excalidraw export or a redraw.
"""
import argparse
import json
from pathlib import Path


def smooth(source):
    source = Path(source)
    scene = json.loads(source.read_text(encoding="utf-8"))
    unconvertible = []
    for element in scene["elements"]:
        if element.get("isDeleted"):
            continue
        element["roughness"] = 0
        if element.get("fillStyle", "solid") != "solid":
            element["fillStyle"] = "solid"
        if element["type"] == "text":
            element["fontFamily"] = 2
        if element.get("angle", 0) or element.get("opacity", 100) != 100:
            unconvertible.append(element.get("id", element["type"]))
    source.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    return unconvertible


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    try:
        remaining = smooth(args.source)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f"{error}\n")
    if remaining:
        parser.exit(1, "Restyled, but export_scene.py will reject these rotated or translucent "
                       f"elements: {', '.join(remaining)}\n")
    print(f"Restyled {args.source} for export_scene.py")

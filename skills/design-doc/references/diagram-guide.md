# Diagram guide

Contents: choose the diagram, the generator, grammar, palette, API, export.

## Choose the diagram before you build it

`check()` guarantees a legible diagram, not the right one. Pin three things and state them back to the requester before writing the generator:

- **Altitude.** A component sketch (3 to 8 leaf nodes, one flow, no containers) answers "how do A and B talk". A subsystem view (a container or two, only the leaves that matter, one or two flows) answers "how does X work". A full HLD (every owning container, the services that matter, the real queue and topic edges) answers "document the architecture". When the ask is ambiguous, build the smaller one and offer to expand.
- **Scope boundary.** Say what is in and what is out. Anything not on the list stays off the canvas.
- **One altitude, consistently.** If one leaf carries `apps/admin` as its home tag, they all carry a home tag. One edge vocabulary, one colour meaning throughout.

Two altitudes (an overview and a drill-down) means two diagrams.

## The generator

Write a small script. Replace `<skill-dir>` with the absolute path of this skill.

```python
import sys; sys.path.insert(0, r"<skill-dir>/scripts")
from excalidraw_lib import *

reset()
banner(0, 0, "Booking confirmation flow")
admin = container(0, 60, 820, 300, "apps/admin", *APP)
save = rnode(30, 120, 300, "apps/admin", "saveBooking()", *APP)
mail = rnode(430, 120, 320, "packages/comms", "sendConfirmation()", *WORKER, dashed=True)
connect(save, "r", mail, "l", color=WORKER[1], lbl="enqueue")
check()                      # raises LayoutError listing every defect
write("overview.excalidraw")
print(rect_of(save), rect_of(mail))   # manifest targets for build_hld.py
```

Run it with `python generator.py`. If `check()` raises, fix the coordinates and rerun until clean. Keep the generator beside the diagram source so it can be re-run.

## Grammar

- A `container` is a big hatched boundary box (an app, a package, a worker). A `node`, `rnode`, `diamond`, `ellipse` or `cylinder` is a leaf. A leaf or label may sit inside a container; a label may not sit on a sibling leaf; an arrow may not cross a leaf that is not one of its endpoints.
- `rnode(x, y, w, home, name, ...)` carries a small home tag (the app, package or file that contains the component) above the name. Put the verbatim `path:line` there when you have it.
- `dashed=True` means NEW or proposed. `openmarker` means an open decision. Arrows: solid is a verified call, dashed is proposed, dotted is derived.
- `band` is a trust boundary or swimlane. `legend` explains the swatches. `relaynum` numbers the order of a flow.

## Palette (light theme only)

The default palette is plain dark ink on a white canvas, light gray fills and one blue accent. It is a configurable default: the colours are the constants at the top of `excalidraw_lib.py` (and `assets/preview.css` repeats the same neutrals), so edit them once to match your brand and re-export. Keep fills light and strokes dark; the test suite enforces both. Roles: `APP` (the accent) for the component under design, `WORKER` for your workers, packages and jobs, `STORE` for durable stores such as a database, object storage or cache (draw with `cylinder`), `EXTERNAL` for third parties, `USER` for a person or browser, `CONFIG` for secrets and bindings, `RISK` for failure paths, `OPEN` for undecided parts. Use the constants; do not scatter literal colours through generators.

## What check() catches

`LABEL-ON-LEAF`, `LABEL-LABEL`, `LEAF-LEAF`, `ARROW-CROSS`, `ARROW-CROSS-ARROW`, `ARROW-OVER-TEXT` and `WRAP`. Fix them; do not suppress them. `warnings()` adds advisory `PARALLEL-H` and `PARALLEL-V` for arrows sharing a corridor; look at those by eye.

## API

Lifecycle: `reset()`, `check()`, `problems()`, `warnings()`, `write(path)`, `rect_of(handle)`. Text: `banner`, `label`. Shapes: `container`, `node`, `rnode`, `diamond` (centre coordinates), `ellipse`, `cylinder`, `rect`, `openmarker`, `block`, `band`, `relaynum`, `legend`, `lifeline`. Connectors: `connect(a, side, b, side, color, dashed, dotted, lbl)` with sides `l r t b`, and `arrow(points, ends=(a, b))` for explicit waypoints. Every builder asserts that its text fits, so an overflowing label fails at build time.

## Export to PNG

`smooth_scene.py` restyles the scene in place (no roughness, Arial-style text, solid fills) and reports rotated or translucent elements it cannot export; redraw those. `export_scene.py` then draws the scene at 4x and shrinks it to 1300 by 1040, with Excalidraw's own dash lengths so dashed means dashed. It needs Pillow and an Arial-style font (`--font` takes a path). A scene outside the 1300 by 1040 canvas is refused: place the whole view inside it.

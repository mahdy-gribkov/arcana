# HLD manifest contract

Contents: layout, required fields, targets, steps, APIs and setup, outputs.

The manifest is one JSON file. [The example](../assets/manifest.example.json) is complete and synthetic. Paths are relative to the project root, which is the manifest's folder (or its parent when the manifest sits in `src/`); `--project-root` overrides it. Paths that leave the root are rejected.

A working layout:

```text
<folder next to the README>/
  hld.json
  research/            evidence files the sources point at
  diagrams/source/     overview.excalidraw, overview.png, the generator
  diagrams/steps/      focus images, generated
```

## Required fields

| Field | Content |
| --- | --- |
| `schema_version` | `1` |
| `title`, `summary`, `status` | Design title, purpose, and `current`, `proposed` or `untested` |
| `sources` | Objects with stable `id`, readable `label`, and `url` (an https URL or a local file that exists) |
| `diagrams` | Objects with `id`, `label`, `base_png`, editable `source`, `source_ids`, `targets` |
| `overview_diagram` | Diagram ID shown before the flow groups |
| `flow_groups` | Objects with `id`, `title`, `entrypoint`, ordered `steps` |
| `apis` | Route registry; every route is used by at least one step (`[]` when none) |
| `setup` | Resource, permission and setup rows (`[]` when none) |
| `open_items` | Unresolved decisions and missing runtime proof, as strings (`[]` when none) |

IDs use lowercase letters, digits and hyphens and start with a letter. They are stable cross references, so changing a title does not change its ID.

## Targets

A diagram target has `id`, `shape` (`roundedrect` by default, `ellipse` or `diamond`) and `rect: [x, y, width, height]` in base-image pixels inside the 1300 by 1040 canvas. Rounded rectangles accept `radius` (default 10). `always_visible: [[x, y, w, h]]` keeps headers and branch labels at full strength in every focus image. Paste values from `rect_of(handle)` in the generator.

## Steps

Each step has `id`, `title`, `status`, `explanation`, `pseudocode`, `source_ids`, `api_ids`, plus `diagram`, `focus` (target IDs) and `image` (`diagrams/steps/<step-id>.png`). Annotation writes a sibling `.focus.json` holding the base hash, the focus mapping and the image hash. Validation rejects a stale base, image or focus map, so a changed diagram forces `--annotate` again. A step with no API call has `api_ids: []`; its local method names belong in the pseudocode. An unknown route goes to `open_items`, never into the registry.

## APIs, setup, extras

- API entries: `id`, `method`, `path` (a route or https URL taken from code or official docs), `kind` (`internal` or `external`), `caller`, `purpose`, `status`, `source_ids`.
- Setup rows: `resource`, `requirement`, `responsible` (a system or role), `status`, `source_ids`.
- Optional `side_diagrams`: `{diagram, explanation}` for lifecycle or policy topology that does not belong in the main flow.
- Optional `appendices`: `{id, title, content, source_ids, diagram_ids}` that keep supporting research after the main flow, collapsed in the HTML preview.

Strings may contain tabs and newlines but no other control characters.

## Outputs

`--output <dir>` writes `hld.md` (the note, image links prefixed by `--image-prefix`, ready to paste into the plan or README) and `hld.html` (a standalone light-theme preview with the images embedded). Both render from the manifest, so they cannot drift. Nothing is published anywhere.

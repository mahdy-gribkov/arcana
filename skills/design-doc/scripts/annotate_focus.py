"""Make a focus image from a base diagram: fade everything, restore the focused shapes at full strength and outline them in red."""
from pathlib import Path

# constraint: pixel colours drawn into a PNG cannot use CSS tokens. Red is the focus outline of the step images (RGB 224, 49, 49).
FOCUS_RED = (224, 49, 49)
INACTIVE_OPACITY = 0.25
FOCUS_STROKE = 4
EXPORT_SCALE = 4  # draw at 4x and shrink, so curved outlines stay smooth


def shape(draw, target, fill=None, outline=None, stroke=FOCUS_STROKE):
    """Draw one target (rounded rectangle, ellipse or diamond) described by {rect: [x, y, w, h], shape, radius}."""
    x, y, width, height = target["rect"]
    bounds = [x, y, x + width, y + height]
    kind = target.get("shape", "roundedrect")
    if kind == "ellipse":
        draw.ellipse(bounds, fill=fill, outline=outline, width=stroke)
    elif kind == "diamond":
        points = [(x + width / 2, y), (x + width, y + height / 2),
                  (x + width / 2, y + height), (x, y + height / 2)]
        if fill is not None:
            draw.polygon(points, fill=fill)
        if outline is not None:
            draw.line(points + [points[0]], fill=outline, width=stroke, joint="curve")
    else:
        draw.rounded_rectangle(bounds, radius=target.get("radius", 10), fill=fill, outline=outline, width=stroke)


def annotate(base, destination, targets, keep_rects):
    """Write `destination` (same size as `base`). `targets` are the focus shapes; `keep_rects` are [x, y, w, h] areas
    (headers, lane labels) that stay at full strength."""
    from PIL import Image, ImageDraw  # imported here so validation runs on a Python without Pillow

    image = Image.open(base).convert("RGB")
    faded = Image.blend(Image.new("RGB", image.size, "white"), image, INACTIVE_OPACITY)
    mask = Image.new("L", image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    for x, y, width, height in keep_rects:
        mask_draw.rectangle([x, y, x + width, y + height], fill=255)
    for target in targets:
        shape(mask_draw, target, fill=255)
    faded.paste(image, (0, 0), mask)

    scale = EXPORT_SCALE
    big = faded.resize(tuple(value * scale for value in image.size), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(big)
    for target in targets:
        scaled = {**target, "rect": [value * scale for value in target["rect"]],
                  "radius": target.get("radius", 10) * scale}
        shape(draw, scaled, outline=FOCUS_RED, stroke=FOCUS_STROKE * scale)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    big.resize(image.size, Image.Resampling.LANCZOS).save(destination)

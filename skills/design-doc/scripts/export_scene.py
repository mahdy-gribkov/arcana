"""Export a smooth scene (see smooth_scene.py) to a 1300 by 1040 PNG from its Excalidraw coordinates. Needs Pillow and an Arial-style font."""
import argparse
import math
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def font_path(explicit=None):
    choices = [explicit] if explicit else [
        '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/usr/share/fonts/truetype/msttcorefonts/Arial.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
        'C:/Windows/Fonts/arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
    for value in choices:
        if value and Path(value).is_file(): return value
    raise ValueError('No Arial-style font found in the usual places; pass --font with the path of a TTF file (Arial, Liberation Sans or DejaVu Sans).')


# Excalidraw's own stroke dash arrays (@excalidraw/excalidraw 0.18 getDashArrayDashed / getDashArrayDotted).
DASHES = {'dashed': lambda width: (8, 8 + width), 'dotted': lambda width: (1.5, 6 + width)}


def outline(kind, x, y, width, height, radius):
    if kind == 'ellipse':
        return [(x + width / 2 * (1 + math.cos(math.pi * step / 48)),
                 y + height / 2 * (1 + math.sin(math.pi * step / 48))) for step in range(97)]
    if kind == 'diamond':
        return [(x + width / 2, y), (x + width, y + height / 2), (x + width / 2, y + height),
                (x, y + height / 2), (x + width / 2, y)]
    radius = min(radius, width / 2, height / 2)
    corners = [(x + width - radius, y + radius, -90), (x + width - radius, y + height - radius, 0),
               (x + radius, y + height - radius, 90), (x + radius, y + radius, 180)]
    path = [(cx + radius * math.cos(math.radians(start + turn)), cy + radius * math.sin(math.radians(start + turn)))
            for cx, cy, start in corners for turn in range(0, 91, 10)]
    return path + path[:1]


def dashed_line(draw, path, pattern, color, width):
    on, off = pattern
    drawing, left, dash = True, on, [path[0]]
    for (x1, y1), (x2, y2) in zip(path, path[1:]):
        length, done = math.hypot(x2 - x1, y2 - y1), 0
        while length - done > left:
            done += left
            spot = (x1 + (x2 - x1) * done / length, y1 + (y2 - y1) * done / length)
            if drawing:
                draw.line(dash + [spot], fill=color, width=width, joint='curve')
            dash, drawing = [spot], not drawing
            left = on if drawing else off
        left -= length - done
        if drawing:
            dash.append((x2, y2))
    if drawing and len(dash) > 1:
        draw.line(dash, fill=color, width=width, joint='curve')


def export(source, output, font=None):
    elements = json.loads(Path(source).read_text(encoding='utf-8'))['elements']
    visible = [e for e in elements if not e.get('isDeleted') and e['type'] != 'frame']
    for e in visible:
        if e['type'] not in {'rectangle', 'ellipse', 'diamond', 'text', 'arrow', 'line'}:
            raise ValueError(f'Use native Excalidraw export for unsupported element {e["type"]}.')
        if e.get('roughness', 0) or e.get('angle', 0) or e.get('fillStyle', 'solid') != 'solid':
            raise ValueError('This exporter supports smooth, unrotated solid scenes; use native export for this scene.')
        if e['type'] == 'text' and e.get('fontFamily') != 2:
            raise ValueError('Use fontFamily 2 for smooth scenes (run smooth_scene.py first) or native export for another font.')
        if e.get('strokeStyle', 'solid') not in {'solid', *DASHES}:
            raise ValueError(f'Use native export for stroke style {e["strokeStyle"]}.')
        if e.get('opacity', 100) != 100:
            raise ValueError('Export an opaque baseline and use annotate_focus for fading, or use native export.')
    scale = 4
    image = Image.new('RGB', (1300 * scale, 1040 * scale), 'white')
    draw = ImageDraw.Draw(image)
    font = font_path(font)
    def point(values): return tuple(round(value * scale) for value in values)
    for e in visible:
        x, y, width, height = (e[k] for k in ('x', 'y', 'width', 'height'))
        if e['type'] in {'arrow', 'line'}:
            xs = [x + dx for dx, _ in e['points']]
            ys = [y + dy for _, dy in e['points']]
        else:
            xs, ys = [x, x + width], [y, y + height]
        if min(xs + ys) < 0 or max(xs) > 1300 or max(ys) > 1040:
            raise ValueError('Scene leaves the fixed canvas; position the complete view within 1300 by 1040.')
        kind, color = e['type'], e.get('strokeColor', '#1e1e1e')
        stroke = round(e.get('strokeWidth', 2) * scale)
        fill = e.get('backgroundColor', 'transparent')
        fill = None if fill == 'transparent' else fill
        bounds = point((x, y, x + width, y + height))
        style = e.get('strokeStyle', 'solid')
        dashes = [length * scale for length in DASHES[style](e.get('strokeWidth', 2))] if style in DASHES else None
        solid = None if dashes else color
        radius = 10 if kind == 'rectangle' and e.get('roundness') else 0
        if kind == 'rectangle':
            draw.rounded_rectangle(bounds, radius=radius * scale, fill=fill, outline=solid, width=stroke)
        elif kind == 'ellipse': draw.ellipse(bounds, fill=fill, outline=solid, width=stroke)
        elif kind == 'diamond':
            draw.polygon([point((x + width / 2, y)), point((x + width, y + height / 2)),
                          point((x + width / 2, y + height)), point((x, y + height / 2))],
                         fill=fill, outline=solid, width=stroke)
        elif kind == 'text':
            face = ImageFont.truetype(font, round(e['fontSize'] * scale))
            for index, line in enumerate(e['text'].split('\n')):
                yy = y + index * e['fontSize'] * e.get('lineHeight', 1.28)
                align = e.get('textAlign', 'left')
                xx = x + width / 2 if align == 'center' else x + width if align == 'right' else x
                draw.text(point((xx, yy)), line, font=face, fill=color,
                          anchor={'left': 'lt', 'center': 'mt', 'right': 'rt'}[align])
        else:
            points = [(x + dx, y + dy) for dx, dy in e['points']]
            if not dashes:
                draw.line([point(p) for p in points], fill=color, width=stroke)
            if e.get('endArrowhead'):
                a, b = points[-2:]
                angle = math.atan2(b[1] - a[1], b[0] - a[0])
                # Filled arrowheads, so a call reads as a call.
                left = (b[0] - 18 * math.cos(angle - .48), b[1] - 18 * math.sin(angle - .48))
                right = (b[0] - 18 * math.cos(angle + .48), b[1] - 18 * math.sin(angle + .48))
                draw.polygon([point(b), point(left), point(right)], fill=color)
        if dashes and kind != 'text':
            path = points if kind in {'arrow', 'line'} else outline(kind, x, y, width, height, radius)
            dashed_line(draw, [(px * scale, py * scale) for px, py in path], dashes, color, stroke)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.resize((1300, 1040), Image.Resampling.LANCZOS).save(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--font')
    args = parser.parse_args()
    try: export(args.source, args.output, args.font)
    except (ValueError, KeyError, OSError) as error: parser.exit(1, f'{error}\n')

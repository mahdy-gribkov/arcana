"""Builder and defect gate for architecture diagrams stored as .excalidraw files.

Import this from a small generator script, build with the primitives, call check() (raises on any layout defect), then write().

    import sys; sys.path.insert(0, "<skill dir>/scripts")
    from excalidraw_lib import *
    reset()
    banner(0, 0, "Booking confirmation flow")
    admin = container(0, 60, 820, 300, "apps/admin", *APP)
    save = rnode(30, 120, 300, "apps/admin", "saveBooking()", *APP)
    mail = rnode(430, 120, 320, "packages/comms", "sendConfirmation()", *WORKER, dashed=True)
    connect(save, "r", mail, "l", color=WORKER[1], lbl="enqueue")
    check()
    write("booking.excalidraw")

Grammar:
- A container() is a big hatched boundary box (an app, a package, a worker). A node, rnode, diamond, ellipse or cylinder is a leaf.
  A leaf or label may sit inside a container. A label may not sit on a sibling leaf, and an arrow may not cross a leaf that is not
  one of its endpoints. check() enforces all three, plus text that would wrap out of its box.
- dashed=True marks NEW or proposed. openmarker() marks an open decision. Solid arrows are verified calls, dashed are proposed,
  dotted are derived or decision-applies.
- Light theme only: there is no dark variant.
"""
import json
import random
import time

# constraint: an Excalidraw scene stores literal hex colours, so the palette is a set of constants here, not design tokens.
# This is the DEFAULT palette: plain dark ink, light gray fills and one accent (blue). To match your brand, edit the pairs
# below (and assets/preview.css, which repeats the same neutrals). Keep fills light (the palette test enforces it) and
# strokes dark enough to read on the canvas. A (fill, stroke) pair per role; INK and SUB are text colours.
APP = ('#E8F0FE', '#2F6FEB')       # the component under design: your app, service or route surface (the one accent)
WORKER = ('#F3F4F6', '#4B5563')    # your worker, shared package or job
STORE = ('#E5E7EB', '#374151')     # durable store: database, object storage, cache (drawn as a cylinder)
EXTERNAL = ('#FFFFFF', '#1F2328')  # a third party you call or that calls you
USER = ('#F9FAFB', '#57606A')      # a person or a browser
CONFIG = ('#F3F4F6', '#6B7280')    # secrets, settings, bindings
RISK = ('#E5E7EB', '#111827')      # failure path or risk (darkest stroke)
OPEN = ('#F3F4F6', '#6B7280')      # open decision (see openmarker)
INK = '#1F2328'
SUB = '#57606A'
CANVAS = '#FFFFFF'                 # ground
FACT = 0.62                        # average glyph advance as a fraction of font size; deliberately wide so text never overflows

els = []
TEXT_HOME = {}
ARROWS = []
CONTAINERS = set()
LEAVES = set()


class LayoutError(Exception):
    """Raised by check() when the diagram has layout defects."""


def reset():
    """Clear module state so one process can build several diagrams."""
    els.clear()
    TEXT_HOME.clear()
    ARROWS.clear()
    CONTAINERS.clear()
    LEAVES.clear()


def _nz():
    return random.randint(1, 2**31 - 1)


def _rid():
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=18))


def tw(s, fs):
    return max((len(line) for line in s.split('\n')), default=0) * fs * FACT


def th(s, fs):
    return (s.count('\n') + 1) * fs * 1.28


def _base(**kw):
    e = dict(angle=0, strokeColor=INK, backgroundColor='transparent', fillStyle='solid', strokeWidth=2,
             strokeStyle='solid', roughness=1, opacity=100, groupIds=[], frameId=None, roundness=None,
             seed=_nz(), version=1, versionNonce=_nz(), isDeleted=False, boundElements=[],
             updated=int(time.time() * 1000), link=None, locked=False)
    e.update(kw)
    return e


def _shape(kind, x, y, w, h, fill, stroke, emph=False, dashed=False, hatch=False, leaf=True):
    i = _rid()
    els.append(_base(id=i, type=kind, x=x, y=y, width=w, height=h, backgroundColor=fill, strokeColor=stroke,
                     strokeWidth=4 if emph else 2, strokeStyle='dashed' if dashed else 'solid',
                     fillStyle='cross-hatch' if hatch else 'solid',
                     roundness=({'type': 3} if kind == 'rectangle' else None)))
    (LEAVES if leaf else CONTAINERS).add(i)
    return dict(id=i, x=x, y=y, w=w, h=h, k=kind)


def _bind(host, s, fs, color):
    ti = _rid()
    hh = (s.count('\n') + 1) * fs * 1.28
    els.append(_base(id=ti, type='text', x=host['x'] + 6, y=host['y'] + (host['h'] - hh) / 2, width=host['w'] - 12,
                     height=hh, strokeColor=color, text=s, fontSize=fs, fontFamily=5, textAlign='center',
                     verticalAlign='middle', containerId=host['id'], originalText=s, lineHeight=1.28,
                     autoResize=False, baseline=int(fs)))
    for e in els:
        if e['id'] == host['id']:
            e['boundElements'] = (e.get('boundElements') or []) + [{'type': 'text', 'id': ti}]
    TEXT_HOME[ti] = host['id']
    return ti


def label(x, y, s, fs=13, color=SUB, w=None, home=None):
    """Free-floating text. Pass home=<box id> when it legitimately sits inside that box."""
    w = w if w is not None else tw(s, fs) + 4
    i = _rid()
    els.append(_base(id=i, type='text', x=x, y=y, width=w, height=th(s, fs), strokeColor=color, text=s,
                     fontSize=fs, fontFamily=5, textAlign='left', verticalAlign='top', originalText=s,
                     lineHeight=1.28, autoResize=False, baseline=int(fs)))
    if home:
        TEXT_HOME[i] = home
    return i


def banner(x, y, s, color=INK, fs=30):
    return label(x, y, s, fs=fs, color=color, w=tw(s, fs) + 8)


def container(x, y, w, h, title, fill, stroke, dashed=False, tfs=17):
    """Big hatched boundary box with a free top-left title."""
    g = _shape('rectangle', x, y, w, h, fill, stroke, dashed=dashed, hatch=True, leaf=False)
    assert tw(title, tfs) <= w - 16, f'container title overflow {title!r}'
    label(x + 14, y + 9, title, fs=tfs, color=stroke, w=tw(title, tfs) + 6, home=g['id'])
    return g


def node(x, y, w, h, s, fill, stroke, fs=13, emph=False, dashed=False, kind='rectangle'):
    g = _shape(kind, x, y, w, h, fill, stroke, emph=emph, dashed=dashed)
    assert tw(s, fs) <= w - 10 and th(s, fs) <= h - 4, f'node overflow {s!r}'
    _bind(g, s, fs, stroke)
    return g


def rnode(x, y, w, home, name, fill, stroke, fs=13, emph=False, dashed=False):
    """Node with a small home tag on top (the app, package or file that owns it) and the component name below."""
    nl = name.count('\n') + 1
    h = 10 + int(11 * 1.28) + int(nl * fs * 1.28) + 8
    g = _shape('rectangle', x, y, w, h, fill, stroke, emph=emph, dashed=dashed)
    assert tw(home, 11) <= w - 16 and tw(name, fs) <= w - 16, f'rnode overflow {home!r}/{name!r}'
    label(x + 10, y + 7, home, fs=11, color=stroke, w=tw(home, 11) + 4, home=g['id'])
    label(x + 10, y + 7 + int(11 * 1.28) + 2, name, fs=fs, color=INK, w=w - 16, home=g['id'])
    return g


def diamond(cx, cy, w, h, s, fill, stroke, fs=13):
    """Decision. Draw it inside the container that owns the decision. Takes centre coordinates."""
    g = _shape('diamond', cx - w / 2, cy - h / 2, w, h, fill, stroke, hatch=True)
    assert tw(s, fs) <= w * 0.6 and th(s, fs) <= h * 0.55, f'diamond overflow {s!r}'
    _bind(g, s, fs, stroke)
    return g


def ellipse(x, y, w, h, s, fill, stroke, fs=13):
    g = _shape('ellipse', x, y, w, h, fill, stroke)
    assert tw(s, fs) <= w * 0.72 and th(s, fs) <= h * 0.6, f'ellipse overflow {s!r}'
    _bind(g, s, fs, stroke)
    return g


def cylinder(x, y, w, h, s, fill=STORE[0], stroke=STORE[1], fs=13):
    """Durable store (database, object storage, cache). Excalidraw has no cylinder primitive, so a store is an ellipse leaf in the STORE colours."""
    g = _shape('ellipse', x, y, w, h, fill, stroke)
    assert tw(s, fs) <= w * 0.8 and th(s, fs) <= h * 0.62, f'cylinder overflow {s!r}'
    _bind(g, s, fs, stroke)
    return g


def rect(x, y, w, h, fill, stroke, emph=False, dashed=False, hatch=False, leaf=True):
    """Raw rectangle with no bound text, for legend swatches and free-form boxes."""
    return _shape('rectangle', x, y, w, h, fill, stroke, emph=emph, dashed=dashed, hatch=hatch, leaf=leaf)


def openmarker(x, y, w, s):
    """Dotted node marking an OPEN decision. Distinct from dashed=True, which marks NEW."""
    g = _shape('rectangle', x, y, w, 54, OPEN[0], OPEN[1], dashed=True)
    assert tw('? ' + s, 11) <= w - 12, f'open marker overflow {s!r}'
    _bind(g, '? ' + s, 11, OPEN[1])
    return g


def block(x, y, w, title, lines, fill, stroke, tfs=15, bfs=13, hatch=False):
    """Titled block of short lines, for dense lists. Not for paragraphs."""
    lh = int(bfs * 1.5)
    h = 14 + int(tfs * 1.4) + len(lines) * lh + 10
    g = _shape('rectangle', x, y, w, h, fill, stroke, hatch=hatch)
    label(x + 14, y + 10, title, fs=tfs, color=stroke, w=w - 20, home=g['id'])
    yy = y + 12 + int(tfs * 1.4)
    for line in lines:
        label(x + 16, yy, line, fs=bfs, color=INK, w=w - 24, home=g['id'])
        yy += lh
    return g


def band(x, y, w, h, title, stroke=USER[1]):
    """Trust-boundary or swimlane band: a dashed unfilled region with a top-left title. A container, so leaves may sit inside."""
    g = _shape('rectangle', x, y, w, h, 'transparent', stroke, dashed=True, leaf=False)
    label(x + 12, y + 8, title, fs=12, color=stroke, w=tw(title, 12) + 6, home=g['id'])
    return g


def relaynum(cx, cy, n, fill=APP[0], stroke=APP[1]):
    """Small numbered marker for the order of a flow (1..N)."""
    d = 26
    g = _shape('ellipse', cx - d / 2, cy - d / 2, d, d, fill, stroke)
    _bind(g, str(n), 13, stroke)
    return g


def legend(x, y, w, title, rows, fill=USER[0], stroke=USER[1]):
    """Legend panel. rows = [(kind, text)] with kind one of app, worker, store, decision, solid, dashed, dotted or ''."""
    lh = 20
    h = 16 + int(15 * 1.4) + len(rows) * lh + 10
    g = _shape('rectangle', x, y, w, h, fill, stroke, leaf=False)
    label(x + 14, y + 10, title, fs=15, color=stroke, w=w - 20, home=g['id'])
    yy = y + 14 + int(15 * 1.4)
    for kind, text in rows:
        sx, sy = x + 16, yy + 2
        if kind == 'app':
            rect(sx, sy, 16, 12, APP[0], APP[1], leaf=False)
        elif kind == 'worker':
            rect(sx, sy, 16, 12, WORKER[0], WORKER[1], leaf=False)
        elif kind == 'store':
            _shape('ellipse', sx, sy, 16, 12, STORE[0], STORE[1], leaf=False)
        elif kind == 'decision':
            _shape('diamond', sx, sy, 16, 14, OPEN[0], OPEN[1], leaf=False)
        elif kind in ('solid', 'dashed', 'dotted'):
            arrow([(sx, sy + 6), (sx + 16, sy + 6)], color=stroke, dashed=(kind == 'dashed'), dotted=(kind == 'dotted'), head=False)
        label(x + 40, yy, text, fs=12, color=INK, w=w - 48, home=g['id'])
        yy += lh
    return g


def lifeline(xc, y0, y1):
    els.append(_base(id=_rid(), type='line', x=xc, y=y0, width=0, height=y1 - y0, points=[[0, 0], [0, y1 - y0]],
                     strokeColor='#8C959F', strokeStyle='dashed', strokeWidth=1))


def rect_of(g):
    """[x, y, width, height] of a shape handle, as integers: the value to paste into a build_hld.py manifest target."""
    return [round(g['x']), round(g['y']), round(g['w']), round(g['h'])]


def port(g, side, frac=0.5):
    if side == 'r':
        return (g['x'] + g['w'], g['y'] + g['h'] * frac)
    if side == 'l':
        return (g['x'], g['y'] + g['h'] * frac)
    if side == 't':
        return (g['x'] + g['w'] * frac, g['y'])
    if side == 'b':
        return (g['x'] + g['w'] * frac, g['y'] + g['h'])
    raise ValueError(f"port side must be 'l', 'r', 't' or 'b', not {side!r}")


def arrow(pts, color=SUB, dashed=False, dotted=False, lbl='', ends=(), lbl_side=1, head=True):
    """Polyline arrow through absolute waypoints. Pass ends=(from, to) so check() exempts the endpoint shapes.
    The label sits on the longest segment."""
    ox, oy = pts[0]
    rel = [[p[0] - ox, p[1] - oy] for p in pts]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    style = 'dotted' if dotted else ('dashed' if dashed else 'solid')
    els.append(_base(id=_rid(), type='arrow', x=ox, y=oy, width=max(xs) - min(xs), height=max(ys) - min(ys),
                     points=rel, strokeColor=color, strokeStyle=style,
                     roundness=None, startArrowhead=None, endArrowhead='arrow' if head else None))
    lbl_id = None
    if lbl:
        best = max(range(len(pts) - 1), key=lambda i: (pts[i + 1][0] - pts[i][0]) ** 2 + (pts[i + 1][1] - pts[i][1]) ** 2)
        (x1, y1), (x2, y2) = pts[best], pts[best + 1]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        lw = tw(lbl, 11) + 4
        if abs(x2 - x1) >= abs(y2 - y1):
            lx, ly = mx - lw / 2, my - 16 * lbl_side - 2
        else:
            lx, ly = mx + 10 * lbl_side, my - 7
        lbl_id = label(lx, ly, lbl, fs=11, color=color, w=lw)
    ARROWS.append((pts, set(e['id'] for e in ends if e), lbl_id))


def connect(g1, s1, g2, s2, color=SUB, dashed=False, dotted=False, lbl='', f1=0.5, f2=0.5, lbl_side=1):
    """Orthogonal connector between two shapes' edge ports: straight when aligned, else one or two elbows."""
    p1 = port(g1, s1, f1)
    p2 = port(g2, s2, f2)
    if abs(p1[0] - p2[0]) < 2 or abs(p1[1] - p2[1]) < 2:
        pts = [p1, p2]
    elif s1 in ('r', 'l') and s2 in ('l', 'r'):
        mx = (p1[0] + p2[0]) / 2
        pts = [p1, (mx, p1[1]), (mx, p2[1]), p2]
    elif s1 in ('t', 'b') and s2 in ('t', 'b'):
        my = (p1[1] + p2[1]) / 2
        pts = [p1, (p1[0], my), (p2[0], my), p2]
    elif s1 in ('r', 'l'):
        pts = [p1, (p2[0], p1[1]), p2]
    else:
        pts = [p1, (p1[0], p2[1]), p2]
    arrow(pts, color=color, dashed=dashed, dotted=dotted, lbl=lbl, ends=(g1, g2), lbl_side=lbl_side)


def _bbox(e):
    return (e['x'], e['y'], e['x'] + e.get('width', 0), e['y'] + e.get('height', 0))


def _inter(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return ix * iy


def _seg_rect(p1, p2, r, pad=3):
    """Liang-Barsky: does the segment p1-p2 touch rectangle r grown by pad?"""
    x1, y1 = p1
    x2, y2 = p2
    rx1, ry1, rx2, ry2 = r[0] - pad, r[1] - pad, r[2] + pad, r[3] + pad
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in [(-dx, x1 - rx1), (dx, rx2 - x1), (-dy, y1 - ry1), (dy, ry2 - y1)]:
        if p == 0:
            if q < 0:
                return False
        else:
            ratio = q / p
            if p < 0:
                t0 = max(t0, ratio)
            else:
                t1 = min(t1, ratio)
    return t0 <= t1


def _segments(pts):
    return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]


def _ccw(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])


def _proper_cross(s1, s2):
    """True only when the segments cross through each other's interior. Shared endpoints and collinear touches do not count."""
    a, b = s1
    c, d = s2
    return (_ccw(a, b, c) * _ccw(a, b, d) < 0) and (_ccw(c, d, a) * _ccw(c, d, b) < 0)


def problems():
    """The layout defects of the current diagram. Empty means clean."""
    leaf = [e for e in els if e['id'] in LEAVES]
    texts = [e for e in els if e['type'] == 'text']
    out = []
    for t in texts:  # a label sitting on a leaf it does not belong to
        home = TEXT_HOME.get(t['id']) or t.get('containerId')
        for lf in leaf:
            if lf['id'] == home:
                continue
            ov = _inter(_bbox(t), _bbox(lf))
            if ov > 1:
                amin = min(t['width'] * t['height'], lf['width'] * lf['height']) or 1
                if ov > 0.10 * amin:
                    out.append(f"LABEL-ON-LEAF {t['text'][:22]!r} @({int(t['x'])},{int(t['y'])})")
    for i in range(len(texts)):  # two labels overlapping
        for j in range(i + 1, len(texts)):
            a, b = texts[i], texts[j]
            ov = _inter(_bbox(a), _bbox(b))
            if ov > 1 and ov > 0.18 * (min(a['width'] * a['height'], b['width'] * b['height']) or 1):
                out.append(f"LABEL-LABEL {a['text'][:16]!r} x {b['text'][:16]!r}")
    for i in range(len(leaf)):  # two leaves overlapping
        for j in range(i + 1, len(leaf)):
            a, b = leaf[i], leaf[j]
            ov = _inter(_bbox(a), _bbox(b))
            if ov > 1 and ov > 0.08 * (min(a['width'] * a['height'], b['width'] * b['height']) or 1):
                out.append(f"LEAF-LEAF @({int(a['x'])},{int(a['y'])}) x @({int(b['x'])},{int(b['y'])})")
    for pts, ends, _label_id in ARROWS:  # an arrow through a leaf that is not its endpoint
        for k in range(len(pts) - 1):
            for lf in leaf:
                if lf['id'] in ends:
                    continue
                if _seg_rect(pts[k], pts[k + 1], _bbox(lf)):
                    name = next((c['text'][:18] for c in els if c.get('containerId') == lf['id']), '?')
                    out.append(f"ARROW-CROSS seg{k} x {name!r}")
    for i in range(len(ARROWS)):  # an arrow crossing another arrow
        for j in range(i + 1, len(ARROWS)):
            if any(_proper_cross(s1, s2) for s1 in _segments(ARROWS[i][0]) for s2 in _segments(ARROWS[j][0])):
                out.append(f"ARROW-CROSS-ARROW #{i} x #{j}")
    for pts, ends, label_id in ARROWS:  # an arrow running through a foreign label
        for t in texts:
            if t['id'] == label_id:
                continue
            host = TEXT_HOME.get(t['id']) or t.get('containerId')
            if host in ends:
                continue
            if any(_seg_rect(s[0], s[1], _bbox(t), pad=1) for s in _segments(pts)):
                out.append(f"ARROW-OVER-TEXT {t['text'][:22]!r} @({int(t['x'])},{int(t['y'])})")
    for e in texts:  # a line wider than its box will wrap and overflow
        for line in e['text'].split('\n'):
            if len(line) * e['fontSize'] * FACT > e['width'] + 2:
                out.append(f"WRAP {line[:28]!r} (w={int(e['width'])})")
                break
    return out


def warnings():
    """Advisory only: near-parallel arrow segments sharing a corridor (under 12px apart, over 20px of overlap)."""
    out = []
    segs = []
    for pts, _ends, _label_id in ARROWS:
        segs += _segments(pts)
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            (a1, a2), (b1, b2) = segs[i], segs[j]
            if abs(a1[1] - a2[1]) < 2 and abs(b1[1] - b2[1]) < 2 and abs(a1[1] - b1[1]) < 12:
                ov = min(max(a1[0], a2[0]), max(b1[0], b2[0])) - max(min(a1[0], a2[0]), min(b1[0], b2[0]))
                if ov > 20:
                    out.append(f"PARALLEL-H y~{int(a1[1])}")
            if abs(a1[0] - a2[0]) < 2 and abs(b1[0] - b2[0]) < 2 and abs(a1[0] - b1[0]) < 12:
                ov = min(max(a1[1], a2[1]), max(b1[1], b2[1])) - max(min(a1[1], a2[1]), min(b1[1], b2[1]))
                if ov > 20:
                    out.append(f"PARALLEL-V x~{int(a1[0])}")
    return out


def check():
    """Raise LayoutError listing every defect, or return True. Call before write()."""
    found = problems()
    if found:
        raise LayoutError("%d layout problems:\n  %s" % (len(found), "\n  ".join(found[:60])))
    return True


def write(path, source='arcana-design-doc'):
    """Write the scene as an .excalidraw file and return the element count."""
    doc = {'type': 'excalidraw', 'version': 2, 'source': source, 'elements': els,
           'appState': {'gridSize': None, 'viewBackgroundColor': CANVAS}, 'files': {}}
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(doc, handle, indent=2)
    return len(els)

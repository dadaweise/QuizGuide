"""Small SVG renderers for the diagram manual (activity, sequence, class, use case).

Standard library only. Each render function returns an SVG string.
Highlight colour marks proposed additions or corrections; it is not UML notation.
"""

from xml.sax.saxutils import escape

INK = "#09251C"
PANEL = "#F3D2AF"
PAPER = "#FFFDF9"
LANE_HEAD = "#F8EADC"
HL = "#E8590C"          # highlight: new or corrected element
GONE = "#6B6B6B"        # cross: element to delete
FONT = "font-family='Segoe UI, Arial, sans-serif'"
CHAR_W = 6.4            # approximate width of one 12px character


def text_width(text, size=12):
    return len(text) * CHAR_W * size / 12


def wrap(text, limit):
    words, lines, line = text.split(), [], ""
    for word in words:
        if line and len(line) + 1 + len(word) > limit:
            lines.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        lines.append(line)
    return lines or [""]


def t(x, y, text, size=12, anchor="middle", weight="normal", fill=INK, italic=False):
    style = " font-style='italic'" if italic else ""
    return (f"<text x='{x:.1f}' y='{y:.1f}' font-size='{size}' text-anchor='{anchor}' "
            f"font-weight='{weight}' fill='{fill}'{style}>{escape(text)}</text>")


def bt(x, y, text, size=12, anchor="middle", weight="normal", fill=INK, italic=False):
    """Text on a pale background so lifelines and frame lines do not cut through it."""
    w = text_width(text, size) + 6
    left = {"middle": x - w / 2, "start": x - 3, "end": x - w + 3}[anchor]
    return (f"<rect x='{left:.1f}' y='{y - size + 1:.1f}' width='{w:.1f}' height='{size + 3}' fill='{PAPER}' opacity='0.92'/>"
            + t(x, y, text, size, anchor, weight, fill, italic))


def svg_doc(width, height, body, title, desc):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width:.0f} {height:.0f}' "
            f"width='{width:.0f}' height='{height:.0f}' role='img' {FONT}>"
            f"<title>{escape(title)}</title><desc>{escape(desc)}</desc>"
            f"<defs>"
            f"<marker id='open' viewBox='0 0 10 10' refX='9' refY='5' markerUnits='userSpaceOnUse' markerWidth='11' markerHeight='11' orient='auto-start-reverse'>"
            f"<path d='M0,0 L10,5 L0,10' fill='none' stroke='context-stroke' stroke-width='1.4'/></marker>"
            f"<marker id='filled' viewBox='0 0 10 10' refX='9' refY='5' markerUnits='userSpaceOnUse' markerWidth='11' markerHeight='11' orient='auto'>"
            f"<path d='M0,0 L10,5 L0,10 z' fill='context-stroke'/></marker>"
            f"<marker id='hollow' viewBox='0 0 12 12' refX='11' refY='6' markerUnits='userSpaceOnUse' markerWidth='16' markerHeight='16' orient='auto'>"
            f"<path d='M0,0 L11,6 L0,12 z' fill='{PAPER}' stroke='context-stroke' stroke-width='1.2'/></marker>"
            f"</defs>"
            f"<rect width='100%' height='100%' fill='{PAPER}'/>{body}</svg>")


def gone_mark(x, y, w, h):
    """Grey cross over an element the reader deletes."""
    return (f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' fill='{PAPER}' opacity='0.3'/>"
            f"<path d='M{x:.1f},{y:.1f} L{x+w:.1f},{y+h:.1f} M{x+w:.1f},{y:.1f} L{x:.1f},{y+h:.1f}' "
            f"stroke='{GONE}' stroke-width='1.8'/>")


def legend(x, y):
    return (f"<rect x='{x}' y='{y}' width='16' height='12' fill='none' stroke='{HL}' stroke-width='2.5'/>"
            + t(x + 22, y + 10, "Orange = new or corrected in this step (teaching mark, not UML)",
                11, "start", fill=HL))


# ---------------------------------------------------------------- activity

LANE_W = 270
ROW_H = 64
TOP = 46


def activity(spec):
    """spec: lanes, nodes {id: dict(type, lane, row, label, dx, hl)}, edges [dict]."""
    lanes = spec["lanes"]
    lane_ws = spec.get("lane_ws", [LANE_W] * len(lanes))
    lane_x = [sum(lane_ws[:i]) for i in range(len(lanes))]
    geo = {}
    for nid, n in spec["nodes"].items():
        cx = lane_x[n["lane"]] + lane_ws[n["lane"]] / 2 + n.get("dx", 0)
        cy = TOP + 24 + n["row"] * ROW_H
        kind = n["type"]
        if kind == "action":
            lines = wrap(n["label"], 24)
            w = max(110, max(text_width(s) for s in lines) + 26)
            h = 14 + 15 * len(lines)
        elif kind in ("decision", "merge"):
            w = h = 34
        else:
            w = h = 22
        geo[nid] = dict(cx=cx, cy=cy, w=w, h=h)
    max_row = max([n["row"] for n in spec["nodes"].values()] or [spec.get("min_rows", 3)])
    max_row = max(max_row, spec.get("min_rows", 0))
    width = sum(lane_ws)
    height = TOP + 24 + max_row * ROW_H + 70
    out = []
    for i, name in enumerate(lanes):
        lx, lw = lane_x[i], lane_ws[i]
        out.append(f"<rect x='{lx}' y='0' width='{lw}' height='{height-34}' fill='none' stroke='{INK}' stroke-width='1.2'/>")
        out.append(f"<rect x='{lx}' y='0' width='{lw}' height='{TOP-14}' fill='{LANE_HEAD}' stroke='{INK}' stroke-width='1.2'/>")
        out.append(t(lx + lw / 2, 21, name, 13, weight="bold"))
        if i in spec.get("gone_lanes", ()):
            out.append(gone_mark(lx, 0, lw, height - 34))

    def port(nid, side):
        g = geo[nid]
        return {"top": (g["cx"], g["cy"] - g["h"] / 2), "bottom": (g["cx"], g["cy"] + g["h"] / 2),
                "left": (g["cx"] - g["w"] / 2, g["cy"]), "right": (g["cx"] + g["w"] / 2, g["cy"])}[side]

    for e in spec["edges"]:
        s, d = geo[e["from"]], geo[e["to"]]
        color = HL if e.get("hl") else INK
        width_px = 2.2 if e.get("hl") else 1.2
        route = e.get("route")
        facing = "right" if d["cx"] > s["cx"] else "left"
        opposite = "left" if facing == "right" else "right"
        below = d["cy"] > s["cy"]
        if "via" in e:
            pts = [port(e["from"], e.get("sp", "bottom"))] + list(e["via"]) + [port(e["to"], e.get("ep", "top"))]
        elif route == "straight":
            pts = [port(e["from"], e.get("sp", "bottom")), port(e["to"], e.get("ep", "top"))]
        elif route == "elbow":
            a, b = port(e["from"], "bottom"), port(e["to"], "top")
            ym = (a[1] + b[1]) / 2
            pts = [a, (a[0], ym), (b[0], ym), b]
        elif route == "hv":
            a = port(e["from"], facing)
            b = port(e["to"], "top" if below else "bottom")
            pts = [a, (b[0], a[1]), b]
        elif route == "vh":
            a = port(e["from"], "bottom" if below else "top")
            b = port(e["to"], opposite)
            pts = [a, (a[0], b[1]), b]
        elif route == "up":
            a = port(e["from"], "top")
            b = port(e["to"], e.get("ep", "right"))
            pts = [a, (a[0], b[1]), b]
        elif route == "loop":
            side = e.get("side", "left")
            a = port(e["from"], side)
            ep = e.get("ep", side)
            b = port(e["to"], ep)
            gx = e["gx"]
            if ep == "top":
                pts = [a, (gx, a[1]), (gx, b[1] - 14), (b[0], b[1] - 14), b]
            else:
                pts = [a, (gx, a[1]), (gx, b[1]), b]
        elif abs(s["cx"] - d["cx"]) < 4 and d["cy"] > s["cy"]:
            pts = [port(e["from"], "bottom"), port(e["to"], "top")]
        elif abs(s["cy"] - d["cy"]) < 4:
            side = "right" if d["cx"] > s["cx"] else "left"
            pts = [port(e["from"], side), port(e["to"], "left" if side == "right" else "right")]
        elif d["cy"] > s["cy"]:
            sp = e.get("sp")
            if sp == "bottom":
                a = port(e["from"], "bottom")
                pts = [a, (a[0], d["cy"]), port(e["to"], "left" if d["cx"] > s["cx"] else "right")]
            else:
                side = "right" if d["cx"] > s["cx"] else "left"
                a = port(e["from"], side)
                pts = [a, (d["cx"], a[1]), port(e["to"], "top")]
        else:   # loop back upward
            side = e.get("side", "left")
            a = port(e["from"], side)
            b = port(e["to"], side)
            if side == "left":
                gx = e.get("gx", min(a[0], b[0]) - 26)
            else:
                gx = e.get("gx", max(a[0], b[0]) + 26)
            pts = [a, (gx, a[1]), (gx, b[1]), b]
        path = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        out.append(f"<polyline points='{path}' fill='none' stroke='{color}' stroke-width='{width_px}' marker-end='url(#open)'/>")
        if e.get("guard"):
            (x1, y1), (x2, y2) = pts[0], pts[1]
            label = f"[{e['guard']}]"
            if abs(x1 - x2) < 1:      # vertical first segment
                lx, ly, anchor = x1 + 6, y1 + 15, "start"
            else:
                lx = x1 + (8 if x2 > x1 else -8)
                ly, anchor = y1 - 6, "start" if x2 > x1 else "end"
            if "glabel" in e:
                lx, ly, anchor = e["glabel"][0], e["glabel"][1], "start"
            out.append(t(lx, ly, label, 11, anchor, fill=color, italic=True))

    for nid, n in spec["nodes"].items():
        g = geo[nid]
        cx, cy, w, h = g["cx"], g["cy"], g["w"], g["h"]
        hl = n.get("hl")
        stroke = HL if hl else INK
        sw = 2.6 if hl else 1.3
        kind = n["type"]
        if kind == "start":
            out.append(f"<circle cx='{cx}' cy='{cy}' r='10' fill='{INK}'/>")
        elif kind == "end":
            out.append(f"<circle cx='{cx}' cy='{cy}' r='11' fill='none' stroke='{INK}' stroke-width='1.5'/>"
                       f"<circle cx='{cx}' cy='{cy}' r='7' fill='{INK}'/>")
        elif kind in ("decision", "merge"):
            out.append(f"<polygon points='{cx},{cy-17} {cx+17},{cy} {cx},{cy+17} {cx-17},{cy}' "
                       f"fill='{PANEL}' stroke='{stroke}' stroke-width='{sw}'/>")
            if n.get("label"):
                out.append(t(cx + 22, cy - 12, n["label"], 11, "start", italic=True, fill=stroke))
        else:
            lines = wrap(n["label"], 24)
            out.append(f"<rect x='{cx-w/2:.1f}' y='{cy-h/2:.1f}' width='{w:.1f}' height='{h:.1f}' rx='12' "
                       f"fill='{PANEL}' stroke='{stroke}' stroke-width='{sw}'/>")
            for i, line in enumerate(lines):
                out.append(t(cx, cy - h / 2 + 19 + i * 15, line, 12))
        if n.get("gone"):
            out.append(gone_mark(cx - w / 2, cy - h / 2, w, h))
    body = "".join(out)
    if spec.get("legend"):
        body += legend(8, height - 22)
    return svg_doc(width, height, body, spec["title"], spec.get("desc", spec["title"]))


# ---------------------------------------------------------------- sequence

def sequence(spec):
    """spec: lifelines [dict(id, name, stereo, actor, created, hl)], events [tuple]."""
    lls = spec["lifelines"]
    col_w = spec.get("col_w", 175)
    x0 = 70
    xs = {l["id"]: x0 + i * col_w for i, l in enumerate(lls)}
    head_y = 20
    y = 104
    out_msgs, frags, stack_f, acts, notes = [], [], [], [], []
    created_y = {}
    # Activation bars: view and controller stay active for a whole request (until a 'gap');
    # other objects are active from an incoming call until they return.
    union = {l["id"] for l in lls if l.get("stereo") in ("view", "controller")}
    open_acts = {}

    def touch(lid, yy):
        if lid in open_acts:
            open_acts[lid][1] = max(open_acts[lid][1], yy)

    def close(lid):
        if lid in open_acts:
            ya, yb = open_acts.pop(lid)
            acts.append((lid, ya, yb + 8, 0))

    pending = None   # created object whose short activation ends unless it is used next
    prev_kind = None
    for ev in spec["events"]:
        kind = ev[0]
        last_kind, prev_kind = prev_kind, kind   # last_kind: the previous event's kind
        hl = ev[-1] == "hl" if isinstance(ev[-1], str) else False
        if pending and not (kind in ("m", "r", "c") and pending in ev[1:3]) and kind != "n":
            close(pending)
        if kind != "n":
            pending = None
        if kind in ("m", "r", "c"):
            _, src, dst, label = ev[:4]
            if kind == "c":
                y += 14 + (10 if last_kind == "n" else 0)
                created_y[dst] = y
                pending = dst
            out_msgs.append((kind, src, dst, label, y, hl))
            touch(src, y)
            if kind in ("m", "c"):
                if dst not in open_acts:
                    start = y + 15 if kind == "c" else y
                    open_acts[dst] = [start, start]
                touch(dst, y)
            else:
                touch(dst, y)
                if src not in union:
                    close(src)
            y += 40 if kind == "c" else 34
        elif kind == "n":
            _, lid, text = ev[:3]
            lines = []
            for part in text.split("\n"):
                lines += wrap(part, 46)
            h = 10 + 14 * len(lines)
            notes.append((lid, y - 8, lines, hl))
            y += h + 6
        elif kind == "frag":
            _, op, guard, lfrom, lto = ev[:5]
            stack_f.append(dict(op=op, guards=[(y, guard)], lfrom=lfrom, lto=lto,
                                y=y - 14, depth=len(stack_f), hl=hl))
            y += 40
        elif kind == "else":
            stack_f[-1]["guards"].append((y, ev[1]))
            y += 34
        elif kind == "end":
            f = stack_f.pop()
            f["y2"] = y - 8
            frags.append(f)
            y += 14
        elif kind == "gap":
            for lid in list(open_acts):
                close(lid)
            y += ev[1]
    end_y = y + 10
    for lid in list(open_acts):
        close(lid)
    width = x0 + col_w * (len(lls) - 1) + max(150, col_w)
    height = end_y + 30
    out, late = [], []
    # fragments (drawn first, behind); guard text is drawn last so bars do not hide it
    for f in sorted(frags, key=lambda f: f["depth"]):
        pad = 62 - f["depth"] * 8
        xa = xs[f["lfrom"]] - pad
        xb = xs[f["lto"]] + pad
        stroke = HL if f["hl"] else INK
        out.append(f"<rect x='{xa:.1f}' y='{f['y']:.1f}' width='{xb-xa:.1f}' height='{f['y2']-f['y']:.1f}' "
                   f"fill='none' stroke='{stroke}' stroke-width='{2 if f['hl'] else 1.1}'/>")
        tw = text_width(f["op"]) + 16
        # the tag goes on top, so activation bars of nested frames never hide it
        late.append(f"<path d='M{xa},{f['y']} h{tw} v12 l-7,7 h-{tw-7} z' fill='{LANE_HEAD}' stroke='{stroke}' stroke-width='1.1'/>")
        late.append(t(xa + 6, f["y"] + 14, f["op"], 12, "start", "bold"))
        for i, (gy, guard) in enumerate(f["guards"]):
            if i > 0:
                out.append(f"<line x1='{xa}' y1='{gy-14}' x2='{xb}' y2='{gy-14}' stroke='{stroke}' stroke-dasharray='6 4'/>")
            late.append(bt(xa + (tw + 8 if i == 0 else 8), gy + 4, f"[{guard}]", 11, "start", italic=True, fill=stroke))
    # lifelines
    for l in lls:
        x = xs[l["id"]]
        top = created_y.get(l["id"], head_y + 30) if l.get("created") else head_y
        stroke = HL if l.get("hl") else INK
        sw = 2.5 if l.get("hl") else 1.2
        if l.get("actor"):
            out.append(f"<circle cx='{x}' cy='{top+8}' r='7' fill='none' stroke='{stroke}' stroke-width='{sw}'/>"
                       f"<path d='M{x},{top+15} v16 M{x-11},{top+21} h22 M{x},{top+31} l-9,13 M{x},{top+31} l9,13' "
                       f"stroke='{stroke}' stroke-width='{sw}' fill='none'/>")
            out.append(t(x, top + 58, l["name"], 12, weight="bold"))
            line_top = top + 64
        else:
            name = l["name"]
            stereo = l.get("stereo")
            w = max(text_width(name) + 20, text_width(stereo or "") + 20, 110)
            h = 42 if stereo else 30
            by = top - h / 2 if l.get("created") else top
            out.append(f"<rect x='{x-w/2:.1f}' y='{by:.1f}' width='{w:.1f}' height='{h}' fill='{PANEL}' stroke='{stroke}' stroke-width='{sw}'/>")
            if stereo:
                out.append(t(x, by + 15, f"«{stereo}»", 11))
                out.append(t(x, by + 32, name, 12) + f"<line x1='{x-text_width(name)/2:.1f}' y1='{by+34:.1f}' x2='{x+text_width(name)/2:.1f}' y2='{by+34:.1f}' stroke='{INK}'/>")
            else:
                out.append(t(x, by + 20, name, 12) + f"<line x1='{x-text_width(name)/2:.1f}' y1='{by+22:.1f}' x2='{x+text_width(name)/2:.1f}' y2='{by+22:.1f}' stroke='{INK}'/>")
            line_top = by + h
        out.append(f"<line x1='{x}' y1='{line_top:.1f}' x2='{x}' y2='{end_y}' stroke='{INK}' stroke-dasharray='5 4' stroke-width='1'/>")
    # activations
    for lid, ya, yb, depth in acts:
        if any(l["id"] == lid and l.get("actor") for l in lls):
            continue
        x = xs[lid] + depth * 6
        out.append(f"<rect x='{x-5}' y='{ya:.1f}' width='10' height='{max(yb-ya, 10):.1f}' fill='{PAPER}' stroke='{INK}' stroke-width='1'/>")
    # messages
    for kind, src, dst, label, my, hl in out_msgs:
        xa, xb = xs[src], xs[dst]
        direction = 1 if xb > xa else -1
        xa += 5 * direction
        if kind == "c":
            name = next(l["name"] for l in lls if l["id"] == dst)
            xb -= direction * (max(text_width(name) + 20, 110) / 2)
        else:
            xb -= 5 * direction
        color = HL if hl else INK
        dash = " stroke-dasharray='6 4'" if kind == "r" else ""
        marker = "open" if kind == "r" else "filled"
        out.append(f"<line x1='{xa:.1f}' y1='{my}' x2='{xb:.1f}' y2='{my}' stroke='{color}' stroke-width='{2 if hl else 1.2}'{dash} marker-end='url(#{marker})'/>")
        if kind == "c":
            out.append(bt(xa + 8 * direction, my - 19, label, 11.5, "start" if direction > 0 else "end",
                          fill=color, weight="bold" if hl else "normal"))
        else:
            out.append(bt((xa + xb) / 2, my - 6, label, 11.5, fill=color, weight="bold" if hl else "normal"))
    out += late
    # notes
    for lid, ny, lines, hl in notes:
        x = xs[lid] + 12
        w = max(text_width(s, 11) for s in lines) + 18
        h = 6 + 14 * len(lines)
        stroke = HL if hl else INK
        out.append(f"<path d='M{x},{ny} h{w-10} l10,10 v{h-10} h-{w} z' fill='#FFF6D6' stroke='{stroke}' stroke-width='{1.8 if hl else 1}'/>")
        for i, s in enumerate(lines):
            out.append(t(x + 8, ny + 15 + i * 14, s, 11, "start"))
    body = "".join(out)
    if spec.get("legend"):
        body += legend(8, height - 14)
    return svg_doc(width, height, body, spec["title"], spec.get("desc", spec["title"]))


# ---------------------------------------------------------------- class

def class_diagram(spec, upto=None, focus=None):
    """spec: classes {id: dict(name, stereo, x, y, w, attrs, ops, since)}, rels [dict(type, from, to, since, via)].

    Items carry 'since' (step number). upto hides later items; focus highlights items with since == focus.
    """
    def visible(item):
        return upto is None or item.get("since", 0) <= upto

    def is_new(item):
        return focus is not None and item.get("since", 0) == focus or item.get("hl")

    boxes = {}
    out = []
    for cid, c in spec["classes"].items():
        if not visible(c):
            continue
        attrs = [a for a in c.get("attrs", []) if visible(a if isinstance(a, dict) else {})]
        ops = [o for o in c.get("ops", []) if visible(o if isinstance(o, dict) else {})]
        head_h = 36 if c.get("stereo") else 24
        h = head_h + 8 + 15 * max(len(attrs), 1) + 8 + 15 * max(len(ops), 1)
        boxes[cid] = (c["x"], c["y"], c["w"], h, c, attrs, ops, head_h)
    max_x = max(b[0] + b[2] for b in boxes.values()) + 30
    max_y = max(b[1] + b[3] for b in boxes.values()) + 50

    def edge_point(b, px, py):
        x, y, w, h = b[:4]
        cx, cy = x + w / 2, y + h / 2
        dx, dy = px - cx, py - cy
        if dx == 0 and dy == 0:
            return cx, cy
        sx = (w / 2) / abs(dx) if dx else 1e9
        sy = (h / 2) / abs(dy) if dy else 1e9
        s = min(sx, sy)
        return cx + dx * s, cy + dy * s

    for r in spec["rels"]:
        if not visible(r) or r["from"] not in boxes or r["to"] not in boxes:
            continue
        a, b = boxes[r["from"]], boxes[r["to"]]
        color = HL if is_new(r) else INK
        sw = 2.2 if is_new(r) else 1.2
        via = r.get("via", [])
        first = via[0] if via else (b[0] + b[2] / 2 + r.get("tdx", 0), b[1] + b[3] / 2 + r.get("tdy", 0))
        last = via[-1] if via else (a[0] + a[2] / 2 + r.get("sdx", 0), a[1] + a[3] / 2 + r.get("sdy", 0))
        start = edge_point(a, *first) if not r.get("sp") else r["sp"]
        if r.get("sdx") or r.get("sdy"):
            start = edge_point(a, a[0] + a[2] / 2 + r.get("sdx", 0), a[1] + a[3] / 2 + r.get("sdy", 0)) if not via else start
        end = edge_point(b, *last) if not r.get("ep") else r["ep"]
        pts = [start] + list(via) + [end]
        path = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        marker = "hollow" if r["type"] == "gen" else "open"
        out.append(f"<polyline points='{path}' fill='none' stroke='{color}' stroke-width='{sw}' marker-end='url(#{marker})'/>")

    for cid, (x, y, w, h, c, attrs, ops, head_h) in boxes.items():
        new_box = is_new(c)
        stroke = HL if new_box else INK
        sw = 2.6 if new_box else 1.2
        out.append(f"<rect x='{x}' y='{y}' width='{w}' height='{h}' fill='{PANEL}' stroke='{stroke}' stroke-width='{sw}'/>")
        ty = y + 16
        if c.get("stereo"):
            out.append(t(x + w / 2, ty, f"«{c['stereo']}»", 11))
            ty += 14
        out.append(t(x + w / 2, ty + 2, c["name"], 12.5, weight="bold"))
        y_line = y + head_h + 2
        out.append(f"<line x1='{x}' y1='{y_line}' x2='{x+w}' y2='{y_line}' stroke='{stroke}'/>")
        cy = y_line + 15
        for a in attrs:
            label, item = (a["t"], a) if isinstance(a, dict) else (a, {})
            out.append(t(x + 6, cy, label, 11.5, "start", fill=HL if is_new(item) and not new_box else INK,
                         weight="bold" if is_new(item) and not new_box else "normal"))
            cy += 15
        if not attrs:
            cy += 15
        y_line = cy - 7
        out.append(f"<line x1='{x}' y1='{y_line}' x2='{x+w}' y2='{y_line}' stroke='{stroke}'/>")
        cy = y_line + 16
        for o in ops:
            label, item = (o["t"], o) if isinstance(o, dict) else (o, {})
            out.append(t(x + 6, cy, label, 11.5, "start", fill=HL if is_new(item) and not new_box else INK,
                         weight="bold" if is_new(item) and not new_box else "normal"))
            cy += 15
        if c.get("gone"):
            out.append(gone_mark(x, y, w, h))
    body = "".join(out)
    if focus is not None or spec.get("legend"):
        body += legend(10, max_y - 18)
    return svg_doc(max_x, max_y, body, spec["title"], spec.get("desc", spec["title"]))

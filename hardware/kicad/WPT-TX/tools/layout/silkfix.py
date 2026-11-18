#!/usr/bin/env python3
"""Place the reference designators of the parts added in the STM32 redesign so that they can be read.

usage: silkfix.py BOARD_IN BOARD_OUT ADDED_REFS.json [--also REF,REF] [--hide-if-stuck REF,REF]

For every listed footprint whose reference is visible, the text is set to 0.8 x 0.7 mm (0.15 mm stroke) and moved to the
nearest place beside the part where it covers no pad, no hole, no component body, no other silkscreen and stays 0.6 mm
inside the board edge. Dense groups are served first. A reference that finds no place within 4.5 mm is looked for
up to 8 mm away; if there is none either, it stays where it was and is reported. The space a text needs is taken from its glyphs (KiCad's own text box is about twice as high). Legacy texts are obstacles and are not moved.
"""
import json
import math
import sys

import pcbnew

MM = 1e6
src, dst, reflist = sys.argv[1:4]
refs = set(json.load(open(reflist)))
if '--also' in sys.argv:
    refs |= set(sys.argv[sys.argv.index('--also') + 1].split(','))
hide = set(sys.argv[sys.argv.index('--hide-if-stuck') + 1].split(',')) if '--hide-if-stuck' in sys.argv else set()
b = pcbnew.LoadBoard(src)
H, Wd, TH = 0.8, 0.7, 0.15
edge = b.GetBoardEdgesBoundingBox()
EX0, EY0, EX1, EY1 = edge.GetLeft() / MM + 0.6, edge.GetTop() / MM + 0.6, edge.GetRight() / MM - 0.6, edge.GetBottom() / MM - 0.6


def box(bb, g=0.0):
    return (bb.GetLeft() / MM - g, bb.GetTop() / MM - g, bb.GetRight() / MM + g, bb.GetBottom() / MM + g)


def hit(a, c):
    return a[0] < c[2] and c[0] < a[2] and a[1] < c[3] and c[1] < a[3]


SIDE = {'F': (pcbnew.F_SilkS, pcbnew.F_Mask, pcbnew.F_Fab, pcbnew.F_CrtYd), 'B': (pcbnew.B_SilkS, pcbnew.B_Mask, pcbnew.B_Fab, pcbnew.B_CrtYd)}
report = []
for side, (silk, mask, fab, crt) in SIDE.items():
    obst = []                                             # (x0, y0, x1, y1, owner)
    body = {}
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        onside = (fp.GetLayer() == pcbnew.F_Cu) == (side == 'F')
        for pad in fp.Pads():
            if pad.IsOnLayer(mask) or pad.GetDrillSize().x > 0:
                obst.append(box(pad.GetBoundingBox(), 0.12) + (ref,))
        bb = None
        for g in fp.GraphicalItems():
            if g.GetLayer() == silk and g.Type() != pcbnew.PCB_FIELD_T:
                obst.append(box(g.GetBoundingBox(), 0.1) + (ref,))
            if g.GetLayer() == fab and onside and g.Type() == pcbnew.PCB_SHAPE_T:
                q = box(g.GetBoundingBox())
                bb = q if bb is None else (min(bb[0], q[0]), min(bb[1], q[1]), max(bb[2], q[2]), max(bb[3], q[3]))
        if onside:
            if bb is None:
                bb = box(fp.GetBoundingBox(False, False))
            body[ref] = bb
            obst.append((bb[0] - 0.1, bb[1] - 0.1, bb[2] + 0.1, bb[3] + 0.1, ref))
        for f in fp.GetFields():
            if f.IsVisible() and f.GetLayer() == silk and not (f.IsReference() and ref in refs and onside):
                obst.append(box(f.GetBoundingBox(), 0.1) + (ref,))
    for d in b.GetDrawings():
        if d.GetLayer() == silk:
            obst.append(box(d.GetBoundingBox(), 0.1) + ('board',))
    todo = [fp for fp in b.GetFootprints() if fp.GetReference() in refs and fp.Reference().IsVisible()
            and (fp.GetLayer() == pcbnew.F_Cu) == (side == 'F')]

    def crowd(fp):
        c = fp.GetPosition()
        return sum(1 for o in body.values() if math.hypot((o[0] + o[2]) / 2 - c.x / MM, (o[1] + o[3]) / 2 - c.y / MM) < 3.0)

    todo.sort(key=lambda fp: (-crowd(fp), fp.GetReference()))
    for fp in todo:
        t = fp.Reference()
        t.SetLayer(silk)
        t.SetTextSize(pcbnew.VECTOR2I(int(Wd * MM), int(H * MM)))
        t.SetTextThickness(int(TH * MM))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        t.SetKeepUpright(True)
        bx = body[fp.GetReference()]
        cx, cy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
        hw, hh = (bx[2] - bx[0]) / 2, (bx[3] - bx[1]) / 2
        old = (t.GetPosition(), t.GetTextAngleDegrees())
        best = None
        n = len(fp.GetReference())
        gw, gh = (n * Wd * 0.9 + TH) / 2 + 0.05, (H + TH) / 2 + 0.05          # half extents of the glyphs themselves
        for ang in (0.0, 90.0):
            tw, th = (gw, gh) if ang == 0.0 else (gh, gw)
            # along a long body (pin headers) the text may sit anywhere beside it
            sx = [i * 0.4 * sg for i in range(0, int(max(hw - tw, 0.0) / 0.4) + 7) for sg in (1, -1)]
            sy = [i * 0.4 * sg for i in range(0, int(max(hh - th, 0.0) / 0.4) + 7) for sg in (1, -1)]
            for d in (0.15, 0.35, 0.6, 0.9, 1.2, 1.6, 2.0, 2.5, 3.0, 3.7, 4.5, 5.5, 6.5, 8.0):
                if d > 4.5 and best is not None:
                    break
                cands = [(cx + hw + d + tw, cy + s, s) for s in sy] + [(cx - hw - d - tw, cy + s, s) for s in sy]
                cands += [(cx + s, cy - hh - d - th, s) for s in sx] + [(cx + s, cy + hh + d + th, s) for s in sx]
                for px, py, s in cands:
                    r = (px - tw, py - th, px + tw, py + th)
                    if r[0] < EX0 or r[1] < EY0 or r[2] > EX1 or r[3] > EY1:
                        continue
                    cost = d + 0.25 * abs(s) + (0.4 if ang else 0.0)
                    if best is not None and cost >= best[0]:
                        continue
                    if any(hit(r, o) for o in obst):
                        continue
                    best = (cost, px, py, ang, r)
        if best is None:
            t.SetPosition(old[0])
            t.SetTextAngleDegrees(old[1])
            report.append(fp.GetReference())
            if fp.GetReference() in hide:
                t.SetVisible(False)            # stays on the fabrication layer drawing
            else:
                obst.append(box(t.GetBoundingBox(), 0.1) + (fp.GetReference(),))
            continue
        t.SetTextAngleDegrees(best[3])
        t.SetPosition(pcbnew.VECTOR2I(int(round(best[1] * MM)), int(round(best[2] * MM))))
        obst.append((best[4][0] - 0.1, best[4][1] - 0.1, best[4][2] + 0.1, best[4][3] + 0.1, fp.GetReference()))
    print(side, 'side:', len(todo), 'references placed')
print('no free place found for:', report)
pcbnew.SaveBoard(dst, b)

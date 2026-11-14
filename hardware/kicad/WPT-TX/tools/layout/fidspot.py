#!/usr/bin/env python3
"""Is a spot free for a fiducial? usage: fidspot.py BOARD x,y[,F|B] ...   (prints the nearest object of each kind)"""
import math
import sys
import pcbnew
MM = 1e-6
b = pcbnew.LoadBoard(sys.argv[1])


def dseg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def rdist(px, py, bb):
    x0, y0, x1, y1 = bb.GetLeft() * MM, bb.GetTop() * MM, bb.GetRight() * MM, bb.GetBottom() * MM
    return math.hypot(max(x0 - px, 0, px - x1), max(y0 - py, 0, py - y1))


edge = b.GetBoardEdgesBoundingBox()
for a in sys.argv[2:]:
    q = a.split(',')
    x, y = float(q[0]), float(q[1])
    side = q[2] if len(q) > 2 else 'F'
    cu = pcbnew.F_Cu if side == 'F' else pcbnew.B_Cu
    silk = pcbnew.F_SilkS if side == 'F' else pcbnew.B_SilkS
    near = {}

    def note(kind, d, what):
        if kind not in near or d < near[kind][0]:
            near[kind] = (d, what)
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            note('via', math.hypot(t.GetPosition().x * MM - x, t.GetPosition().y * MM - y) - 0.3, t.GetNetname())
        elif t.GetLayer() == cu:
            s, e = t.GetStart(), t.GetEnd()
            note('track', dseg(x, y, s.x * MM, s.y * MM, e.x * MM, e.y * MM) - t.GetWidth() * MM / 2, t.GetNetname())
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.IsOnLayer(cu):
                note('pad', rdist(x, y, p.GetBoundingBox()), f.GetReference() + '.' + p.GetNumber())
        cy = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
        if cy.OutlineCount() and (f.IsFlipped() == (side == 'B')):
            note('courtyard', rdist(x, y, cy.BBox()), f.GetReference())
        for g in f.GraphicalItems():
            if g.GetLayer() == silk:
                note('silk', rdist(x, y, g.GetBoundingBox()), f.GetReference())
        for fld in (f.Reference(), f.Value()):
            if fld.IsVisible() and fld.GetLayer() == silk:
                note('silk', rdist(x, y, fld.GetBoundingBox()), f.GetReference() + ' text')
    for d in b.GetDrawings():
        if d.GetLayer() == silk:
            note('silk', rdist(x, y, d.GetBoundingBox()), 'board text/graphic')
    ed = min(x - edge.GetLeft() * MM, y - edge.GetTop() * MM, edge.GetRight() * MM - x, edge.GetBottom() * MM - y)
    print('(%.2f, %.2f) %s  edge %.2f  ' % (x, y, side, ed) + '  '.join('%s %.2f (%s)' % (k, v[0], v[1].split('/')[-1]) for k, v in sorted(near.items())))

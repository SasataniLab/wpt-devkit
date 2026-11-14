#!/usr/bin/env python3
"""Assembly clearances that DRC does not look at. usage: nearchk.py BOARD

  1 surface-mount pads on the solder side of a through-hole part: distance from every SMD pad to every through-hole
    pad of another part on the same side as the SMD pad (the THT part is soldered there), listed below 1.0 mm
  2 parts close to the board edge: courtyard to the outline, listed below 0.5 mm (connectors that overhang on purpose show up too)
  3 body-to-body distance of neighbouring parts on the same side taken from the courtyards, listed below 0.15 mm
"""
import math
import sys

import pcbnew

MM = 1e-6
b = pcbnew.LoadBoard(sys.argv[1])
fps = list(b.GetFootprints())


def rect(p):
    bb = p.GetBoundingBox()
    return bb.GetLeft() * MM, bb.GetTop() * MM, bb.GetRight() * MM, bb.GetBottom() * MM


def rdist(a, c):
    dx = max(a[0] - c[2], c[0] - a[2], 0)
    dy = max(a[1] - c[3], c[1] - a[3], 0)
    return math.hypot(dx, dy)


print('== 1 SMD pads beside the solder joints of through-hole parts (< 1.0 mm)')
tht = []
for f in fps:
    for p in f.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            tht.append((f, p, rect(p)))
seen = {}
for f in fps:
    for p in f.Pads():
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
        side_b = f.IsFlipped()
        r = rect(p)
        for g, q, rq in tht:
            if g is f or g.IsFlipped() == side_b and not g.GetReference().startswith('REF'):
                # the THT part sits on the same side as the SMD part: its joints are on the other side -> no conflict
                continue
            d = rdist(r, rq)
            if d < 1.0:
                k = (f.GetReference(), g.GetReference())
                if k not in seen or d < seen[k][0]:
                    seen[k] = (d, p.GetNumber(), q.GetNumber())
for (a, c), (d, pn, qn) in sorted(seen.items(), key=lambda kv: kv[1][0]):
    print('   %-6s pad %-3s is %.2f mm from the joint of %s.%s' % (a, pn, d, c, qn))
print('== 2 courtyard to board edge (< 0.5 mm)')
edge = b.GetBoardEdgesBoundingBox()
ex0, ey0, ex1, ey1 = edge.GetLeft() * MM, edge.GetTop() * MM, edge.GetRight() * MM, edge.GetBottom() * MM
for f in sorted(fps, key=lambda f: f.GetReference()):
    cy = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    if not cy.OutlineCount():
        continue
    bb = cy.BBox()
    x0, y0, x1, y1 = bb.GetLeft() * MM, bb.GetTop() * MM, bb.GetRight() * MM, bb.GetBottom() * MM
    m = min(x0 - ex0, y0 - ey0, ex1 - x1, ey1 - y1)
    if m < 0.5:
        print('   %-7s %-22s courtyard %.2f mm from the outline box (negative = overhangs)' % (f.GetReference(), f.GetValue()[:22], m))
print('== 3 courtyards closer than 0.15 mm (same side)')
cys = []
for f in fps:
    cy = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    if cy.OutlineCount():
        bb = cy.BBox()
        cys.append((f, (bb.GetLeft() * MM, bb.GetTop() * MM, bb.GetRight() * MM, bb.GetBottom() * MM)))
for i, (f, r) in enumerate(cys):
    for g, q in cys[i + 1:]:
        if f.IsFlipped() != g.IsFlipped():
            continue
        d = rdist(r, q)
        if d < 0.15:
            print('   %-7s %-7s %.2f mm' % (f.GetReference(), g.GetReference(), d))

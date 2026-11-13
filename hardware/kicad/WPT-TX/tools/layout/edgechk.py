#!/usr/bin/env python3
"""Tracks whose copper comes closer than D mm to the board outline. usage: edgechk.py BOARD [D=1.0]"""
import sys
import pcbnew
MM = 1e-6
b = pcbnew.LoadBoard(sys.argv[1])
D = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
bb = b.GetBoardEdgesBoundingBox()
x0, y0, x1, y1 = bb.GetLeft() * MM, bb.GetTop() * MM, bb.GetRight() * MM, bb.GetBottom() * MM
from collections import defaultdict
out = defaultdict(lambda: [0.0, 9.9, None])
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        continue
    a, e = t.GetStart(), t.GetEnd()
    w = t.GetWidth() * MM / 2
    n = 20
    L = t.GetLength() * MM
    for i in range(n + 1):
        x = (a.x + (e.x - a.x) * i / n) * MM
        y = (a.y + (e.y - a.y) * i / n) * MM
        d = min(x - x0, x1 - x, y - y0, y1 - y) - w
        if d < D:
            k = (t.GetNetname().split('/')[-1], b.GetLayerName(t.GetLayer()))
            out[k][0] += L / (n + 1)
            if d < out[k][1]:
                out[k][1] = d
                out[k][2] = (round(x, 2), round(y, 2))
for k, v in sorted(out.items(), key=lambda kv: kv[1][1]):
    print('%-22s %-5s %5.1f mm within %.1f mm of the edge, closest %.2f mm at %s' % (k[0], k[1], v[0], D, v[1], v[2]))

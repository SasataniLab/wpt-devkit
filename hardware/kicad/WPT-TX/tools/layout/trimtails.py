#!/usr/bin/env python3
"""Shorten tracks whose free end sticks out beyond the point where the rest of the net joins them.

usage: trimtails.py BOARD
"""
import math
import re
import sys

import pcbnew

import router as R

MM = 1e6
path = sys.argv[1]
txt = R.run_drc(path, path.replace('.kicad_pcb', '_tails.rpt'))
want = []
for blk in re.split(r'\n(?=\[)', txt):
    if not blk.startswith('[track_dangling]'):
        continue
    m = R.ITEM.search(blk)
    x, y, desc = float(m.group(1)), float(m.group(2)), m.group(3)
    want.append((re.search(r'\[([^\]]*)\]', desc).group(1), x, y, re.search(r' on (\S+\.Cu)', desc).group(1), float(re.search(r'length ([\d.]+) mm', desc).group(1))))
b = pcbnew.LoadBoard(path)
P = lambda v: (v.x / MM, v.y / MM)
tracks = [t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA']
vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
n = 0
for net, x, y, lay, ln in want:
    for t in tracks:
        if t.GetNetname() != net or b.GetLayerName(t.GetLayer()) != lay or abs(t.GetLength() / MM - ln) > 0.002:
            continue
        a, e = P(t.GetStart()), P(t.GetEnd())
        if math.dist(a, (x, y)) > 0.003 and math.dist(e, (x, y)) > 0.003:
            continue
        # anchors of the same net that touch this segment
        pts = []
        for o in tracks:
            if o is t or o.GetNetname() != net or o.GetLayer() != t.GetLayer():
                continue
            pts += [P(o.GetStart()), P(o.GetEnd())]
        pts += [P(v.GetPosition()) for v in vias if v.GetNetname() == net]
        for fp in b.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() == net:
                    pts.append(P(pad.GetPosition()))
        L = math.dist(a, e)
        ux, uy = (e[0] - a[0]) / L, (e[1] - a[1]) / L
        s = []
        for p in pts:
            tt = (p[0] - a[0]) * ux + (p[1] - a[1]) * uy
            d = abs((p[0] - a[0]) * uy - (p[1] - a[1]) * ux)
            if d < 0.03 and -0.03 <= tt <= L + 0.03:
                s.append(max(0.0, min(L, tt)))
        if len(s) < 2:
            continue
        lo, hi = min(s), max(s)
        if lo > 0.02:
            t.SetStart(pcbnew.VECTOR2I(int(round((a[0] + ux * lo) * MM)), int(round((a[1] + uy * lo) * MM))))
            n += 1
        if hi < L - 0.02:
            t.SetEnd(pcbnew.VECTOR2I(int(round((a[0] + ux * hi) * MM)), int(round((a[1] + uy * hi) * MM))))
            n += 1
        print('  ', net.split('/')[-1], lay, 'was', a, e, 'kept part', round(lo, 3), '..', round(hi, 3), 'of', round(L, 3))
pcbnew.SaveBoard(path, b)
print('track ends trimmed:', n)

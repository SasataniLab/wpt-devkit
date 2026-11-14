#!/usr/bin/env python3
"""List the segments that are not on 0 / 45 / 90 degrees and are not copper of the base board. usage: off45.py BOARD BASE"""
import math
import sys
import pcbnew
MM = 1e6
def keys(p, full=False):
    b = pcbnew.LoadBoard(p)
    out = []
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_VIA':
            a, e = (round(t.GetStart().x / MM, 3), round(t.GetStart().y / MM, 3)), (round(t.GetEnd().x / MM, 3), round(t.GetEnd().y / MM, 3))
            out.append((b.GetLayerName(t.GetLayer()),) + tuple(sorted([a, e])) + ((t.GetNetname(), t.GetWidth() / MM) if full else ()))
    return out
base = set(keys(sys.argv[2]))
n = tot = 0
for layer, a, e, net, w in sorted(keys(sys.argv[1], True), key=lambda k: (k[3], k[0], k[1])):
    if (layer, a, e) in base:
        continue
    tot += 1
    dx, dy = abs(a[0] - e[0]), abs(a[1] - e[1])
    if not (dx < 2e-3 or dy < 2e-3 or abs(dx - dy) < 2e-3):
        n += 1
        print('%-22s %-5s (%.3f,%.3f)-(%.3f,%.3f) w%.2f  len %.2f  angle %.1f' % (net.split('/')[-1], layer, a[0], a[1], e[0], e[1], w, math.hypot(dx, dy), math.degrees(math.atan2(dy, dx))))
print('%d of %d segments (not counting base-board copper) are off 0/45/90 degrees' % (n, tot))

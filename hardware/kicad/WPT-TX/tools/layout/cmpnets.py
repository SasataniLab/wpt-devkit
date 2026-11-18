#!/usr/bin/env python3
"""Compare length / vias / inner-layer use of every net between two boards. usage: cmpnets.py OLD NEW"""
import sys
from collections import defaultdict
import pcbnew
def stat(p):
    b = pcbnew.LoadBoard(p)
    L = defaultdict(lambda: [0.0, 0, 0.0])
    for t in b.GetTracks():
        n = t.GetNetname().split('/')[-1]
        if t.Type() == pcbnew.PCB_VIA_T:
            L[n][1] += 1
        else:
            L[n][0] += t.GetLength() / 1e6
            if b.GetLayerName(t.GetLayer()) == 'In2.Cu':
                L[n][2] += t.GetLength() / 1e6
    return L
a, b = stat(sys.argv[1]), stat(sys.argv[2])
tot = [0.0, 0.0, 0, 0]
for n in sorted(set(a) | set(b)):
    x, y = a.get(n, [0, 0, 0]), b.get(n, [0, 0, 0])
    if abs(x[0] - y[0]) > 0.3 or x[1] != y[1]:
        print('%-22s %6.1f mm / %d vias / In2 %4.1f  ->  %6.1f mm / %d vias / In2 %4.1f' % (n, x[0], x[1], x[2], y[0], y[1], y[2]))
        tot[0] += x[0]; tot[1] += y[0]; tot[2] += x[1]; tot[3] += y[1]
print('changed nets total: %.1f mm / %d vias -> %.1f mm / %d vias' % (tot[0], tot[2], tot[1], tot[3]))

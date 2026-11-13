#!/usr/bin/env python3
"""Flood from two points of a net inside one window and report whether the two regions meet. usage: reach2.py BOARD REG NET x1 y1 L1 x2 y2 L2 OUT.png"""
import json
import sys
from collections import deque

import numpy as np

import router as R

R.DEFAULT_CORRIDORS = ()
path, regfile, name = sys.argv[1:4]
p1 = (float(sys.argv[4]), float(sys.argv[5]), sys.argv[6])
p2 = (float(sys.argv[7]), float(sys.argv[8]), sys.argv[9])
out = sys.argv[10]
tup = lambda q: tuple(tuple(v) if isinstance(v, list) else v for v in q)
REG = {n: [tup(k) for k in ks] for n, ks in json.load(open(regfile)).items()}
r = R.Router(path, reg=REG, protected=set())
net = [n for n in r.nets if n.split('/')[-1] == name][0]
m = 6.0
wx0, wy0 = min(p1[0], p2[0]) - m, max(R.Y0 + 0.5, min(p1[1], p2[1]) - m)
wx1, wy1 = max(p1[0], p2[0]) + m, max(p1[1], p2[1]) + m
ix0, iy0 = int((wx0 - R.X0) / R.RES), int((wy0 - R.Y0) / R.RES)
ix1, iy1 = int((wx1 - R.X0) / R.RES), int((wy1 - R.Y0) / R.RES)
L = ['F.Cu', 'B.Cu']
res = {}
for soft in (False, True):
    free, via_ok, own = r.maps(net, (ix0, iy0, ix1, iy1), 0.2, soft=soft)
    ok = [free[l] | own[l] for l in L]
    hh, ww = via_ok.shape
    regs = []
    for (x, y, layer) in (p1, p2):
        cx, cy = int(round((x - R.X0) / R.RES)) - ix0, int(round((y - R.Y0) / R.RES)) - iy0
        li = L.index(layer)
        seen = [np.zeros((hh, ww), bool) for _ in L]
        q = deque()
        for dy in range(-5, 6):
            for dx in range(-5, 6):
                yy, xx = cy + dy, cx + dx
                if 0 <= yy < hh and 0 <= xx < ww and ok[li][yy, xx] and not seen[li][yy, xx]:
                    seen[li][yy, xx] = True
                    q.append((li, yy, xx))
        while q:
            l, yy, xx = q.popleft()
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                y2, x2 = yy + dy, xx + dx
                if 0 <= y2 < hh and 0 <= x2 < ww and ok[l][y2, x2] and not seen[l][y2, x2]:
                    seen[l][y2, x2] = True
                    q.append((l, y2, x2))
            if via_ok[yy, xx]:
                o = 1 - l
                if ok[o][yy, xx] and not seen[o][yy, xx]:
                    seen[o][yy, xx] = True
                    q.append((o, yy, xx))
        regs.append(seen)
    meet = sum(int((regs[0][k] & regs[1][k]).sum()) for k in range(2))
    print('soft' if soft else 'hard', 'cells from A', sum(int(s.sum()) for s in regs[0]), 'from B', sum(int(s.sum()) for s in regs[1]), 'common', meet)
    res[soft] = (regs, ok, via_ok)
# picture of the hard case: A region red, B region blue, per layer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
regs, ok, via_ok = res[False]
fig, axs = plt.subplots(1, 2, figsize=(16, 14))
for k in range(2):
    img = np.zeros(ok[k].shape + (3,))
    img[~ok[k]] = (0.25, 0.25, 0.25)
    img[regs[0][k]] = (0.9, 0.3, 0.3)
    img[regs[1][k]] = (0.3, 0.5, 1.0)
    axs[k].imshow(img, extent=(wx0, wx1, wy1, wy0), interpolation='nearest')
    axs[k].set_title(L[k] + ' (grey = blocked, red = reachable from the MCU pin, blue = from the J301 side)')
fig.savefig(out, dpi=70)

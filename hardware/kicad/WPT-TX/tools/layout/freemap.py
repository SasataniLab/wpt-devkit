#!/usr/bin/env python3
"""Where is board area free of parts on both sides? usage: freemap.py BOARD OUT.png [x0 y0 x1 y1]
White = no courtyard / pad of any part on either side (a through-hole part could go there), light = one side free."""
import sys
import numpy as np
import pcbnew
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1])
x0, y0, x1, y1 = (float(v) for v in sys.argv[3:7]) if len(sys.argv) > 6 else (150, 135, 220, 200)
RES = 0.1
W, H = int((x1 - x0) / RES), int((y1 - y0) / RES)
occ = {'F': np.zeros((H, W), bool), 'B': np.zeros((H, W), bool)}
def mark(a, bb, g=0.0):
    i0, j0 = max(0, int((bb[0] - g - x0) / RES)), max(0, int((bb[1] - g - y0) / RES))
    i1, j1 = min(W, int((bb[2] + g - x0) / RES) + 1), min(H, int((bb[3] + g - y0) / RES) + 1)
    if i1 > i0 and j1 > j0:
        a[j0:j1, i0:i1] = True
labels = []
for fp in b.GetFootprints():
    side = 'B' if fp.IsFlipped() else 'F'
    cy = fp.GetCourtyard(pcbnew.B_CrtYd if side == 'B' else pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False, False)
    q = (bb.GetLeft() / MM, bb.GetTop() / MM, bb.GetRight() / MM, bb.GetBottom() / MM)
    mark(occ[side], q)
    for p in fp.Pads():
        if p.GetDrillSize().x > 0:
            pb = p.GetBoundingBox()
            pq = (pb.GetLeft() / MM, pb.GetTop() / MM, pb.GetRight() / MM, pb.GetBottom() / MM)
            mark(occ['F'], pq, 0.3); mark(occ['B'], pq, 0.3)
    labels.append((fp.GetReference(), (q[0] + q[2]) / 2, (q[1] + q[3]) / 2, side))
img = np.ones((H, W, 3))
img[occ['F'] & ~occ['B']] = (1.0, 0.75, 0.75)
img[occ['B'] & ~occ['F']] = (0.75, 0.8, 1.0)
img[occ['F'] & occ['B']] = (0.6, 0.5, 0.7)
fig = plt.figure(figsize=(W / 55, H / 55), dpi=100)
ax = fig.add_axes([0.04, 0.04, 0.95, 0.95])
ax.imshow(img, extent=(x0, x1, y1, y0), interpolation='nearest')
for r, cx, cyy, s in labels:
    if x0 < cx < x1 and y0 < cyy < y1:
        ax.text(cx, cyy, r, fontsize=5, ha='center', va='center', color='#a00000' if s == 'F' else '#0000a0')
ax.set_xticks(np.arange(x0, x1 + 0.1, 5)); ax.set_yticks(np.arange(y0, y1 + 0.1, 5)); ax.grid(True, lw=0.3, color='#888')
ax.tick_params(labelsize=6)
fig.savefig(sys.argv[2], dpi=100)
free = ~occ['F'] & ~occ['B']
print('both sides free: %.0f mm2 of %.0f mm2' % (free.sum() * RES * RES, W * H * RES * RES))

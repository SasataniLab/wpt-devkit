#!/usr/bin/env python3
"""Leg-A switch-node divider made compact (same idea as leg B in phys1.py). usage: phys2.py BOARD_IN BOARD_OUT

R339 / C338 are turned so that their switch-node pads face the driver and their tap pads face R343 / R340;
R340 is turned so that its tap pad touches the tap. The tap node then spans about 1.2 x 1.3 mm.
"""
import shutil
import sys

import pcbnew

import router as R
from nego import rip_text

R.DEFAULT_CORRIDORS = ()
MM = 1e6
src, dst = sys.argv[1:3]
shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)
P = lambda v: (round(v.x / MM, 3), round(v.y / MM, 3))
T, VK = R.Router.tkey, R.Router.vkey
net = lambda s: [str(n) for n in b.GetNetsByName().asdict().keys() if str(n).split('/')[-1] == s][0]
kill = set()
for t in b.GetTracks():
    n = t.GetNetname()
    if t.GetClass() == 'PCB_VIA':
        c = P(t.GetPosition())
        if n == 'GND' and c == (193.2, 183.5):
            kill.add(VK(n, c))
    else:
        a, e = P(t.GetStart()), P(t.GetEnd())
        ln = b.GetLayerName(t.GetLayer())
        box = lambda p, x0, y0, x1, y1: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
        if ln == 'B.Cu' and n.split('/')[-1] == 'OutA' and box(a, 191.5, 179.3, 194.4, 183.8) and box(e, 191.5, 179.3, 194.4, 183.8):
            kill.add(T(n, ln, a, e))
        if ln == 'B.Cu' and n == 'GND' and box(a, 190.6, 180.8, 193.4, 183.7) and box(e, 190.6, 180.8, 193.4, 183.7):
            kill.add(T(n, ln, a, e))
pads = {}
for ref in ('R339', 'C338', 'R340'):
    fp = b.FindFootprintByReference(ref)
    fp.SetOrientationDegrees(fp.GetOrientationDegrees() + 180.0)
for ref in ('R339', 'C338', 'R340', 'R343', 'D301'):
    pads[ref] = {p.GetNumber(): P(p.GetPosition()) for p in b.FindFootprintByReference(ref).Pads()}
    print(ref, pads[ref])
outa, tap = net('OutA'), net('VSWA_SENSE')
pcbnew.SaveBoard(dst, b)
del b
print('removed', rip_text(dst, kill))
r = R.Router(dst)
r._fixed = True
B = lambda n, pts, w=0.2: [r.add_track(n, 'B.Cu', p, q, w) for p, q in zip(pts, pts[1:])]
B(outa, [pads['C338']['1'], pads['R339']['1']])
B(outa, [(194.25, 183.65), (193.3, 182.7), (193.3, 181.3), pads['R339']['1']])
B(tap, [pads['C338']['2'], pads['R339']['2']])
B(tap, [pads['R343']['2'], pads['C338']['2']])
B(tap, [pads['R340']['1'], pads['R339']['2']])
r.add_via('GND', (188.9, 180.6)); B('GND', [pads['R340']['2'], (189.2, 180.9), (188.9, 180.6)], 0.25)
r.save()
print('written', dst)

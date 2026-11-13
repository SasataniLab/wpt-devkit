#!/usr/bin/env python3
"""Leg-A comparator line: the 1 k series resistor R343 moves from the divider to the MCU end of the sense line.

usage: phys3.py BOARD_IN BOARD_OUT

One sense line per leg then leaves the divider; the comparator input is a 3 mm stub behind 1 k instead of a second
70 mm line that would have to cross the gate signals.
"""
import shutil
import sys

import pcbnew

import router as R

R.DEFAULT_CORRIDORS = ()
MM = 1e6
src, dst = sys.argv[1:3]
shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)
fp = b.FindFootprintByReference('R343')
fp.SetPosition(pcbnew.VECTOR2I(int(185.0 * MM), int(163.9 * MM)))
fp.SetOrientationDegrees(90.0)
pads = {p.GetNumber(): (round(p.GetPosition().x / MM, 3), round(p.GetPosition().y / MM, 3)) for p in fp.Pads()}
if pads['1'][1] > pads['2'][1]:                   # comparator pad has to be the upper one
    fp.SetOrientationDegrees(270.0)
    pads = {p.GetNumber(): (round(p.GetPosition().x / MM, 3), round(p.GetPosition().y / MM, 3)) for p in fp.Pads()}
print('R343', pads)
cmpn = [str(n) for n in b.GetNetsByName().asdict().keys() if str(n).endswith('/VSWA_CMP')][0]
pcbnew.SaveBoard(dst, b)
del b
r = R.Router(dst)
r._fixed = True
pts = [pads['1'], (185.0, 162.9), (185.3, 162.6), (185.3, 160.7)]
for p, q in zip(pts, pts[1:]):
    r.add_track(cmpn, 'B.Cu', p, q, 0.2)
r.save()

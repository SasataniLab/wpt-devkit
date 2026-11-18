#!/usr/bin/env python3
"""Three local hand fixes after auto-routing: tie the GND pads of C15, C210 and R338 to the ground plane.

usage: fix3.py BOARD_IN BOARD_OUT
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


def keys_in(net_end, layer, box, both=True):
    x0, y0, x1, y1 = box
    out = set()
    ins = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    for t in b.GetTracks():
        net = t.GetNetname()
        if not net.endswith(net_end):
            continue
        if t.GetClass() == 'PCB_VIA':
            c = (t.GetPosition().x / MM, t.GetPosition().y / MM)
            if layer == 'VIA' and ins(c):
                out.add(R.Router.vkey(net, c))
        elif b.GetLayerName(t.GetLayer()) == layer:
            a = (t.GetStart().x / MM, t.GetStart().y / MM)
            e = (t.GetEnd().x / MM, t.GetEnd().y / MM)
            if (ins(a) and ins(e)) if both else (ins(a) or ins(e)):
                out.add(R.Router.tkey(net, layer, a, e))
    return out


def move(ref, x, y, drot=0.0):
    fp = b.FindFootprintByReference(ref)
    fp.SetPosition(pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM))))
    if drot:
        fp.SetOrientationDegrees(fp.GetOrientationDegrees() + drot)
    print(ref, [(p.GetNumber(), p.GetNetname().split('/')[-1], round(p.GetPosition().x / MM, 3), round(p.GetPosition().y / MM, 3)) for p in fp.Pads()])


kill = set()
# 1. C15: turn it round so that the GND pad faces the free side; redo the two short ENCODER_PUSH links
kill |= keys_in('GPIO_ENCODER_PUSH', 'B.Cu', (171.9, 147.4, 172.85, 149.0))
# 2. R338 (EEV2 pull-down): next to the ground via that already serves R336
kill |= keys_in('HRTIM1_EEV2', 'B.Cu', (174.9, 138.5, 176.6, 139.5))
kill.add(R.Router.vkey('GND', (185.85, 138.4)))      # a ground stitching via that sits where the resistor goes
# 3. level shifter: SDA_5V hairpin and the +5V feed that sat where C210's ground via belongs
kill |= keys_in('SDA_5V', 'B.Cu', (158.2, 157.8, 160.8, 162.1))
kill |= keys_in('+5V', 'B.Cu', (158.9, 160.2, 159.75, 162.95))
move('C15', 172.7, 148.9, 180.0)
move('R338', 185.3, 138.65, -90.0)
pcbnew.SaveBoard(dst, b)
del b
print('removed', rip_text(dst, kill), 'pieces of copper')

r = R.Router(dst)
r._fixed = True
N = lambda s: [n for n in r.nets if n.split('/')[-1] == s][0]
Bt = lambda net, pts, w=0.2: [r.add_track(net, 'B.Cu', p, q, w) for p, q in zip(pts, pts[1:])]
Ft = lambda net, pts, w=0.2: [r.add_track(net, 'F.Cu', p, q, w) for p, q in zip(pts, pts[1:])]
# 1. C15
enc = N('GPIO_ENCODER_PUSH')
Bt(enc, [(172.8, 148.2), (172.2, 147.6), (172.19, 147.3)])
Bt(enc, [(173.18, 148.9), (173.18, 148.2)])
r.add_via('GND', (171.2, 148.9)); Bt('GND', [(172.22, 148.9), (171.2, 148.9)], 0.25)
# 2. R338
eev2 = N('HRTIM1_EEV2')
Bt(eev2, [(174.95, 138.6), (175.21, 139.0), (175.21, 139.35)])
# 3. level shifter
sda5 = N('SDA_5V')
Bt(sda5, [(158.3, 158.05), (158.75, 158.5), (160.05, 158.5), (160.7, 157.85)])
Bt('+5V', [(159.0, 160.25), (159.0, 160.5), (159.7, 161.2), (159.7, 162.9)])
r.add_via('GND', (158.85, 162.0)); Ft('GND', [(158.8, 161.644), (158.85, 162.0)], 0.25)
r.save()

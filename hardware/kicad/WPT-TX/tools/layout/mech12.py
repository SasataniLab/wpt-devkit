#!/usr/bin/env python3
"""Revision 7, part 2: J2 as two rows of six in the top strip, the clock link R346. usage: mech12.py BOARD_IN BOARD_OUT NETLIST

What tools/schematic/edit_sch11.py asks for (J2, R346), with hand-chosen coordinates. The seven signals of J2 that are
laid out again lose all their copper here; the router (nego.py, then smooth45.py, shorten.py) draws them afterwards.

J2 (2 x 6, 2.54 mm) stands where the comparators were: odd pins in the inner row y = 136.42, even pins in the outer row
y = 133.88 (a pin header cannot be turned the other way round without mirroring it), columns x = 171.00 + 2.54 k, pin 1 at
the west end. The back-side track SCL_3.3V (y = 135.20) stays: it passes between the two rows.
The two supply pins go straight to the planes (In1 GND, In2 +3V3).

R331, R332 and the test pad TP304 (fault input FLT3) stood in the way and move 5.3 mm to the west, with their three vias.

Y1 took its ground from pin 12 of the old J2 (a through-hole pad). It gets a via of its own at the end of that track.

R346 (0 ohm, not fitted) lies between C11 and the edge of Y1's courtyard, 1 mm from the crystal pad, so that the open
land adds nothing but 1 mm of track to the oscillator node.
"""
import shutil
import sys

import pcbnew

import newfp
from newfp import seg, via, place, pads, net, flush, P, V

src, dst, netlist = sys.argv[1:4]
shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)
comps = newfp.load_netlist(netlist)
NETS = {n for c in comps.values() for n in c['pins'].values()}


def N(short):
    hit = [n for n in NETS if n == short or n.split('/')[-1] == short]
    assert len(hit) == 1, (short, hit)
    net(b, hit[0])
    return hit[0]


def put(ref, x, y, want, rots=(0, 90, 180, 270), side='F'):
    if b.FindFootprintByReference(ref) is not None:
        newfp.remove_footprint(b, ref)
    fp = place(b, comps, ref, x, y, rot=rots[0], side=side)
    for r in rots:
        fp.SetOrientationDegrees(r)
        got = pads(fp)
        if all(abs(got[k][0] - v[0]) < 0.02 and abs(got[k][1] - v[1]) < 0.02 for k, v in want.items()):
            break
    else:
        raise AssertionError((ref, got, want))
    t = fp.Reference()
    t.SetPosition(V(x, y))
    t.SetTextAngleDegrees(0)
    return fp


STRIP = ('SPI1_CLK_DISP', 'SPI1_MISO_DISP', 'SPI1_MOSI_DISP', 'ADC2_IN8_EXTERNAL', 'GPIO_DISP_CS', 'GPIO_DISP_DC', 'GPIO_DISP_RST')
k = 0
for t in list(b.GetTracks()):
    if t.GetNetname().split('/')[-1] in STRIP:
        newfp._PENDING.append(t)
        k += 1
print('copper of the seven display signals marked:', k)

# ------------------------------------------------------------------ J2
X0, YN, YS = 171.0, 133.88, 136.42
put('J2', X0, YS, {'1': (X0, YS), '2': (X0, YN), '3': (X0 + 2.54, YS), '12': (X0 + 12.7, YN)})

# ------------------------------------------------------------------ R331, R332, TP304 and their vias: 5.3 mm west
DX = -5.3
FLT, G, V3 = N('HRTIM1_FLT3'), 'GND', '+3V3'
newfp.rip(b, FLT, 'F.Cu', [(172.27, 134.11), (173.54, 134.11), (173.54, 136.42)], expect=2)
newfp.rip(b, FLT, 'B.Cu', [(173.54, 136.42), (169.73, 140.23), (169.73, 140.57)], expect=2)
newfp.rip_via(b, FLT, (173.54, 136.42))
newfp.rip(b, G, 'F.Cu', [(173.54, 133.09), (173.54, 132.2)], expect=1)
newfp.rip_via(b, G, (173.54, 132.2))
newfp.rip(b, V3, 'F.Cu', [(172.27, 133.09), (172.27, 132.2)], expect=1)
newfp.rip_via(b, V3, (172.27, 132.2))
x1, x2 = 172.27 + DX, 173.54 + DX
put('R331', x1, 133.6, {'1': (x1, 133.09)})
put('R332', x2, 133.6, {'1': (x2, 134.11)})
put('TP304', x2, 136.42, {'1': (x2, 136.42)})
seg(b, FLT, [(x1, 134.11), (x2, 134.11), (x2, 136.42)], layer='F.Cu')
via(b, FLT, (x2, 136.42))
seg(b, FLT, [(x2, 136.42), (x2, 139.08), (169.73, 140.57)], layer='B.Cu')
seg(b, G, [(x2, 133.09), (x2, 132.2)], w=0.25, layer='F.Cu')
via(b, G, (x2, 132.2))
seg(b, V3, [(x1, 133.09), (x1, 132.2)], w=0.25, layer='F.Cu')
via(b, V3, (x1, 132.2))

# ------------------------------------------------------------------ Y1: its own ground via
newfp.rip(b, G, 'F.Cu', [(185.97, 142.47), (186.24, 142.2)], expect=1)
via(b, G, (185.97, 142.47))

# ------------------------------------------------------------------ R346
put('R346', 187.8, 144.85, {'1': (187.29, 144.85)})
seg(b, 'HSE_EXT', [(187.3, 144.85), (187.3, 145.9)], layer='F.Cu')

seen, once = set(), []
for x in newfp._PENDING:
    u = x.m_Uuid.AsString()
    if u not in seen:
        seen.add(u)
        once.append(x)
newfp._PENDING[:] = once
print('removed', flush(b))
pcbnew.SaveBoard(dst, b)

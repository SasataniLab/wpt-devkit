#!/usr/bin/env python3
"""Revision 7, part 2: J2 as two rows of six in the top strip, its eight signals, the clock link R346.
usage: mech12.py BOARD_IN BOARD_OUT NETLIST

What tools/schematic/edit_sch11.py asks for (J2, R346), with hand-chosen coordinates.

J2 (2 x 6, 2.54 mm) stands where the comparators were: odd pins in the inner row y = 136.42, even pins in the outer row
y = 133.88 (a pin header cannot be turned the other way round without mirroring it), columns x = 171.00 + 2.54 k, pin 1 at
the west end. The back-side track SCL_3.3V (y = 135.20) stays: it passes between the two rows. The supply pins go
straight to the planes (In1 GND, In2 +3V3).

The eight signals run on the front side, in the order of the pins of J2, so that none crosses another:
  PA7 MOSI, PA6 MISO, PA5 SCK, PA3 DC, PA4 RST leave the west side of the MCU and pass the encoder between its pad S2
  and the reset line, five lanes on a pitch of 0.45 / 0.5 mm; north of the pad they fan out to the columns of J2.
  PA2 CS and PC2 ADC leave the north side; PB3 IO comes on the back side from the east as before and changes sides at
  (182.43, 142.73). A pin of the outer row is reached between two pads of the inner row: straight north at
  x = pad + 1.27, then 45 degrees into the pad.
Lengths: 16 to 22 mm (the old row was 10 to 20 mm away, by longer ways round the encoder).
What had to give way:
  NRST          changes to the back side earlier (via 172.20 instead of 176.05) and passes under the eight signals;
                its piece on the front side moves 0.7 mm east (x = 178.90).
  HV_SW_STATE   wove through the old tracks with four vias; now one piece on the back side (y = 144.95).

R331, R332 and the test pad TP304 (fault input FLT3) stood in the way of J2 and move 5.3 mm to the west, with their vias.

Y1 took its ground from pin 12 of the old J2 (a through-hole pad). It gets a via of its own at the end of that track.

R346 (0 ohm, not fitted) lies between C11 and the edge of Y1's courtyard, 1 mm from the crystal pad, so that the open
land adds nothing but 1 mm of track to the oscillator node. CLK1 of U306 is closed in by the tracks of its neighbours
and leaves its pad towards the inside of the package (the path the router found, straightened).
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
hse = [k for k, v in comps['R346']['pins'].items() if v == 'HSE_EXT'][0]      # whichever pin of the link is on the crystal net lies west
put('R346', 187.8, 144.85, {hse: (187.29, 144.85)})
seg(b, 'HSE_EXT', [(187.3, 144.85), (187.3, 145.9)], layer='F.Cu')
CLK1 = N('Net-(U306-CLK1)')
seg(b, CLK1, [(188.31, 144.85), (189.3, 144.85), (190.1, 145.65)], layer='F.Cu')
via(b, CLK1, (190.1, 145.65))
seg(b, CLK1, [(190.1, 145.65), (190.3, 145.85), (195.45, 145.85), (197.55, 147.95), (198.45, 147.95)], layer='B.Cu')
via(b, CLK1, (198.45, 147.95))
seg(b, CLK1, [(198.45, 147.95), (200.8, 150.3), (202.62, 150.3), (202.919, 150.599), (202.919, 151.375)], layer='F.Cu')

# ------------------------------------------------------------------ NRST and HV_SW_STATE make room
NRST, HV = N('NRST'), N('HV_SW_STATE')
newfp.rip(b, NRST, 'F.Cu', [(176.05, 139.55), (157.8, 139.55)], expect=1)
newfp.rip_via(b, NRST, (176.05, 139.55))
newfp.rip(b, NRST, 'B.Cu', [(176.05, 139.55), (176.25, 139.75), (178.6, 139.75), (179.85, 141.0), (179.85, 143.45), (179.4, 143.9)])
newfp.rip_via(b, NRST, (179.4, 143.9))
newfp.rip(b, NRST, 'F.Cu', [(179.4, 143.9), (178.2, 145.1), (178.2, 148.75)])
newfp.rip_via(b, NRST, (178.2, 148.75))
newfp.rip(b, NRST, 'B.Cu', [(184.18, 148.75), (178.2, 148.75)], expect=1)
seg(b, NRST, [(157.8, 139.55), (172.2, 139.55)], layer='F.Cu')
via(b, NRST, (172.2, 139.55))
seg(b, NRST, [(172.2, 139.55), (172.4, 139.75), (178.6, 139.75), (178.9, 140.05), (178.9, 143.0)], layer='B.Cu')
via(b, NRST, (178.9, 143.0))
seg(b, NRST, [(178.9, 143.0), (178.9, 148.75)], layer='F.Cu')
via(b, NRST, (178.9, 148.75))
seg(b, NRST, [(178.9, 148.75), (184.18, 148.75)], layer='B.Cu')
newfp.rip(b, HV, 'B.Cu', [(175.3, 144.55), (174.9, 144.95)], expect=1)
newfp.rip(b, HV, 'F.Cu', [(176.9, 144.55), (175.3, 144.55)], expect=1)
newfp.rip(b, HV, 'B.Cu', [(176.9, 144.55), (178.1, 144.55), (178.9, 145.35)], expect=2)
newfp.rip(b, HV, 'F.Cu', [(178.9, 145.35), (179.35, 144.9), (180.35, 144.9), (181.0, 145.55)], expect=3)
for c in ((175.3, 144.55), (176.9, 144.55), (178.9, 145.35), (181.0, 145.55)):
    newfp.rip_via(b, HV, c)
seg(b, HV, [(174.9, 144.95), (180.4, 144.95), (181.0, 145.55)], layer='B.Cu')

# ------------------------------------------------------------------ the eight signals of J2 (front side)
YA = YN + 1.27                                    # where the 45-degree piece to a pin of the outer row begins
for short, pts in (
        ('SPI1_MOSI_DISP', [(178.225, 152.15), (176.4, 152.15), (176.25, 152.0), (176.25, 145.3), (173.54, 142.59), (173.54, YS)]),
        ('SPI1_MISO_DISP', [(178.225, 151.65), (176.85, 151.65), (176.7, 151.5), (176.7, 145.0), (174.81, 143.11), (174.81, YA), (173.54, YN)]),
        ('SPI1_CLK_DISP', [(178.225, 151.15), (177.3, 151.15), (177.15, 151.0), (177.15, 144.7), (176.08, 143.63), (176.08, YS)]),
        ('GPIO_DISP_DC', [(177.65, 150.15), (177.65, 139.5), (177.35, 139.2), (177.35, YA), (176.08, YN)]),
        ('GPIO_DISP_RST', [(178.225, 150.65), (179.4, 150.65), (179.4, 149.85), (179.15, 149.6), (178.45, 149.6), (178.15, 149.3), (178.15, 140.4),
                           (178.62, 139.93), (178.62, YS)]),
        ('GPIO_DISP_CS', [(181.15, 148.225), (181.15, 146.9), (179.89, 145.64), (179.89, YA), (178.62, YN)]),
        ('ADC2_IN8_EXTERNAL', [(183.15, 148.225), (183.15, 147.3), (181.16, 145.31), (181.16, YS)])):
    seg(b, N(short), pts, layer='F.Cu')
IO = N('GPIO_SW_MISC1')
newfp.rip(b, IO, 'B.Cu', [(186.55, 146.85), (181.3, 141.6)], expect=1)
seg(b, IO, [(186.55, 146.85), (182.43, 142.73)], layer='B.Cu')
via(b, IO, (182.43, 142.73))
seg(b, IO, [(182.43, 142.73), (182.43, YA), (181.16, YN)], layer='F.Cu')

seen, once = set(), []
for x in newfp._PENDING:
    u = x.m_Uuid.AsString()
    if u not in seen:
        seen.add(u)
        once.append(x)
newfp._PENDING[:] = once
print('removed', flush(b))
pcbnew.SaveBoard(dst, b)

#!/usr/bin/env python3
"""Revision 5, part 1: what has to be decided by hand. usage: mech9.py BOARD_IN BOARD_OUT
(Part 2 is tools/layout/shorten.py, which re-lays single runs; see README.md.)

1. Leg-A comparator output. In revision 4 R335 / R336 stayed in the resistor row at y = 133.6, so the output of U308
   ran 4 mm north to R335 and HRTIM1_EEV1 came 6 mm back south along x = 177.35 before it turned east: a U-turn of
   about 10 mm. Now both resistors stand directly west of the output pin:
     * R335 (100 ohm, series) upright at (177.30, 138.65): pad 1 on a 1.5 mm link from U308 pin 1, pad 2 down a
       45-degree piece into the lane y = 140.00.
     * R336 (pull-down) upright at (176.20, 137.80), 0.85 mm higher than R335 because the NRST via sits at
       (176.05, 139.55); its ground via is 0.9 mm west of pad 2.
   The pin list of J2 on the silkscreen is wrapped into four lines so that it ends west of the two resistors.
   The old ground via of R336 at (177.35, 132.20) goes with its track.

2. Threshold line. ZVS_VTH climbed over the ground vias of the row, ran along y = 131.55 as far as TP303 and came
   down there. With R335 / R336 out of the row it comes down right behind the last ground via (R332) on one
   45-degree piece and reaches the bus at C344: 13.6 mm instead of 17.1 mm. TP303 keeps a 1.6 mm stub from the bus.

3. Gate signals of leg A (HRTIM1_CHC1 / CHC2, back side). The pair ran down the west side of the driver area and
   turned east with a 0.4 mm chamfer. The chamfer is now 3.2 mm (CHC1) and 3.65 mm (CHC2), as large as the ground via
   at (188.20, 189.10) allows; the two stay parallel at 0.6 mm.

4. Net-(U301-A) passed the 2 mm screw hole at (195.00, 162.35) on an arc of 31 tiny pieces. The same clearance
   (0.3 mm to the pad of the hole) is kept by one 45-degree piece.

5. The four pieces that were not on 0 / 45 / 90 degrees (BOOT0, ~{WLAT}, SPI1_CLK_DISP, TIM3_CH1_ENCODER). Each
   threads between two vias or a via and a pad; a 45-degree shape with the same clearances was found for each by
   hand. They get 0.1 to 0.4 mm longer, which is the price of the angle.

6. Copper of one net lying on top of itself (left from the routing passes of revisions 1 to 3): doubled lines and
   steps of a few hundredths of a millimetre at the level shifter U202 (SCL_3.3V, SDA_3.3V, SDA_5V, SCL), at the
   driver inputs (H_Sig2, L_Sig2), at the via of SCL_5V and where SCL_3.3V turns south under J2. One clean line each.
"""
import math
import shutil
import sys

import pcbnew

import newfp
from newfp import seg, via, rip, rip_via, pads, flush, V

src, dst = sys.argv[1:3]
shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)
N = lambda s: newfp.full_name(b, s)
A_IN, EEV1, VTH, GND = N('ZVS_A_IN'), N('HRTIM1_EEV1'), N('ZVS_VTH'), 'GND'


def move(ref, x, y, want):
    """move a footprint; try the four right angles until its pads are where `want` says; reference not shown"""
    fp = b.FindFootprintByReference(ref)
    fp.SetPosition(V(x, y))
    for r in (0, 90, 180, 270):
        fp.SetOrientationDegrees(r)
        got = pads(fp)
        if all(abs(got[k][0] - v[0]) < 0.006 and abs(got[k][1] - v[1]) < 0.006 for k, v in want.items()):
            break
    else:
        raise AssertionError((ref, pads(fp), want))
    fp.Reference().SetVisible(False)                      # no room for it between the comparator and the header
    fp.Reference().SetPosition(V(x, y))
    return fp


# ---- old copper of the leg-A output
rip(b, A_IN, 'F.Cu', [(178.80, 138.3375), (178.10, 138.3375), (178.10, 134.63), (178.62, 134.11)], expect=3)
rip(b, EEV1, 'F.Cu', [(178.62, 133.09), (177.99, 133.09), (177.99, 133.84), (177.72, 134.11), (177.35, 134.11), (177.35, 139.70),
                      (177.65, 140.00), (189.95, 140.00)], expect=7)
rip(b, GND, 'F.Cu', [(177.35, 133.09), (177.35, 132.20)], expect=1)
rip_via(b, GND, (177.35, 132.20))

# ---- the two resistors beside the output pin
move('R335', 177.30, 138.65, {'1': (177.30, 138.14), '2': (177.30, 139.16)})
move('R336', 176.20, 137.80, {'1': (176.20, 138.31), '2': (176.20, 137.29)})
seg(b, A_IN, [(178.80, 138.14), (177.30, 138.14)])                                   # starts inside pad 1 of U308 (pad: y 137.68 .. 139.00)
seg(b, EEV1, [(177.30, 139.16), (178.14, 140.00), (189.95, 140.00)])                 # into the old lane
seg(b, EEV1, [(176.20, 138.31), (177.05, 139.16), (177.30, 139.16)])                 # R336 -> pad 2 of R335
seg(b, GND, [(176.20, 137.29), (175.30, 137.29)], w=0.25)
via(b, GND, (175.30, 137.29))

# the pin list of J2 on the silkscreen ran through the new place of the two resistors: four shorter lines instead of three
LEGEND = {'J2  1:GND 2:+3V3 3:SCK': ('J2 1:GND 2:+3V3 3:SCK', 136.40), '4:MISO 5:MOSI 6:ADC 7:CS 8:DC': ('4:MISO 5:MOSI 6:ADC', 137.45),
          '9:RST 10:IO 11:+3V3 12:GND': ('7:CS 8:DC 9:RST 10:IO', 138.50)}
found = 0
for d in b.GetDrawings():
    if d.GetClass() == 'PCB_TEXT' and d.GetText() in LEGEND:
        txt, y = LEGEND[d.GetText()]
        d.SetText(txt)
        d.SetPosition(V(157.6, y))
        found += 1
assert found == 3, found
newfp.text(b, '11:+3V3 12:GND', 157.6, 139.55)

# ---- threshold line
rip(b, VTH, 'F.Cu', [(169.73, 133.09), (169.73, 131.85), (170.03, 131.55), (182.30, 131.55), (182.60, 131.85), (182.60, 134.58)], expect=5)
seg(b, VTH, [(169.73, 133.09), (169.73, 132.60), (170.78, 131.55), (174.25, 131.55), (177.28, 134.58), (180.70, 134.58)])
seg(b, VTH, [(182.60, 134.58), (182.60, 133.00)])                                    # test pad TP303


# ---- 3. gate signals of leg A: a real 45-degree corner instead of an L
CHC1, CHC2 = N('HRTIM1_CHC1'), N('HRTIM1_CHC2')
rip(b, CHC1, 'B.Cu', [(185.45, 170.10), (185.45, 190.20), (185.85, 190.60), (192.70, 190.60)], expect=3)
seg(b, CHC1, [(185.45, 170.10), (185.45, 187.40), (188.65, 190.60), (192.70, 190.60)], layer='B.Cu')
rip(b, CHC2, 'B.Cu', [(184.85, 168.55), (184.85, 190.85), (185.30, 191.30), (191.89, 191.30)], expect=3)
seg(b, CHC2, [(184.85, 168.55), (184.85, 187.65), (188.50, 191.30), (191.89, 191.30)], layer='B.Cu')


# ---- helpers for exact pieces
def cut(netname, layer, a, e, tol=0.002):
    """mark the track piece a - e (either direction) for removal"""
    gone = {x.m_Uuid.AsString() for x in newfp._PENDING}          # (two Python objects can stand for one track: compare the ids)
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != netname or b.GetLayerName(t.GetLayer()) != layer or t.m_Uuid.AsString() in gone:
            continue
        p, q = newfp.P(t.GetStart()), newfp.P(t.GetEnd())
        if (math.dist(p, a) < tol and math.dist(q, e) < tol) or (math.dist(p, e) < tol and math.dist(q, a) < tol):
            newfp._PENDING.append(t)
            return t.GetWidth() / newfp.MM
    raise AssertionError(('no such piece', netname, layer, a, e))


def chain(netname, layer, pts):
    """mark the pieces pts[0] - pts[1] - ... for removal"""
    for p, q in zip(pts, pts[1:]):
        cut(netname, layer, p, q)


# ---- 4. the arc round the 2 mm screw hole
UA = 'Net-(U301-A)'
arc = []                                                  # the pieces between (197.15, 162.65) and the first point on y = 164.50
for t in b.GetTracks():
    if t.Type() != pcbnew.PCB_VIA_T and t.GetNetname() == UA and b.GetLayerName(t.GetLayer()) == 'F.Cu':
        p, q = newfp.P(t.GetStart()), newfp.P(t.GetEnd())
        if all(194.9 <= x <= 197.16 and 162.64 <= y <= 164.51 for x, y in (p, q)):
            arc.append((t, p, q))
ends = {}
for t, p, q in arc:
    for x in (p, q):
        ends[x] = ends.get(x, 0) + 1
tips = sorted(x for x, n in ends.items() if n == 1)
assert len(arc) >= 30 and tips[-1] == (197.15, 162.65) and abs(tips[0][1] - 164.50) < 1e-6, (len(arc), tips)
newfp._PENDING.extend(t for t, p, q in arc)
cut(UA, 'F.Cu', (197.15, 161.10), (197.15, 162.65))
seg(b, UA, [(197.15, 161.10), (197.15, 163.24), (195.89, 164.50), tips[0]])        # 2.15 mm from the centre of the hole, as before

# ---- 5. the four off-angle pieces
BOOT0, WLAT, SCK, ENC1 = (N(x) for x in ('BOOT0', '~{WLAT}', 'SPI1_CLK_DISP', 'TIM3_CH1_ENCODER'))
cut(BOOT0, 'B.Cu', (171.05, 153.30), (171.40, 156.20))                               # between the vias of FLT3 (west) and USART1 / HV_EN (east)
seg(b, BOOT0, [(171.05, 153.30), (171.05, 154.60), (171.40, 154.95), (171.40, 156.20)], layer='B.Cu')
chain(WLAT, 'F.Cu', [(162.15, 154.50), (163.55, 153.10), (168.80, 152.90), (168.95, 152.75)])   # 0.2 mm above USART1_TX, 0.25 mm below a ground via
seg(b, WLAT, [(162.15, 154.50), (163.65, 153.00), (168.70, 153.00), (168.95, 152.75)])
chain(SCK, 'F.Cu', [(172.00, 145.85), (174.05, 145.85), (174.25, 146.05), (175.75, 147.00), (176.30, 147.55), (176.30, 150.15)])
seg(b, SCK, [(172.00, 145.85), (174.525, 145.85), (176.30, 147.625), (176.30, 150.15)])           # between the via of ADC2_IN8 and the pad of SW1
chain(ENC1, 'B.Cu', [(162.20, 149.15), (162.60, 149.55), (168.15, 153.45), (168.30, 153.45), (169.85, 155.00)])
seg(b, ENC1, [(162.20, 149.15), (164.55, 151.50), (166.35, 151.50), (169.85, 155.00)], layer='B.Cu')

# ---- 6. one net lying on top of itself
S33, D33, D5, SCL, S5, H2, L2 = (N(x) for x in ('SCL_3.3V', 'SDA_3.3V', 'SDA_5V', 'SCL', 'SCL_5V', 'H_Sig2', 'L_Sig2'))
# SCL_3.3V at U202: pin 3 -> R215 east, -> R219 west and south, R219 -> via
chain(S33, 'F.Cu', [(164.95, 159.85), (164.40, 159.85), (164.25, 160.00), (164.25, 160.0192), (164.2115, 160.0577), (164.2115, 160.0885),
                    (164.15, 160.15), (164.15, 161.20), (164.90, 161.95), (165.60, 161.95)])
chain(S33, 'F.Cu', [(164.20, 160.05), (164.35, 159.90), (164.95, 159.90), (165.80, 159.90), (165.95, 159.75)])
chain(S33, 'F.Cu', [(164.95, 159.85), (165.60, 159.85), (165.80, 159.65), (165.90, 159.65)])
chain(S33, 'F.Cu', [(165.85, 159.894), (165.972, 159.772), (165.997, 159.747), (166.10, 159.644)])
chain(S33, 'F.Cu', [(164.95, 159.894), (164.206, 159.894), (164.125, 159.975), (164.10, 160.00), (164.10, 160.05), (164.10, 161.344)])
seg(b, S33, [(165.85, 159.894), (166.10, 159.644)])
seg(b, S33, [(164.95, 159.894), (164.206, 159.894), (164.10, 160.00), (164.10, 161.344)])
seg(b, S33, [(164.90, 162.144), (165.406, 162.144), (165.60, 161.95)])
# SDA_3.3V at U202: pin 4 -> through the pad of R216 -> on to the east
chain(D33, 'F.Cu', [(164.95, 159.394), (165.35, 159.394), (165.447, 159.297), (165.547, 159.197), (166.10, 158.644)])
chain(D33, 'F.Cu', [(165.45, 159.30), (165.55, 159.20), (166.103, 158.647), (166.50, 158.25), (166.75, 158.00)])
seg(b, D33, [(164.95, 159.394), (165.356, 159.394), (166.75, 158.00)])
# SDA_5V: the branch from the via joins the line of pin 5 at a right angle instead of running beside it to R222
chain(D5, 'F.Cu', [(164.00, 158.85), (163.25, 159.60), (163.25, 161.75), (163.00, 162.00)])
cut(D5, 'F.Cu', (163.10, 159.8793), (162.6147, 159.394))
seg(b, D5, [(162.6147, 159.394), (163.03535, 159.81465), (163.10, 159.8793)], allow_any_angle=True)
seg(b, D5, [(164.00, 158.85), (163.03535, 159.81465)], allow_any_angle=True)
# SCL at R219: the line from the east ends in the via, the via reaches the pad
chain(SCL, 'F.Cu', [(171.95, 161.25), (167.25, 161.25), (165.475, 163.025), (165.45, 163.05), (165.10, 163.05), (165.05, 163.05)])
seg(b, SCL, [(171.95, 161.25), (167.50, 161.25), (165.60, 163.15)])
# SCL_5V: the via sits beside the long line
chain(S5, 'F.Cu', [(161.10, 165.50), (161.25, 165.50), (161.40, 165.65), (161.50, 165.65), (161.55, 165.70)])
cut(S5, 'F.Cu', (169.90, 165.50), (160.9072, 165.50))
seg(b, S5, [(169.90, 165.50), (161.35, 165.50), (160.9072, 165.50)])
seg(b, S5, [(161.35, 165.50), (161.55, 165.70)])
# SCL_3.3V under J2: the diagonal from the north-east turns south in one corner
chain(S33, 'B.Cu', [(165.50, 137.65), (162.45, 140.70), (162.45, 140.75), (162.425, 140.775), (162.40, 140.80), (162.40, 140.85), (162.30, 140.95)])
chain(S33, 'B.Cu', [(162.40, 140.75), (162.2892, 140.8608), (162.2892, 140.9438), (162.20, 141.033), (162.20, 143.75)])
seg(b, S33, [(165.50, 137.65), (162.20, 140.95), (162.20, 143.75)], layer='B.Cu')
# SCL_3.3V at U306: two lines 19 um apart into pin 4
chain(S33, 'F.Cu', [(200.65, 149.20), (200.75, 149.20), (201.85, 148.10), (201.90, 148.05), (201.90, 148.00), (201.90, 147.8967), (201.90, 147.15)])
cut(S33, 'F.Cu', (201.919, 146.975), (201.919, 147.8967))
seg(b, S33, [(200.65, 149.20), (200.819, 149.20), (201.919, 148.10), (201.919, 146.975)])
# ZVS_VTH_DAC at pin 33 of the MCU: three little chains on top of each other
DAC = N('ZVS_VTH_DAC')
for _ in range(2):
    chain(DAC, 'F.Cu', [(180.00, 159.35), (180.00, 159.425), (180.15, 159.575)])
chain(DAC, 'F.Cu', [(180.00, 159.35), (180.05, 159.40), (180.05, 159.475), (180.15, 159.575)])
cut(DAC, 'F.Cu', (180.00, 159.35), (178.45, 159.35))
seg(b, DAC, [(180.15, 159.575), (179.925, 159.35), (178.45, 159.35)])
# L_Sig2 between R329, R330 and its via (back side): steps of 0.07 mm inside and beside the pad of R330
chain(L2, 'B.Cu', [(192.70, 174.51), (192.70, 174.62), (192.70, 174.68), (192.10, 175.28), (192.10, 175.3246), (192.0149, 175.4097),
                   (192.0149, 175.4751), (191.89, 175.60)])
seg(b, L2, [(192.70, 174.51), (192.70, 174.68), (191.89, 175.49)], layer='B.Cu')        # the old diagonal, carried on into the pad of R330
chain(L2, 'B.Cu', [(192.0553, 175.8553), (192.0553, 175.60), (192.0553, 175.5291), (192.0553, 175.4553), (192.00, 175.40)])
# driver inputs of leg B: a piece laid twice, and a branch beside the line it belongs to
cut(H2, 'F.Cu', (191.10, 172.20), (191.70, 172.20))
chain(L2, 'F.Cu', [(193.80, 175.10), (193.80, 175.75), (193.05, 176.50)])
cut(L2, 'F.Cu', (193.875, 176.225), (193.875, 174.975))
seg(b, L2, [(193.875, 176.225), (193.875, 175.675), (193.875, 174.975)])
seg(b, L2, [(193.875, 175.675), (193.05, 176.50)])

print('items removed:', flush(b))
pcbnew.SaveBoard(dst, b)
print('saved', dst)

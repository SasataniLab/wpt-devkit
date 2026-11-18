#!/usr/bin/env python3
"""East side of the MCU and the J301 / J3 headers, laid out by hand. usage: phys6.py BOARD_IN REG.json BOARD_OUT

Everything here is on 0 / 45 / 90 degrees.

The idea
  * top side, east of the MCU: the pins that go north leave as a comb, without vias, in the order of the pins
    (HV_SW_STATE, EEV1, EEV2, SWCLK, SWDIO from the pads outwards), then the USB pair. Return current in In1 (GND).
  * back side, east of the MCU: nothing but the two divider-tap lines to J301 (1.4 mm apart). No logic signal
    shares that layer there; the comparator outputs (EEV) are on the other side of two planes.
  * the tap lines run on the back all the way to the through-hole pins of J301: VSWB_SENSE has no via,
    VSWA_SENSE has the two of the hop over VSWB_CMP.
  * GPIO_VUSB_SENSE (a DC level) is the one signal that has to get from the MCU to the east of both the USB pair
    (top) and the tap lines (back): it crosses on In2, 3.2 mm.
  * EEV1 / EEV2 stay on the top side from the MCU pin to their series resistor (no via).
  * SWCLK / SWDIO stay on the top side from the MCU pin to J3 (no via): between J301 pin 1 and U3 into the strip
    north of J301, west along it, round the north and west of J3.
"""
import json
import math
import shutil
import sys

import router as R

R.DEFAULT_CORRIDORS = ()
src, regfile, dst = sys.argv[1:4]
shutil.copy(src, dst)
tup = lambda q: tuple(tuple(x) if isinstance(x, list) else x for x in q)
reg = {n: [tup(q) for q in ks] for n, ks in json.load(open(regfile)).items()}
r = R.Router(dst, reg=reg)
r._fixed = True
net = lambda s: [n for n in r.nets if n.split('/')[-1] == s][0]


def path(name, layer, pts, w=0.2):
    n = net(name)
    for p, q in zip(pts, pts[1:]):
        dx, dy = abs(q[0] - p[0]), abs(q[1] - p[1])
        assert dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-6, ('not on 45 degrees', name, p, q)
        r.add_track(n, layer, p, q, w)


def via(name, c):
    r.add_via(net(name), c)


S2 = math.sqrt(2)
rnd = lambda v: round(v, 4)

# ------------------------------------------------------------------ comb on the top side
X_HV, X_E1, X_E2, X_CK, X_IO, X_DP, X_DN = 190.75, 191.15, 191.55, 191.95, 192.35, 192.90, 193.40

# HV_SW_STATE: pin 57, innermost lane, one via at the north-east corner of the MCU on to its old back-side run
path('HV_SW_STATE', 'F.Cu', [(190.32, 153.65), (190.50, 153.65), (X_HV, 153.40), (X_HV, 149.25), (190.10, 148.60)])
via('HV_SW_STATE', (190.10, 148.60))
path('HV_SW_STATE', 'B.Cu', [(190.10, 148.60), (190.10, 148.00)])

# the four lanes that go on north turn north-west together (0.4 mm apart) at y = 141
Y_E1 = 141.20                                   # EEV1 leaves its lane here
d = 0.4 * S2                                    # shift along the lane for a 0.4 mm perpendicular step
Y_E2, Y_CK, Y_IO = Y_E1 + (X_E2 - X_E1) - d, Y_E1 + (X_CK - X_E1) - 2 * d, Y_E1 + (X_IO - X_E1) - 3 * d
ROW_E1, ROW_E2 = 140.00, 139.60                 # the two EEV rows in the gap between the header rows
X_G56, X_G45 = 177.35, 179.89                   # gaps between J301 pins 5/6 and 4/5
Y_N, Y_S = 133.09, 134.11                       # pad rows of the resistor strip
# EEV1: pin 54 -> lane -> row -> through the gap between J301 pins 5 and 6 -> R336 (pull-down) -> R335 (series)
path('HRTIM1_EEV1', 'F.Cu', [(190.32, 155.15), (190.85, 155.15), (X_E1, 154.85), (X_E1, Y_E1), (rnd(X_E1 - (Y_E1 - ROW_E1)), ROW_E1),
                             (X_G56 + 0.3, ROW_E1), (X_G56, ROW_E1 - 0.3), (X_G56, Y_S)])
path('HRTIM1_EEV1', 'F.Cu', [(X_G56, Y_S), (177.72, Y_S), (177.985, 133.845), (177.985, Y_N), (178.62, Y_N)])
# EEV2: pin 53 -> lane -> row -> through the gap between pins 4 and 5 -> over the resistor strip -> R337 (series) -> R338
Y_TOP = 131.50
path('HRTIM1_EEV2', 'F.Cu', [(190.32, 155.65), (191.25, 155.65), (X_E2, 155.35), (X_E2, rnd(Y_E2)), (rnd(X_E2 - (Y_E2 - ROW_E2)), ROW_E2),
                             (X_G45 + 0.3, ROW_E2), (X_G45, ROW_E2 - 0.3), (X_G45, Y_TOP + 0.3), (X_G45 - 0.3, Y_TOP),
                             (176.38, Y_TOP), (176.08, Y_TOP + 0.3), (176.08, Y_N)])
path('HRTIM1_EEV2', 'F.Cu', [(176.08, Y_N), (175.445, Y_N), (175.445, 133.845), (175.18, Y_S), (174.81, Y_S)])

# SWCLK / SWDIO: lane -> between J301 pin 1 and U3 -> strip north of J301 -> round J3
X_PCK, X_PIO = 190.25, 190.65                   # the two lanes between J301 pin 1 and U3
ROW_CK, ROW_IO = 135.05, 134.65                 # just north of the J301 pad row, below R10
STR_CK, STR_IO = 131.10, 130.70                 # along the strip, north of the resistors
W_CK, W_IO = 133.55, 133.15                     # between the mounting hole and J3
XW_CK, XW_IO = 151.85, 151.45                   # down the west side of J3
x1_io = 188.30                                  # where the rows turn north-west, clear of R10 and the shell of J5
x1_ck = rnd(x1_io - 0.4 * (S2 - 1))
x2_io = 158.70                                  # where they turn south-west, 0.3 mm clear of the mounting-hole pad
x2_ck = rnd(x2_io + 0.4 * (S2 - 1))
path('SWCLK', 'F.Cu', [(190.32, 157.15), (191.65, 157.15), (X_CK, 156.85), (X_CK, rnd(Y_CK)), (X_PCK, rnd(Y_CK - (X_CK - X_PCK))),
                       (X_PCK, ROW_CK + 0.3), (X_PCK - 0.3, ROW_CK), (x1_ck, ROW_CK), (rnd(x1_ck - (ROW_CK - STR_CK)), STR_CK),
                       (x2_ck, STR_CK), (rnd(x2_ck - (W_CK - STR_CK)), W_CK), (XW_CK + 0.4, W_CK), (XW_CK, W_CK + 0.4),
                       (XW_CK, 137.34), (XW_CK + 0.4, 137.74), (153.22, 137.74)])
path('SWDIO', 'F.Cu', [(190.32, 157.65), (192.05, 157.65), (X_IO, 157.35), (X_IO, rnd(Y_IO)), (X_PIO, rnd(Y_IO - (X_IO - X_PIO))),
                       (X_PIO, ROW_IO + 0.3), (X_PIO - 0.3, ROW_IO), (x1_io, ROW_IO), (rnd(x1_io - (ROW_IO - STR_IO)), STR_IO),
                       (x2_io, STR_IO), (rnd(x2_io - (W_IO - STR_IO)), W_IO), (XW_IO + 0.6, W_IO), (XW_IO, W_IO + 0.6),
                       (XW_IO, 139.68), (XW_IO + 0.6, 140.28), (153.22, 140.28)])

# ------------------------------------------------------------------ USB pair (top side, 0.3 mm wide, 0.2 mm apart)
YA = 158.40
path('USB_D_P', 'F.Cu', [(191.35, 137.14), (191.35, 138.90), (X_DP, rnd(138.90 + X_DP - 191.35)), (X_DP, YA), (192.00, rnd(YA + X_DP - 192.00)),
                         (192.00, 162.30)], 0.3)
YB = rnd(YA + 0.5 * S2 - 0.5)
path('USB_D_N', 'F.Cu', [(193.25, 137.14), (193.25, 138.20), (X_DN, 138.35), (X_DN, YB), (192.50, rnd(YB + X_DN - 192.50)), (192.50, 162.70)], 0.3)

# ------------------------------------------------------------------ GPIO_VUSB_SENSE: crosses on In2
path('GPIO_VUSB_SENSE', 'F.Cu', [(190.32, 156.15), (190.65, 156.15), (190.80, 156.30), (191.10, 156.30)])
via('GPIO_VUSB_SENSE', (191.10, 156.30))
path('GPIO_VUSB_SENSE', 'In2.Cu', [(191.10, 156.30), (194.30, 156.30)])
via('GPIO_VUSB_SENSE', (194.30, 156.30))
path('GPIO_VUSB_SENSE', 'F.Cu', [(194.30, 156.30), (193.90, 155.90), (193.90, 150.29), (195.70, 148.49), (197.60, 148.49)])

# ------------------------------------------------------------------ divider taps to J301 (back side)
XB, XA = 192.00, 193.40                         # the two lanes east of the MCU
# VSWB_SENSE: R344 pad 2 -> east of R344 -> lane -> row -> pin 3. No via.
path('VSWB_SENSE', 'B.Cu', [(191.75, 168.11), (192.15, 168.11), (192.45, 167.81), (192.45, 165.55), (XB, 165.10), (XB, 141.05),
                            (189.85, 138.90), (186.18, 138.90), (183.70, 136.42)])
# VSWA_SENSE: the hop over VSWB_CMP on the top side is 0.65 mm longer than before, then lane and one diagonal into pin 1
path('VSWA_SENSE', 'F.Cu', [(192.40, 165.20), (193.05, 165.20)])
via('VSWA_SENSE', (193.05, 165.20))
path('VSWA_SENSE', 'B.Cu', [(193.05, 165.20), (192.90, 165.05), (192.90, 160.40), (XA, 159.90), (XA, rnd(136.42 + XA - 188.78)), (188.78, 136.42)])

# ------------------------------------------------------------------ resistor strip of J301 (top side)
for x, name in ((171.00, 'HRTIM1_FLT4'), (173.54, 'HRTIM1_FLT3'), (176.08, 'ZVS_B_IN'), (178.62, 'ZVS_A_IN')):
    path(name, 'F.Cu', [(x, Y_S), (x, 136.42)])                     # pad that faces the pin -> pin
path('HRTIM1_FLT4', 'F.Cu', [(169.73, Y_S), (171.00, Y_S)])           # pull-up beside the pull-down
path('HRTIM1_FLT3', 'F.Cu', [(172.27, Y_S), (173.54, Y_S)])
Y_V = 132.20
for x, name in ((169.73, '+3V3'), (171.00, 'GND'), (172.27, '+3V3'), (173.54, 'GND'), (174.81, 'GND'), (177.35, 'GND')):
    path(name, 'F.Cu', [(x, Y_N), (x, Y_V)], 0.25)                  # pad -> via into the plane
    via(name, (x, Y_V))

# ------------------------------------------------------------------ HRTIM1_FLT3: new entry from J301 pin 7 (back side)
path('HRTIM1_FLT3', 'B.Cu', [(173.54, 136.42), (169.73, 140.23), (169.73, 140.57)])

r.save()
json.dump({k: [list(q) for q in v] for k, v in r.reg.items()}, open(regfile, 'w'))
print('written', dst)

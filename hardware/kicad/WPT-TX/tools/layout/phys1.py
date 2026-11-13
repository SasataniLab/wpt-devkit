#!/usr/bin/env python3
"""Hand-routed, physics-driven version of the nets that matter: gate signals, comparator sense lines, sense dividers.

usage: phys1.py BOARD_IN BOARD_OUT     (BOARD_IN: the routed board with these nets and the nets they displace stripped)

Reasoning (4-layer board: F.Cu / In1 = unbroken GND / In2 = +3V3 plane under the MCU, +5V plane south of y = 163 / B.Cu):
  * A trace on F.Cu returns its current in the GND plane 0.2 mm below it, everywhere. A trace on B.Cu returns it in
    In2, which is split between +3V3 and +5V just south of the MCU. The four gate signals therefore leave the MCU
    on F.Cu, cross that split on F.Cu, and only then go down to B.Cu, where the +5V plane is continuous to the drivers.
  * The two signals of a half-bridge leg run side by side and end up the same length; the two legs are kept apart.
  * The comparator sense lines run on the other side of both planes from the gate signals.
  * The switch-node dividers are compact: bottom resistor and series resistor sit at the tap, and the part of the
    net that carries the full switch-node swing is as short as the parts allow.
"""
import math
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
V2 = lambda x, y: pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
T, VK = R.Router.tkey, R.Router.vkey


def net(short):
    full = [str(n) for n in b.GetNetsByName().asdict().keys() if str(n).split('/')[-1] == short]
    assert len(full) == 1, (short, full)
    return full[0]


def box_keys(short, layer, box, both=True):
    x0, y0, x1, y1 = box
    ins = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    out = set()
    for t in b.GetTracks():
        n = t.GetNetname()
        if n.split('/')[-1] != short:
            continue
        if t.GetClass() == 'PCB_VIA':
            if layer == 'VIA' and ins(P(t.GetPosition())):
                out.add(VK(n, P(t.GetPosition())))
        elif b.GetLayerName(t.GetLayer()) == layer:
            a, e = P(t.GetStart()), P(t.GetEnd())
            if (ins(a) and ins(e)) if both else (ins(a) or ins(e)):
                out.add(T(n, layer, a, e))
    return out


def place(ref, x=None, y=None, drot=0.0):
    fp = b.FindFootprintByReference(ref)
    if x is not None:
        fp.SetPosition(V2(x, y))
    if drot:
        fp.SetOrientationDegrees(fp.GetOrientationDegrees() + drot)
    return {p.GetNumber(): P(p.GetPosition()) for p in fp.Pads()}


kill = set()
kill.add(VK('GND', (184.25, 163.8)))                                   # stitching via in the path of the gate trunk
kill.add(VK('GND', (186.2, 157.7)))                                    # pin 47 ground via: moves above C3
kill |= box_keys('GND', 'F.Cu', (186.1, 157.6, 187.25, 158.9))
kill |= box_keys('GND', 'B.Cu', (186.1, 157.5, 187.0, 157.9))
kill.add(VK('GND', (188.9, 169.35)))                                   # ground via of R342 at its old place
kill |= box_keys('GND', 'B.Cu', (188.8, 168.6, 189.0, 169.45))
kill |= box_keys('OutB', 'B.Cu', (191.8, 168.2, 193.75, 170.3))         # old feed to R341 / C339
kill |= box_keys('L_Sig2', 'B.Cu', (191.7, 174.3, 192.1, 175.5))       # link between the pads that swap sides
kill |= box_keys('L_Sig1', 'B.Cu', (191.4, 190.9, 193.4, 193.7))
clk = net('Net-(U301-A)')
kill |= {T(clk, 'F.Cu', (188.85, 164.5), (188.25, 163.9)), T(clk, 'F.Cu', (188.15, 163.8), (188.15, 171.2))}
kill |= box_keys('Net-(U301-A)', 'F.Cu', (188.1, 163.75, 188.3, 163.95))
for t in b.GetTracks():                                                # the clock's east-west run ends a little earlier
    if t.GetClass() != 'PCB_VIA' and t.GetNetname() == clk and {P(t.GetStart()), P(t.GetEnd())} == {(195.1, 164.5), (188.85, 164.5)}:
        (t.SetEnd if P(t.GetEnd()) == (188.85, 164.5) else t.SetStart)(V2(188.75, 164.5))

# --- parts: compact leg-B divider, and link resistors turned so that the MCU signal reaches its pad from the west
r341 = place('R341', drot=180.0)
c339 = place('C339', drot=180.0)
r342 = place('R342', 190.45, 169.0, 180.0)
r344 = place('R344', 191.75, 167.6, 90.0)
if r344['2'][1] < r344['1'][1]:                                        # tap pad has to be the lower one
    r344 = place('R344', drot=180.0)
r329 = place('R329', drot=180.0)
r323 = place('R323', drot=180.0)
p320, p321 = b.FindFootprintByReference('R320').GetPosition(), b.FindFootprintByReference('R321').GetPosition()
x320, y320, x321, y321 = p320.x / MM, p320.y / MM, p321.x / MM, p321.y / MM
r320 = place('R320', x321, y321)
r321 = place('R321', x320, y320)
for k, v in (('R341', r341), ('C339', c339), ('R342', r342), ('R344', r344), ('R329', r329), ('R323', r323), ('R320', r320), ('R321', r321)):
    print(k, v)
pcbnew.SaveBoard(dst, b)
names = {s: net(s) for s in ('HRTIM1_CHC1', 'HRTIM1_CHC2', 'HRTIM1_CHD1', 'HRTIM1_CHD2', 'VSWA_CMP', 'VSWB_CMP', 'VSWB_SENSE', 'OutB', 'L_Sig1', 'L_Sig2',
                             'TIM3_CH1_ENCODER', 'TIM3_CH2_ENCODER', 'SCL', 'SDA', 'Net-(U301-A)')}
del b
print('removed', rip_text(dst, kill), 'pieces')

r = R.Router(dst)
r._fixed = True
F = lambda n, pts, w=0.2: [r.add_track(n, 'F.Cu', p, q, w) for p, q in zip(pts, pts[1:])]
B = lambda n, pts, w=0.2: [r.add_track(n, 'B.Cu', p, q, w) for p, q in zip(pts, pts[1:])]
Vi = lambda n, c: r.add_via(n, c)
N = names

# ---------------------------------------------------------------- inside the MCU pad ring, south side
Vi('GND', (186.9, 156.9)); F('GND', [(187.15, 158.825), (187.1, 158.7), (187.1, 157.4), (186.9, 157.2), (186.9, 156.9)]); B('GND', [(186.9, 156.9), (186.92, 157.7)], 0.25)
for n, stub, via, lane in (
        ('TIM3_CH1_ENCODER', [(182.65, 158.825), (182.5, 158.6)], (182.5, 158.25), 160.8),
        ('TIM3_CH2_ENCODER', [(183.15, 158.825)], (183.15, 157.3), 161.3),
        ('SCL', [(183.65, 158.825), (183.75, 158.6)], (183.75, 158.25), 161.8),
        ('SDA', [(184.15, 158.825), (184.15, 158.75), (184.55, 158.35)], (184.65, 158.25), 162.3)):
    F(N[n], stub + [via]); Vi(N[n], via)
    B(N[n], [via, (via[0], lane - 0.25), (via[0] - 0.25, lane), (179.6, lane)])
F(N['VSWA_CMP'], [(181.65, 148.975), (181.65, 149.2), (181.85, 149.4), (181.85, 156.45), (182.05, 156.65), (185.0, 156.65), (185.3, 156.95), (185.3, 157.2)]); Vi(N['VSWA_CMP'], (185.3, 157.2))
B(N['VSWA_CMP'], [(185.3, 157.2), (185.3, 160.7)])
F(N['VSWB_CMP'], [(183.65, 148.975), (183.65, 149.1), (183.9, 149.35), (183.9, 155.95), (184.1, 156.15), (185.6, 156.15), (185.9, 156.45)]); Vi(N['VSWB_CMP'], (185.9, 156.45))
# comparator line of leg B: on the back all the way, under the gate signals (two planes in between), to the series resistor at the tap
B(N['VSWB_CMP'], [(185.9, 156.45), (185.9, 161.5), (189.3, 164.9), (191.2, 164.9), (191.75, 165.45), r344['1']])

# ---------------------------------------------------------------- gate signals: top side from the pads, across the plane split
F(N['HRTIM1_CHC1'], [(180.65, 160.325), (180.65, 161.0), (185.8, 166.15), (185.8, 169.25), (185.95, 169.4), (185.95, 169.6)]); Vi(N['HRTIM1_CHC1'], (185.95, 169.6))
F(N['HRTIM1_CHC2'], [(181.15, 160.325), (181.15, 160.85), (186.45, 166.15), (186.45, 168.2)]); Vi(N['HRTIM1_CHC2'], (186.45, 168.2))
F(N['HRTIM1_CHD1'], [(181.65, 160.325), (181.65, 160.7), (182.2, 161.25), (183.1, 161.25), (187.1, 165.25), (187.1, 168.9)]); Vi(N['HRTIM1_CHD1'], (187.1, 168.9))
F(N['HRTIM1_CHD2'], [(182.15, 160.325), (182.15, 160.5), (182.4, 160.75), (183.35, 160.75), (187.75, 165.15), (187.75, 169.6)]); Vi(N['HRTIM1_CHD2'], (187.75, 169.6))
# ... then on the back, under the unbroken +5V plane, each leg as a pair
B(N['HRTIM1_CHD2'], [(187.75, 169.6), (187.75, 169.85), (191.4, 173.5), (191.45, 173.55), (192.91, 173.55), (192.91, 172.9)])
B(N['HRTIM1_CHD1'], [(187.1, 168.9), (187.1, 170.0), (191.2, 174.1), (191.4, 174.3), r329['2']])
B(N['HRTIM1_CHC2'], [(186.45, 168.2), (185.2, 168.2), (184.85, 168.55), (184.85, 190.85), (185.3, 191.3), r323['2']])
B(N['HRTIM1_CHC1'], [(185.95, 169.6), (185.45, 170.1), (185.45, 190.2), (185.85, 190.6), (192.7, 190.6), (192.91, 190.39), r320['2']])
# driver-input nodes on the back
B(N['L_Sig2'], [r329['1'], (192.7, 174.62), (192.1, 175.28), (191.89, 175.6)])
B(N['L_Sig1'], [r323['1'], (192.7, 191.62), (192.1, 192.28), (191.89, 192.6)]); B(N['L_Sig1'], [(191.89, 192.6), (192.3, 193.2), (193.1, 193.5)])
# legacy clock moved 0.3 mm east to give the gate signals their lanes (only one of the two is ever fitted)
F(N['Net-(U301-A)'], [(188.75, 164.5), (188.45, 164.8), (188.45, 170.9), (188.15, 171.2)])

# ---------------------------------------------------------------- leg-B switch-node divider
B(N['OutB'], [(193.95, 168.85), (193.5, 169.0), r341['1']]); B(N['OutB'], [r341['1'], c339['1']])
B(N['VSWB_SENSE'], [r341['2'], c339['2']]); B(N['VSWB_SENSE'], [r341['2'], r342['1']]); B(N['VSWB_SENSE'], [r344['2'], (191.9, 168.5), r341['2']])
B('GND', [r342['2'], (189.94, 169.5), (190.35, 169.9), (191.075, 169.9)], 0.25)
r.save()
print('written', dst)

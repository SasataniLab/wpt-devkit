#!/usr/bin/env python3
"""USB-C receptacle J5 (GCT USB4105): no top-side copper under the metal shell.

usage: usbfix.py BOARD_IN REG_IN.json BOARD_OUT REG_OUT.json

GCT's drawing (rev B4) marks no keep-out, but its bottom view shows what touches the board: the stainless shell from the
mouth to about 0.47 mm in front of the two locating pegs, and the plastic housing from there back to the pads. A track
under the shell is insulated from it (the shell is GND) by solder mask alone.
  * a rule area on F.Cu (no tracks, no vias) covers the part under the shell; KiCad's DRC and the router both honour it
  * the two links that have to run in front of the pad row (VBUS A4/B9 - A9/B4, D- A7 - B7) move into the 0.9 mm strip
    under the plastic housing; the VBUS link also gets its 0.25 mm distance from the peg holes (it had 0.215 mm)
  * auto-routed nets that ran under the shell are taken out of the board here and routed again afterwards
"""
import json
import shutil
import sys

import pcbnew

import router as R
from nego import rip_text

R.DEFAULT_CORRIDORS = ()
MM = 1e6
src, regin, dst, regout = sys.argv[1:5]
shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)
P = lambda v: (round(v.x / MM, 3), round(v.y / MM, 3))
T = R.Router.tkey
net = lambda s: [str(n) for n in b.GetNetsByName().asdict().keys() if str(n).split('/')[-1] == s][0]
N = {s: net(s) for s in ('VBUS', 'USB_D_N', 'SWDIO', 'SCL_3.3V')}
j5 = b.FindFootprintByReference('J5')
peg_y = [P(p.GetPosition())[1] for p in j5.Pads() if p.GetNumber() == '' ][0]
SHELL = (189.3, 134.9, 198.3, round(peg_y - 0.43, 3))              # x0, y0, x1, y1: 0.04 mm short of where the shell ends


def tup(q):
    return tuple(tuple(x) if isinstance(x, list) else x for x in q)


reg = {n: [tup(q) for q in ks] for n, ks in json.load(open(regin)).items()}
kill = {T(N['VBUS'], 'F.Cu', (191.55, 140.6), (196.05, 140.6)), T(N['VBUS'], 'F.Cu', (191.55, 142.2), (191.55, 140.6)),
        T(N['VBUS'], 'F.Cu', (196.05, 140.6), (196.05, 142.2)),
        T(N['USB_D_N'], 'F.Cu', (193.55, 141.35), (194.55, 141.35)), T(N['USB_D_N'], 'F.Cu', (193.55, 142.1), (193.55, 141.35)),
        T(N['USB_D_N'], 'F.Cu', (194.55, 141.35), (194.55, 142.1))}
ripped = []
for s in ('SWDIO', 'SCL_3.3V'):
    kill |= set(reg.get(N[s], []))
    reg[N[s]] = []
    ripped.append(s)

z = pcbnew.ZONE(b)
z.SetIsRuleArea(True)
z.SetLayer(pcbnew.F_Cu)
z.SetZoneName('J5 shell: no top copper')
z.SetDoNotAllowTracks(True)
z.SetDoNotAllowVias(True)
z.SetDoNotAllowPads(False)
z.SetDoNotAllowFootprints(False)
(z.SetDoNotAllowZoneFills if hasattr(z, 'SetDoNotAllowZoneFills') else z.SetDoNotAllowCopperPour)(False)
o = z.Outline()
o.NewOutline()
for x, y in ((SHELL[0], SHELL[1]), (SHELL[2], SHELL[1]), (SHELL[2], SHELL[3]), (SHELL[0], SHELL[3])):
    o.Append(int(round(x * MM)), int(round(y * MM)))
b.Add(z)
pcbnew.SaveBoard(dst, b)
del b
print('removed', rip_text(dst, kill), 'of', len(kill), 'pieces; rule area', SHELL)

r = R.Router(dst, reg=reg)
r._fixed = True
F = lambda n, pts, w=0.2: [r.add_track(N[n], 'F.Cu', p, q, w) for p, q in zip(pts, pts[1:])]
yv = round(peg_y - 0.28, 3)             # VBUS link: 0.1 mm clear of the rule area, 0.25 mm from the D- link
yd = round(peg_y + 0.17, 3)             # D- link: 0.23 mm from the pads it passes
F('VBUS', [(191.6, 142.2), (191.6, yv + 0.2), (191.8, yv), (195.8, yv), (196.0, yv + 0.2), (196.0, 142.2)])
F('USB_D_N', [(193.55, 142.1), (193.55, yd), (194.55, yd), (194.55, 142.1)])
r.save()
json.dump({n: [list(q) for q in ks] for n, ks in r.reg.items()}, open(regout, 'w'))
print('written', dst, 'VBUS link y', yv, 'D- link y', yd, '; to route again:', ripped)

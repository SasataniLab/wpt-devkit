#!/usr/bin/env python3
"""Display SPI: MOSI straight to the MCU instead of 86 mm round the board. usage: phys5.py BOARD_IN REG_IN.json BOARD_OUT REG_OUT.json

The three SPI signals sit in opposite order on the display header J2 and on the MCU, so they have to cross each other.
The router had solved that by sending MOSI the long way (round the encoder and under the slide switch). There is a
2.25 mm wide passage on the back side between the encoder's mounting lug and a via of HV_SW_STATE; it holds two tracks
side by side with the clock (top side) and SWCLK (top side) crossing above them:
  * MOSI comes down from its header pin on the back, takes the west lane, goes up through one via south of SWCLK and
    runs on the top side beside MISO to its pin (17 mm, one via)
  * HRTIM1_FLT3, which used that passage alone, enters between the header pins J2.5 / J2.6 instead of J2.6 / J2.7,
    takes the east lane and joins its old route at the via (169.95, 150.25); everything south of that stays
MISO, the clock and all other nets are untouched.
"""
import json
import shutil
import sys

import pcbnew

import router as R
from nego import rip_text

R.DEFAULT_CORRIDORS = ()
src, regin, dst, regout = sys.argv[1:5]
shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)
net = lambda s: [str(n) for n in b.GetNetsByName().asdict().keys() if str(n).split('/')[-1] == s][0]
mosi, flt3 = net('SPI1_MOSI_DISP'), net('HRTIM1_FLT3')
del b
T = R.Router.tkey
tup = lambda q: tuple(tuple(x) if isinstance(x, list) else x for x in q)
reg = {n: [tup(q) for q in ks] for n, ks in json.load(open(regin)).items()}
kill = set(reg.get(mosi, []))                                   # all auto-routed copper of MOSI
old = [(172.9, 139.55), (172.3, 141.35), (172.3, 142.35), (169.9, 144.75), (169.95, 150.25)]
kill |= {T(flt3, 'B.Cu', p, q) for p, q in zip(old, old[1:])}   # north part of FLT3
n = rip_text(dst, kill)
print('removed', n, 'of', len(kill), 'pieces')
reg = {k: [q for q in v if q not in kill] for k, v in reg.items()}
r = R.Router(dst, reg=reg)
r._fixed = True
B = lambda nt, pts: [r.add_track(nt, 'B.Cu', p, q, 0.2) for p, q in zip(pts, pts[1:])]
F = lambda nt, pts: [r.add_track(nt, 'F.Cu', p, q, 0.2) for p, q in zip(pts, pts[1:])]
B(mosi, [(168.46, 141.5), (168.46, 142.36), (169.95, 143.85), (169.95, 147.6), (169.8, 147.75), (169.8, 148.2)])
r.add_via(mosi, (169.8, 148.2))
F(mosi, [(169.8, 148.2), (171.1, 149.75), (173.1, 149.75), (175.05, 151.7), (176.55, 151.7), (176.9, 152.05), (177.0, 152.05)])
B(flt3, [(170.25, 140.05), (169.73, 140.57), (169.73, 142.45), (170.45, 143.17), (170.45, 149.3), (169.95, 149.8), (169.95, 150.25)])
r.save()
json.dump({k: [list(q) for q in v] for k, v in r.reg.items()}, open(regout, 'w'))
print('written', dst)

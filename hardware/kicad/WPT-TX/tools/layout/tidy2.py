#!/usr/bin/env python3
"""SWDIO along the top edge: back to 0.9 mm from the board outline. usage: tidy2.py BOARD REG.json  (changed in place)

The only free way from the SWD header J3 to the east side of the MCU is the strip between the board edge and the
header rows. The router used all of it (copper 0.6 mm from the edge); the track is put as close to the header pads
as the clearance allows instead, which keeps it over the ground plane rather than at its rim.
"""
import json
import sys

import pcbnew

import router as R
from nego import rip_text

R.DEFAULT_CORRIDORS = ()
path, regfile = sys.argv[1:3]
b = pcbnew.LoadBoard(path)
net = [str(n) for n in b.GetNetsByName().asdict().keys() if str(n).split('/')[-1] == 'SWDIO'][0]
P = lambda v: (round(v.x / 1e6, 3), round(v.y / 1e6, 3))
T = R.Router.tkey
kill = set()
for t in b.GetTracks():
    if t.GetClass() != 'PCB_VIA' and t.GetNetname() == net and b.GetLayerName(t.GetLayer()) == 'F.Cu':
        a, e = P(t.GetStart()), P(t.GetEnd())
        if min(a[1], e[1]) < 135.9 and 159.0 < min(a[0], e[0]) and max(a[0], e[0]) < 187.2:
            kill.add(T(net, 'F.Cu', a, e))
            print('replace', a, e)
del b
tup = lambda q: tuple(tuple(x) if isinstance(x, list) else x for x in q)
reg = {n: [tup(q) for q in ks if tup(q) not in kill] for n, ks in json.load(open(regfile)).items()}
assert rip_text(path, kill) == len(kill) == 3
r = R.Router(path, reg=reg)
r._fixed = True
pts = [(159.4, 136.05), (159.45, 136.0), (185.0, 136.0), (185.4, 136.4), (185.4, 136.85), (187.05, 138.5), (187.05, 138.55)]
for p, q in zip(pts, pts[1:]):
    r.add_track(net, 'F.Cu', p, q, 0.2)
r.save()
json.dump({n: [list(q) for q in ks] for n, ks in r.reg.items()}, open(regfile, 'w'))

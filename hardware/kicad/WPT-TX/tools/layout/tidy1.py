#!/usr/bin/env python3
"""Local hand corrections after the fill-in routing. usage: tidy1.py BOARD REG.json   (both changed in place)

SDA: the router joined the hand-made lane at its east end and then ran its own track 0.35 mm beside it, along the edge
of the +3V3 plane. The lane (0.7 mm inside the plane edge) is extended to the via instead and the parallel track removed.
"""
import json
import sys

import pcbnew

import router as R
from nego import rip_text

R.DEFAULT_CORRIDORS = ()
path, regfile = sys.argv[1:3]
b = pcbnew.LoadBoard(path)
net = lambda s: [str(n) for n in b.GetNetsByName().asdict().keys() if str(n).split('/')[-1] == s][0]
sda = net('SDA')
del b
T = R.Router.tkey
kill = {T(sda, 'B.Cu', (171.9, 162.65), (183.95, 162.65)), T(sda, 'B.Cu', (183.95, 162.65), (184.25, 162.35))}
tup = lambda q: tuple(tuple(x) if isinstance(x, list) else x for x in q)
reg = {n: [tup(q) for q in ks if tup(q) not in kill] for n, ks in json.load(open(regfile)).items()}
n = rip_text(path, kill)
assert n == len(kill), (n, len(kill))
r = R.Router(path, reg=reg)
r._fixed = True
pts = [(179.6, 162.3), (172.25, 162.3), (171.9, 162.65)]
for p, q in zip(pts, pts[1:]):
    r.add_track(sda, 'B.Cu', p, q, 0.2)
r.save()
json.dump({n: [list(q) for q in ks] for n, ks in r.reg.items()}, open(regfile, 'w'))
print('SDA lane extended')

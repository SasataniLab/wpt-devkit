#!/usr/bin/env python3
"""HRTIM1_EEV1 away from the leg-A sense line. usage: tidy3.py BOARD REG.json  (changed in place)

EEV1 carries the output of an external zero-voltage comparator back to the MCU; VSWA_SENSE is the input of that same
comparator. East of the MCU the router had put the two side by side (0.3 mm gap for 2.5 mm, then 0.5 mm apart for
another 2 mm): output next to input. EEV1's north-going part moves 0.8 mm west, to 1.05 mm from the sense line.
"""
import json
import sys

import pcbnew

import router as R
from nego import rip_text

R.DEFAULT_CORRIDORS = ()
path, regfile = sys.argv[1:3]
b = pcbnew.LoadBoard(path)
net = [str(n) for n in b.GetNetsByName().asdict().keys() if str(n).split('/')[-1] == 'HRTIM1_EEV1'][0]
del b
T = R.Router.tkey
old = [(191.1, 155.15), (192.45, 155.15), (192.95, 154.65), (192.95, 151.2), (191.3, 149.55)]
new = [(191.1, 155.15), (191.75, 155.15), (192.15, 154.75), (192.15, 150.4), (191.3, 149.55)]
kill = {T(net, 'B.Cu', p, q) for p, q in zip(old, old[1:])}
tup = lambda q: tuple(tuple(x) if isinstance(x, list) else x for x in q)
reg = {n: [tup(q) for q in ks if tup(q) not in kill] for n, ks in json.load(open(regfile)).items()}
n = rip_text(path, kill)
assert n == len(kill), (n, len(kill))
r = R.Router(path, reg=reg)
r._fixed = True
for p, q in zip(new, new[1:]):
    r.add_track(net, 'B.Cu', p, q, 0.2)
r.save()
json.dump({n: [list(q) for q in ks] for n, ks in r.reg.items()}, open(regfile, 'w'))
print('EEV1 moved')

#!/usr/bin/env python3
"""HV_EN_MCU: its via under the slide switch sat 0.05 mm from the inner face of the cover wall (via pad edge), inside the
wall band. It moves 0.54 mm diagonally inwards, to under the plastic base, 0.2 mm clear of USART1_TX. usage: hv_en_via.py BOARD REG.json"""
import json
import sys

import router as R
from nego import rip_text

R.DEFAULT_CORRIDORS = ()
path, regfile = sys.argv[1:3]
short = lambda n: n.split('/')[-1]
tup = lambda q: tuple(tuple(x) if isinstance(x, list) else x for x in q)
REG = {n: [tup(q) for q in ks] for n, ks in json.load(open(regfile)).items()}
net = [n for n in REG if short(n) == 'HV_EN_MCU'][0]
old = R.Router.tkey(net, 'B.Cu', (156.9, 156.25), (155.3, 155.85))
print('removed', rip_text(path, {old}))
REG[net] = [k for k in REG[net] if k != old]
r = R.Router(path, reg=REG)
r._fixed = True
r.add_track(net, 'F.Cu', (156.9, 156.25), (156.52, 156.63), 0.2)
r.add_via(net, (156.52, 156.63))
r.add_track(net, 'B.Cu', (156.52, 156.63), (155.74, 155.85), 0.2)
r.add_track(net, 'B.Cu', (155.74, 155.85), (155.3, 155.85), 0.2)
r.save()
json.dump({k: [list(q) for q in v] for k, v in r.reg.items()}, open(regfile, 'w'))

#!/usr/bin/env python3
"""Add one hand-made (fixed) track. usage: stub.py BOARD REG.json NET LAYER x1,y1 x2,y2 [x3,y3 ...] [--width W]"""
import json
import sys

import pcbnew

import router as R

R.DEFAULT_CORRIDORS = ()
args = [a for a in sys.argv[1:] if not a.startswith('--')]
w = float(sys.argv[sys.argv.index('--width') + 1]) if '--width' in sys.argv else 0.2
if '--width' in sys.argv:
    args.remove(sys.argv[sys.argv.index('--width') + 1])
path, regfile, name, layer = args[:4]
pts = [tuple(float(v) for v in a.split(',')) for a in args[4:]]
tup = lambda q: tuple(tuple(x) if isinstance(x, list) else x for x in q)
reg = {n: [tup(q) for q in ks] for n, ks in json.load(open(regfile)).items()}
r = R.Router(path, reg=reg)
net = [n for n in r.nets if n.split('/')[-1] == name][0]
r._fixed = True
for p, q in zip(pts, pts[1:]):
    r.add_track(net, layer, p, q, w)
r.save()
json.dump({n: [list(q) for q in ks] for n, ks in r.reg.items()}, open(regfile, 'w'))
print('added', len(pts) - 1, 'segment(s) on', net)

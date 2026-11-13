#!/usr/bin/env python3
"""Which auto-routed nets stand in the way of an open connection? usage: whyblocked.py BOARD REG.json NET [inner]"""
import json
import math
import sys

import router as R

R.DEFAULT_CORRIDORS = ()
path, regfile, name = sys.argv[1:4]
inner = len(sys.argv) > 4
tup = lambda q: tuple(tuple(x) if isinstance(x, list) else x for x in q)
REG = {n: [tup(k) for k in ks] for n, ks in json.load(open(regfile)).items()}
short = lambda n: n.split('/')[-1]
txt = R.run_drc(path, path.replace('.kicad_pcb', '_why.rpt'))
pairs = [(a, c) for a, c in R.parse_unconnected(txt) if short(a['net']) == name and 'Zone' not in (a['kind'], c['kind'])]
r = R.Router(path, reg=REG, protected=set())
for a, c in pairs:
    A, B = (a['x'], a['y'], a['layers']), (c['x'], c['y'], c['layers'])
    print('open:', A, B)
    for m in (6.0, 15.0, 40.0):
        hit = r.route(a['net'], A, B, margin=m, max_nodes=12_000_000, soft=True, inner=inner)
        print('  margin', m, '->', sorted(short(h) for h in hit) if hit not in (False, True) else hit)
        if hit not in (False,):
            break

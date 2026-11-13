#!/usr/bin/env python3
"""Rip up the auto-routed copper of the named nets and route them again, one after the other.

usage: reroute.py BOARD REG.json NET [NET ...] [--inner]     (NET = last part of the net name)
"""
import gc
import json
import math
import shutil
import sys

import router as R
from nego import rip_text, SLOW, PROT

R.DEFAULT_CORRIDORS = ()
path, regfile = sys.argv[1:3]
names = [a for a in sys.argv[3:] if not a.startswith('--')]
INNER = '--inner' in sys.argv


def tup(k):
    return tuple(tuple(x) if isinstance(x, list) else x for x in k)


REG = {net: [tup(k) for k in ks] for net, ks in json.load(open(regfile)).items()}
for name in names:
    net = [n for n in REG if n.split('/')[-1] == name][0]
    shutil.copy(path, path + '.rr.bak')
    old = REG[net]
    rip_text(path, set(old))
    REG[net] = []
    txt = R.run_drc(path, path.replace('.kicad_pcb', '_rr.rpt'))
    pairs = sorted([(a, c) for a, c in R.parse_unconnected(txt) if a['net'] == net],
                   key=lambda p: math.dist((p[0]['x'], p[0]['y']), (p[1]['x'], p[1]['y'])))
    r = R.Router(path, reg=REG, protected=PROT)
    ok = bool(pairs)
    for a, c in pairs:
        A, B = (a['x'], a['y'], a['layers']), (c['x'], c['y'], c['layers'])
        if not any(r.route(net, A, B, margin=m, max_nodes=8_000_000, inner=INNER and any(k in net for k in SLOW)) for m in (4.0, 10.0, 30.0)):
            ok = False
            break
    if ok:
        r.save()
        print(name, 're-routed,', len(pairs), 'connections')
    else:
        shutil.copy(path + '.rr.bak', path)
        REG[net] = old
        print(name, 'FAILED, left as it was')
    del r
    gc.collect()
    json.dump(REG, open(regfile, 'w'), default=list)

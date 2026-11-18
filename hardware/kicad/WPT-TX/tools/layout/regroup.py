#!/usr/bin/env python3
"""Rip up a group of auto-routed nets together and route them again in the given order; undo if any of them fails
or if the group as a whole gets longer.

usage: regroup.py BOARD REG.json NET [NET ...] [--inner] [--force]
"""
import collections
import gc
import json
import math
import shutil
import sys

import pcbnew

import router as R
from nego import rip_text, SLOW, PROT

R.DEFAULT_CORRIDORS = ()
path, regfile = sys.argv[1:3]
names = [a for i, a in enumerate(sys.argv[3:], 3) if not a.startswith('--') and sys.argv[i - 1] != '--via-cost']
INNER = '--inner' in sys.argv
VIA_COST = float(sys.argv[sys.argv.index('--via-cost') + 1]) if '--via-cost' in sys.argv else 3.0
MM = 1e6


def tup(k):
    return tuple(tuple(x) if isinstance(x, list) else x for x in k)


def cost(nets):
    b = pcbnew.LoadBoard(path)
    c = collections.defaultdict(float)
    for t in b.GetTracks():
        n = t.GetNetname()
        if n in nets:
            c[n] += 4.0 if t.GetClass() == 'PCB_VIA' else (2.0 if b.GetLayerName(t.GetLayer()) == 'In2.Cu' else 1.0) * t.GetLength() / MM
    del b
    gc.collect()
    return c


REG = {net: [tup(k) for k in ks] for net, ks in json.load(open(regfile)).items()}
nets = [[n for n in REG if n.split('/')[-1] == name][0] for name in names]
before = cost(nets)
shutil.copy(path, path + '.grp.bak')
old = {n: REG[n] for n in nets}
rip_text(path, set(k for n in nets for k in REG[n]))
for n in nets:
    REG[n] = []
txt = R.run_drc(path, path.replace('.kicad_pcb', '_grp.rpt'))
allpairs = R.parse_unconnected(txt)
r = R.Router(path, reg=REG, protected=PROT)
ok = True
for net in nets:
    pairs = sorted([(a, c) for a, c in allpairs if a['net'] == net], key=lambda p: math.dist((p[0]['x'], p[0]['y']), (p[1]['x'], p[1]['y'])))
    for a, c in pairs:
        A, B = (a['x'], a['y'], a['layers']), (c['x'], c['y'], c['layers'])
        if not any(r.route(net, A, B, margin=m, max_nodes=8_000_000, via_cost=VIA_COST, inner=INNER and any(k in net for k in SLOW)) for m in (4.0, 10.0, 30.0)):
            ok = False
            print('   no path for', net.split('/')[-1])
            break
    if not ok:
        break
if ok:
    r.save()
del r
gc.collect()
after = cost(nets) if ok else None
if ok and (sum(after.values()) < sum(before.values()) or '--force' in sys.argv):
    print('kept:', {n.split('/')[-1]: (round(before[n], 1), round(after[n], 1)) for n in nets})
else:
    shutil.copy(path + '.grp.bak', path)
    for n in nets:
        REG[n] = old[n]
    print('undone', '' if not ok else {n.split('/')[-1]: (round(before[n], 1), round(after[n], 1)) for n in nets})
json.dump(REG, open(regfile, 'w'), default=list)

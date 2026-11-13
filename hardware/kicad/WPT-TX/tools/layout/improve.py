#!/usr/bin/env python3
"""Re-route one net at a time with everything else in place; keep the new route only when it is better.

usage: improve.py BOARD REG.json [sweeps] [--inner]

After the negotiated run every net is connected, but many took detours that were only needed while their
neighbours were still moving. Cost of a route = copper length + 4 mm per via + inner-layer length once more.
"""
import collections
import copy
import gc
import json
import math
import shutil
import sys
import time

import pcbnew

import router as R
from nego import rip_text, SLOW, PROT

R.DEFAULT_CORRIDORS = ()
path, regfile = sys.argv[1:3]
sweeps = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 1
INNER = '--inner' in sys.argv
MM = 1e6
FAST = ('HRTIM1_CH', 'VSWA', 'VSWB', 'HRTIM1_EEV', 'HRTIM1_FLT', 'SPI1', 'SWCLK', 'SWDIO', 'NRST')


def tup(k):
    return tuple(tuple(x) if isinstance(x, list) else x for x in k)


REG = {net: [tup(k) for k in ks] for net, ks in json.load(open(regfile)).items()}


def stats():
    b = pcbnew.LoadBoard(path)
    L = collections.defaultdict(float)
    for t in b.GetTracks():
        n = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            L[n] += 4.0
        else:
            f = 2.0 if b.GetLayerName(t.GetLayer()) == 'In2.Cu' else 1.0
            L[n] += f * t.GetLength() / MM
    del b
    gc.collect()
    return L


def order(cost):
    nets = [n for n in REG if n not in PROT and REG[n]]
    return sorted(nets, key=lambda n: (0 if any(k in n for k in FAST) else 1, -cost[n]))


bak = path + '.imp.bak'
for sw in range(sweeps):
    cost = stats()
    better = same = 0
    t0 = time.time()
    for net in order(cost):
        shutil.copy(path, bak)
        reg_bak = copy.deepcopy(REG.get(net, []))
        rip_text(path, set(REG.get(net, [])))
        REG[net] = []
        txt = R.run_drc(path, path.replace('.kicad_pcb', '_imp.rpt'))
        pairs = [(a, c) for a, c in R.parse_unconnected(txt) if a['net'] == net]
        r = R.Router(path, reg=REG, protected=PROT)
        ok = bool(pairs)
        fast = any(k in net for k in FAST)
        pairs.sort(key=lambda p: math.dist((p[0]['x'], p[0]['y']), (p[1]['x'], p[1]['y'])))
        for a, c in pairs:
            A, B = (a['x'], a['y'], a['layers']), (c['x'], c['y'], c['layers'])
            done = False
            for m in (4.0, 10.0, 30.0):
                if r.route(net, A, B, margin=m, max_nodes=8_000_000, via_cost=8.0 if fast else 4.0,
                           inner=INNER and any(k in net for k in SLOW)):
                    done = True
                    break
            if not done:
                ok = False
                break
        if ok:
            r.save()
        del r
        gc.collect()
        new = stats()[net] if ok else 1e9
        if ok and new < cost[net] - 0.5:
            better += 1
            print(f'  {net.split("/")[-1]:24} {cost[net]:6.1f} -> {new:6.1f}', flush=True)
            cost[net] = new
        else:
            shutil.copy(bak, path)
            REG[net] = reg_bak
            same += 1
        json.dump(REG, open(regfile, 'w'), default=list)
    print(f'sweep {sw}: {better} nets improved, {same} kept, {time.time() - t0:.0f} s', flush=True)
    if not better:
        break

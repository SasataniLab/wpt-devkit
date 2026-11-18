#!/usr/bin/env python3
"""Route the open connections of the named nets one by one.

usage: fillin.py BOARD REG.json NET[:opts] ...
opts: b = back side only (no vias), v = vias expensive, i = inner layer allowed,
      r = may push auto-routed nets aside; those are then routed again (without pushing anything) at the end
      k = stay out from under the MCU and away from the crystal, s = keep a distance from the analog sense lines,
      n = accept a legal path only within 10 mm of the box around its two ends (with r: rather push others aside than go round the board)
"""
import gc
import json
import math
import sys

import router as R
from nego import PROT, rip_text

R.DEFAULT_CORRIDORS = ()
path, regfile = sys.argv[1:3]
specs = [(a.split(':') + [''])[:2] for a in sys.argv[3:]]


def tup(k):
    return tuple(tuple(x) if isinstance(x, list) else x for x in k)


REG = {net: [tup(k) for k in ks] for net, ks in json.load(open(regfile)).items()}
short = lambda n: n.split('/')[-1]
import os
KEEP = set(os.environ.get('FILL_KEEP', '').split(',')) - {''}
PROT.update(n for n in REG if short(n) in KEEP)        # nets that must not be pushed aside
import numpy as np

# areas a sense line should not pass through: under the MCU and next to the crystal
AVOID = ((176.8, 146.9, 191.2, 161.0), (182.5, 142.8, 189.2, 147.0))


def keep_away(inner):
    def f(ix0, iy0, ix1, iy1):
        gy, gx = np.mgrid[iy0:iy1, ix0:ix1]
        wx, wy = R.X0 + gx * R.RES, R.Y0 + gy * R.RES
        m = np.zeros(wx.shape)
        for x0, y0, x1, y1 in AVOID:
            m += np.where((wx >= x0) & (wx <= x1) & (wy >= y0) & (wy <= y1), 6.0, 0.0)
        return [m, m] + ([m] if inner else [])
    return f


# nets an auto-routed track should not run beside (analog sense lines; a logic edge next to them shows up at the comparator)
SHY = ('VSWA_SENSE', 'VSWB_SENSE', 'VSWA_CMP', 'VSWB_CMP')
SHY_GAP = 0.6           # mm of copper-to-copper distance below which a cell costs four times as much


def shy(r, inner, base=None):
    from scipy import ndimage
    ids = [i for n, i in r.nets.items() if short(n) in SHY]
    pad = 20

    def f(ix0, iy0, ix1, iy1):
        out = base(ix0, iy0, ix1, iy1) if base else None
        res = []
        for k, l in enumerate(['F.Cu', 'B.Cu'] + (['In2.Cu'] if inner else [])):
            full = r.cv.arr(l)
            jy0, jx0 = max(0, iy0 - pad), max(0, ix0 - pad)
            a = full[jy0:iy1 + pad, jx0:ix1 + pad]
            mask = np.isin(a, ids)
            if mask.any():
                d = ndimage.distance_transform_edt(~mask) * R.RES
                pen = np.where(d < SHY_GAP + 0.1, 3.0, 0.0)[iy0 - jy0:iy0 - jy0 + (iy1 - iy0), ix0 - jx0:ix0 - jx0 + (ix1 - ix0)]
            else:
                pen = np.zeros((iy1 - iy0, ix1 - ix0))
            res.append(pen + (out[k] if out else 0.0))
        return res
    return f


queue = list(specs)
seen_rip = set()
while queue:
    name, opts = queue.pop(0)
    txt = R.run_drc(path, path.replace('.kicad_pcb', '_fill.rpt'))
    pairs = sorted([(a, c) for a, c in R.parse_unconnected(txt) if short(a['net']) == name and 'Zone' not in (a['kind'], c['kind'])],
                   key=lambda p: math.dist((p[0]['x'], p[0]['y']), (p[1]['x'], p[1]['y'])))
    if not pairs:
        print(name, ': nothing open', flush=True)
        continue
    r = R.Router(path, reg=REG, protected=PROT)
    ok = 0
    kw = dict(allow_via='b' not in opts, via_cost=12.0 if 'v' in opts else 3.0, inner='i' in opts)
    if 'k' in opts:
        kw['penal'] = keep_away('i' in opts)
    if 's' in opts and short(name) not in SHY:
        kw['penal'] = shy(r, 'i' in opts, kw.get('penal'))
    for a, c in pairs:
        net = a['net']
        A, B = (a['x'], a['y'], a['layers']), (c['x'], c['y'], c['layers'])
        # 'n': look for a legal path only near the straight line; a detour around the board then counts as "no path"
        legal = (4.0, 10.0) if 'n' in opts else (4.0, 10.0, 30.0, 60.0)
        done = any(r.route(net, A, B, margin=m, max_nodes=12_000_000, **kw) for m in legal)
        if not done and 'r' in opts:
            hit = False
            for m in (6.0, 15.0, 40.0):
                hit = r.route(net, A, B, margin=m, max_nodes=12_000_000, soft=True, **kw)
                if hit is not False:
                    break
            if hit:
                hit = {h for h in hit if h not in PROT}
                keys = set(k for h in hit for k in REG.get(h, []))
                r.save()
                del r
                gc.collect()
                rip_text(path, keys)
                for h in hit:
                    REG[h] = []
                    if short(h) not in seen_rip:
                        seen_rip.add(short(h))
                        queue.append((short(h), 'i' if any(k in h for k in ('USART1', 'SCL', 'SDA', 'ENCODER', 'HV_', 'J1-Pin_1', 'WLAT', 'ALERT', 'GPIO_DISP', 'GPIO_SW')) else ''))
                r = R.Router(path, reg=REG, protected=PROT)
                if 's' in opts and short(name) not in SHY:
                    kw['penal'] = shy(r, 'i' in opts, keep_away('i' in opts) if 'k' in opts else None)
                done = any(r.route(net, A, B, margin=m, max_nodes=12_000_000, **kw) for m in legal)
                print(f'   {name}: pushed aside {sorted(short(h) for h in hit)} -> {"ok" if done else "FAIL"}', flush=True)
        ok += bool(done)
    r.save()
    del r
    gc.collect()
    json.dump(REG, open(regfile, 'w'), default=list)
    print(f'{name}: {ok} of {len(pairs)} connections routed', flush=True)

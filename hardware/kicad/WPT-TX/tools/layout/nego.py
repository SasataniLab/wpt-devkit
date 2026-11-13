#!/usr/bin/env python3
"""Negotiated rip-up and re-route on the two outer layers.

usage: nego.py BOARD [max_rips]

The list of open connections is taken once from KiCad DRC. Every connection is routed in turn; when no legal
path exists the connection is routed across copper this router added earlier, the nets it crossed are ripped up
and queued again. A net gets more expensive to cross every time it has been ripped, which is what stops two
nets from evicting each other for ever.
"""
import collections
import json
import math
import sys
import time

import router as R
from do_route import prio, rip, PLANE   # noqa: E402  (do_route is import-safe: see __main__ guard there)

path = sys.argv[1]
MAX_RIPS = int(sys.argv[2]) if len(sys.argv) > 2 else 300
NET_CAP = 10
PROT = {'GND', '+3V3', '+5V', '/VBUS', '/USB_D_P', '/USB_D_N', 'Net-(J5-CC1)', 'Net-(J5-CC2)', 'Net-(U2-VDDA)', 'Net-(U2-PF0)',
        'Net-(U2-PF1)', 'Net-(U301-A)'}


def short(n):
    return n.split('/')[-1]


def attempt(r, c, margins=(4.0, 10.0, 30.0)):
    for m in margins:
        if r.route(c['net'], c['A'], c['B'], margin=m, max_nodes=6_000_000):
            return True
    return False


txt = R.run_drc(path, path.replace('.kicad_pcb', '_nego0.rpt'))
conns = []
for a, b in R.parse_unconnected(txt):
    net = a['net']
    if net in PLANE or net in PROT or 'CN301' in a['desc'] + b['desc'] or 'Zone' in (a['kind'], b['kind']):
        continue
    if 'In2.Cu' in a['desc'] or 'In2.Cu' in b['desc']:
        continue
    conns.append({'net': net, 'A': (a['x'], a['y'], a['layers']), 'B': (b['x'], b['y'], b['layers']),
                  'd': math.dist((a['x'], a['y']), (b['x'], b['y'])), 'desc': (a['desc'][:38], b['desc'][:38])})
conns.sort(key=lambda c: (prio(c['net']), c['d']))
for i, c in enumerate(conns):
    c['id'] = i
bynet = collections.defaultdict(list)
for c in conns:
    bynet[c['net']].append(c)
print(f'{len(conns)} connections on {len(bynet)} nets', flush=True)

REG = {}
r = R.Router(path, reg=REG, protected=PROT)
queue = collections.deque(conns)
queued = set(c['id'] for c in conns)
ripcount = collections.Counter()
tries = collections.Counter()
rips = 0
fails = {}
t0 = time.time()
step = 0
while queue:
    c = queue.popleft()
    queued.discard(c['id'])
    step += 1
    net = c['net']
    if attempt(r, c):
        fails.pop(c['id'], None)
        continue
    tries[c['id']] += 1
    if rips >= MAX_RIPS or tries[c['id']] > 6:
        fails[c['id']] = 'budget'
        continue
    r.softfac = {n: float((1 + k) ** 2) for n, k in ripcount.items()}
    hit = r.route(net, c['A'], c['B'], margin=30.0, max_nodes=8_000_000, soft=True)
    if hit is False:
        fails[c['id']] = 'hard'
        print(f'  [{step}] {short(net)}: blocked by fixed copper', flush=True)
        continue
    hit = set(hit)
    if not hit:
        # a legal path exists in the wide window after all
        if not attempt(r, c, margins=(30.0, 45.0)):
            fails[c['id']] = 'odd'
        continue
    if any(ripcount[h] >= NET_CAP for h in hit):
        fails[c['id']] = 'cap'
        print(f'  [{step}] {short(net)}: would need {sorted(short(h) for h in hit)} (capped)', flush=True)
        continue
    for h in hit:
        ripcount[h] += 1
    rips += 1
    r = rip(path, r, hit)
    ok = attempt(r, c)
    print(f'  [{step}] {short(net)}: ripped {sorted(short(h) for h in hit)} -> {"ok" if ok else "FAIL"}  (rips {rips}, queue {len(queue)}, {time.time() - t0:.0f} s)', flush=True)
    if not ok:
        if c['id'] not in queued:
            queue.append(c)
            queued.add(c['id'])
    else:
        fails.pop(c['id'], None)
    for h in hit:
        for c2 in bynet[h]:
            if c2['id'] not in queued:
                queue.append(c2)
                queued.add(c2['id'])
# last chance for everything that was given up on while the board was still changing
for cid in list(fails):
    c = conns[cid]
    if attempt(r, c):
        fails.pop(cid)
r.save()
json.dump(REG, open(path.replace('.kicad_pcb', '_reg.json'), 'w'), default=list)
print(f'done: {len(conns) - len(fails)} of {len(conns)} routed, {rips} rip-ups, {time.time() - t0:.0f} s', flush=True)
for cid, why in fails.items():
    c = conns[cid]
    print('   FAIL', why, short(c['net']), round(c['d'], 1), c['desc'], flush=True)
print('ripcount', {short(k): v for k, v in ripcount.most_common(12)}, flush=True)

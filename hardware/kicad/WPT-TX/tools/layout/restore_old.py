#!/usr/bin/env python3
"""Bring the routes of named nets back from an earlier board, then drop the pieces the present board cannot keep.

usage: restore_old.py OLD_BOARD BOARD REG.json NET[=OLDNAME] ...

The mechanical revision moved a few parts and added two keep-outs, and the nets that were affected had been taken out
whole. Routing them again from nothing gave longer routes than before, so the old copper comes back first (as copper
of the grid router, i.e. listed in REG) and only what now collides is removed:
  * a piece that KiCad's DRC reports for clearance, a short, a crossing or a keep-out,
  * then every piece that is left hanging without a connection at one end, repeatedly (cleanup.py does that part).
What stays open afterwards is short and is routed by fillin.py.
"""
import collections
import gc
import json
import re
import subprocess
import sys

import pcbnew

import router as R
from nego import rip_text

R.DEFAULT_CORRIDORS = ()
old, path, regfile = sys.argv[1:4]
names = dict((a.split('=') + [a])[:2] for a in sys.argv[4:])          # new short name -> old short name
MM = 1e6
short = lambda n: n.split('/')[-1]
tup = lambda q: tuple(tuple(x) if isinstance(x, list) else x for x in q)
REG = {n: [tup(q) for q in ks] for n, ks in json.load(open(regfile)).items()}
rnd = lambda v: (round(v.x / MM, 4), round(v.y / MM, 4))

ob = pcbnew.LoadBoard(old)
items = collections.defaultdict(list)
back = {v: k for k, v in names.items()}
for t in ob.GetTracks():
    n = short(t.GetNetname())
    if n not in back:
        continue
    if t.GetClass() == 'PCB_VIA':
        items[back[n]].append(('V', rnd(t.GetPosition())))
    else:
        items[back[n]].append(('T', ob.GetLayerName(t.GetLayer()), rnd(t.GetStart()), rnd(t.GetEnd()), round(t.GetWidth() / MM, 4)))
del ob
gc.collect()

r = R.Router(path, reg=REG)
have = set()
for t in r.board.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        have.add(R.Router.vkey(t.GetNetname(), rnd(t.GetPosition())))
    else:
        have.add(R.Router.tkey(t.GetNetname(), r.board.GetLayerName(t.GetLayer()), rnd(t.GetStart()), rnd(t.GetEnd())))
added = collections.Counter()
for name, its in items.items():
    net = [n for n in r.nets if short(n) == name][0]
    for it in its:
        if it[0] == 'V':
            if R.Router.vkey(net, it[1]) not in have:
                r.add_via(net, it[1])
                added[name] += 1
        elif R.Router.tkey(net, it[1], it[2], it[3]) not in have:
            r.add_track(net, it[1], it[2], it[3], it[4])
            added[name] += 1
r.save()
REG = r.reg
del r
gc.collect()
print('brought back:', dict(added))

BAD = ('clearance', 'shorting_items', 'tracks_crossing', 'items_not_allowed', 'hole_clearance', 'copper_edge_clearance', 'solder_mask_bridge')
mine = {n for n in REG if short(n) in names}
for rnd_no in range(8):
    rpt = path.replace('.kicad_pcb', '_ro.json')
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--refill-zones', '--save-board', '--format', 'json', '--severity-all', '-o', rpt, path],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = json.load(open(rpt))
    kill = set()
    for v in d.get('violations', []):
        if v['type'] not in BAD:
            continue
        for i in v['items']:
            m = re.match(r'(Track|Via) \[([^\]]+)\]', i['description'])
            if not m or m.group(2) not in mine:
                continue
            x, y = i['pos']['x'], i['pos']['y']
            # the registered piece of that net that starts, ends or sits at the reported position
            for k in REG[m.group(2)]:
                pts = [k[2]] if k[0] == 'V' else [k[3], k[4]]
                if (k[0] == 'V') == (m.group(1) == 'Via') and any(abs(p[0] - x) < 0.006 and abs(p[1] - y) < 0.006 for p in pts):
                    kill.add(k)
    if not kill:
        break
    n = rip_text(path, kill)
    for net in mine:
        REG[net] = [k for k in REG[net] if k not in kill]
    print('round %d: %d colliding pieces removed' % (rnd_no, n), flush=True)
json.dump({k: [list(q) for q in v] for k, v in REG.items()}, open(regfile, 'w'))
print('written', path)

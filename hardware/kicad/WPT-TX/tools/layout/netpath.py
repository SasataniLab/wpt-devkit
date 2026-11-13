#!/usr/bin/env python3
"""Print the copper of a net as ordered chains, and what runs beside it.

usage: netpath.py BOARD NET [NET...] [--near 0.45]
For every named net (short name): pads, vias, chains of segments per layer (in order),
and for every other net the length of this net's tracks that has copper of that net
closer than --near mm (edge to edge) on the same layer.
"""
import math
import sys
from collections import defaultdict

import pcbnew

MM = 1e-6
args = [a for a in sys.argv[1:] if not a.startswith('--')]
near = 0.45
if '--near' in sys.argv:
    near = float(sys.argv[sys.argv.index('--near') + 1])
    args = [a for a in args if a != sys.argv[sys.argv.index('--near') + 1]]
board = pcbnew.LoadBoard(args[0])
want = args[1:]
short = lambda n: n.split('/')[-1]

tracks = defaultdict(list)   # layer -> [(net, x1,y1,x2,y2,w)]
vias = defaultdict(list)
for t in board.GetTracks():
    n = short(t.GetNetname())
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        vias[n].append((round(p.x * MM, 3), round(p.y * MM, 3)))
    else:
        a, b = t.GetStart(), t.GetEnd()
        tracks[board.GetLayerName(t.GetLayer())].append(
            (n, round(a.x * MM, 3), round(a.y * MM, 3), round(b.x * MM, 3), round(b.y * MM, 3), t.GetWidth() * MM))
pads = defaultdict(list)
for fp in board.GetFootprints():
    for p in fp.Pads():
        c = p.GetPosition()
        pads[short(p.GetNetname())].append((fp.GetReference(), p.GetNumber(), round(c.x * MM, 3), round(c.y * MM, 3)))


def seg_pt_d(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


for net in want:
    print('=' * 8, net)
    for ref, num, x, y in pads[net]:
        print('  pad %s.%s (%.3f, %.3f)' % (ref, num, x, y))
    print('  vias', vias[net])
    tot = defaultdict(float)
    beside = defaultdict(lambda: defaultdict(float))
    for layer, segs in tracks.items():
        mine = [s for s in segs if s[0] == net]
        if not mine:
            continue
        # order into chains
        left = list(mine)
        chains = []
        while left:
            s = left.pop(0)
            chain = [(s[1], s[2]), (s[3], s[4])]
            grown = True
            while grown:
                grown = False
                for o in list(left):
                    a, b = (o[1], o[2]), (o[3], o[4])
                    if a == chain[-1]:
                        chain.append(b)
                    elif b == chain[-1]:
                        chain.append(a)
                    elif a == chain[0]:
                        chain.insert(0, b)
                    elif b == chain[0]:
                        chain.insert(0, a)
                    else:
                        continue
                    left.remove(o)
                    grown = True
            chains.append(chain)
        for ch in chains:
            L = sum(math.dist(ch[i], ch[i + 1]) for i in range(len(ch) - 1))
            tot[layer] += L
            print('  %s %.1f mm: %s' % (layer, L, ' '.join('(%.2f,%.2f)' % p for p in ch)))
        others = [s for s in segs if s[0] != net]
        for s in mine:
            L = math.hypot(s[3] - s[1], s[4] - s[2])
            n = max(1, int(L / 0.1))
            for i in range(n):
                t = (i + 0.5) / n
                px, py = s[1] + t * (s[3] - s[1]), s[2] + t * (s[4] - s[2])
                hit = {}
                for o in others:
                    if min(o[1], o[3]) - 1 > px or max(o[1], o[3]) + 1 < px or min(o[2], o[4]) - 1 > py or max(o[2], o[4]) + 1 < py:
                        continue
                    d = seg_pt_d(px, py, o[1], o[2], o[3], o[4]) - s[5] / 2 - o[5] / 2
                    if d < near:
                        hit[o[0]] = min(hit.get(o[0], 9), d)
                for k, d in hit.items():
                    beside[layer][k] += L / n
    print('  total', {k: round(v, 1) for k, v in tot.items()}, 'sum %.1f' % sum(tot.values()), 'vias', len(vias[net]))
    for layer, d in beside.items():
        items = sorted(d.items(), key=lambda kv: -kv[1])
        print('  beside on %s (<%.2f mm): %s' % (layer, near, ', '.join('%s %.1f' % (k or '(none)', v) for k, v in items if v >= 1.0)))

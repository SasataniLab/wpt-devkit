#!/usr/bin/env python3
"""How long is each net compared with the shortest it could be on 0 / 45 / 90 degrees, and is it on those angles?

usage: lencheck.py BOARD [REF ...] [--all] [--min RATIO]

For every signal net with a pad on one of the named parts (default: U2 and the headers J1 J2 J3 J4 J301):
  routed   copper length of the net, all layers
  ideal    length of the minimum spanning tree over its pads when the distance between two pads is the octilinear
           one (longer leg + 0.414 x shorter leg). For a two-pad net this is exactly the shortest 45-degree route;
           for more pads a tree with branch points can be a little shorter, so a ratio just under 1 is possible.
  off45    number of segments that are not on 0 / 45 / 90 degrees
"""
import math
import sys
from collections import defaultdict

import pcbnew

MM = 1e-6
args = [a for a in sys.argv[1:] if not a.startswith('--')]
board = pcbnew.LoadBoard(args[0])
refs = args[1:] or ['U2', 'J1', 'J2', 'J3', 'J4', 'J301']
minr = float(sys.argv[sys.argv.index('--min') + 1]) if '--min' in sys.argv else 0.0
if '--min' in sys.argv:
    refs = [r for r in refs if r != sys.argv[sys.argv.index('--min') + 1]] or ['U2', 'J1', 'J2', 'J3', 'J4', 'J301']
short = lambda n: n.split('/')[-1]
PLANES = ('GND', '+3V3', '+5V', 'VPP', 'VBUS', '+7V', 'VIN')
want = set()
pads = defaultdict(list)
for fp in board.GetFootprints():
    for p in fp.Pads():
        n = p.GetNetname()
        if not n or n.startswith('unconnected') or short(n) in PLANES:
            continue
        pads[n].append((p.GetPosition().x * MM, p.GetPosition().y * MM, fp.GetReference() + '.' + p.GetNumber()))
        if fp.GetReference() in refs:
            want.add(n)
length = defaultdict(lambda: defaultdict(float))
nvia = defaultdict(int)
off = defaultdict(int)
nseg = defaultdict(int)
for t in board.GetTracks():
    n = t.GetNetname()
    if t.Type() == pcbnew.PCB_VIA_T:
        nvia[n] += 1
        continue
    a, e = t.GetStart(), t.GetEnd()
    dx, dy = abs(a.x - e.x) * MM, abs(a.y - e.y) * MM
    length[n][board.GetLayerName(t.GetLayer())] += math.hypot(dx, dy)
    nseg[n] += 1
    if not (dx < 2e-3 or dy < 2e-3 or abs(dx - dy) < 2e-3):
        off[n] += 1


def octile(p, q):
    dx, dy = abs(p[0] - q[0]), abs(p[1] - q[1])
    return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


def mst(pts):
    if len(pts) < 2:
        return 0.0
    done, rest, tot = [pts[0]], list(pts[1:]), 0.0
    while rest:
        d, q = min((octile(p, q), q) for p in done for q in rest)
        tot += d
        done.append(q)
        rest.remove(q)
    return tot


rows = []
for n in want:
    L = sum(length[n].values())
    ideal = mst(pads[n])
    if ideal < 0.5:
        continue
    rows.append((L / ideal, short(n), L, ideal, nvia[n], length[n].get('In2.Cu', 0.0), nseg[n], off[n], len(pads[n])))
rows.sort(reverse=True)
print('%-24s %7s %7s %6s %5s %6s %5s %5s %s' % ('net', 'routed', 'ideal', 'ratio', 'vias', 'In2', 'segs', 'off45', 'pads'))
for r, name, L, ideal, v, inn, ns, o, np_ in rows:
    if r >= minr:
        print('%-24s %7.1f %7.1f %6.2f %5d %6.1f %5d %5d %d' % (name, L, ideal, r, v, inn, ns, o, np_))
print('nets %d, total routed %.0f mm, total ideal %.0f mm, segments %d, off 45 deg %d, on In2 %.1f mm, vias %d' % (
    len(rows), sum(x[2] for x in rows), sum(x[3] for x in rows), sum(x[6] for x in rows), sum(x[7] for x in rows), sum(x[5] for x in rows), sum(x[4] for x in rows)))

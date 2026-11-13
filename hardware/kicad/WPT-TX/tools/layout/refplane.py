#!/usr/bin/env python3
"""Which plane lies under each track of a net.

usage: refplane.py BOARD NET [NET...]
Outer-layer tracks return their current in the nearest inner layer (F.Cu -> In1.Cu, B.Cu -> In2.Cu).
For every named net: track length over each plane net, and the places where the plane under the
track changes (a gap or a different plane = the return current has to find another way).
The board must be saved with filled zones.
"""
import math
import sys
from collections import defaultdict

import pcbnew

MM = 1e-6
board = pcbnew.LoadBoard(sys.argv[1])
want = sys.argv[2:]
short = lambda n: n.split('/')[-1]
REF = {'F.Cu': 'In1.Cu', 'B.Cu': 'In2.Cu'}
lid = {board.GetLayerName(i): i for i in board.GetEnabledLayers().Seq()}

fills = defaultdict(list)          # layer name -> [(net, SHAPE_POLY_SET)]
for z in board.Zones():
    if z.GetIsRuleArea():
        continue
    for ln in ('In1.Cu', 'In2.Cu'):
        if z.IsOnLayer(lid[ln]):
            fills[ln].append((short(z.GetNetname()), z.GetFilledPolysList(lid[ln])))
# tracks on the inner layers count as "plane" of their net too (wide legacy supply tracks)
inner_tracks = defaultdict(list)
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        continue
    ln = board.GetLayerName(t.GetLayer())
    if ln in ('In1.Cu', 'In2.Cu'):
        a, b = t.GetStart(), t.GetEnd()
        inner_tracks[ln].append((short(t.GetNetname()), a.x * MM, a.y * MM, b.x * MM, b.y * MM, t.GetWidth() * MM))


def under(ln, x, y):
    p = pcbnew.VECTOR2I(int(round(x / MM)), int(round(y / MM)))
    for net, sps in fills[ln]:
        if sps.Contains(p):
            return net
    for net, x1, y1, x2, y2, w in inner_tracks[ln]:
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / L2))
        if math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)) <= w / 2:
            return net + '(track)'
    return '-none-'


for net in want:
    over = defaultdict(float)
    changes = []
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T or short(t.GetNetname()) != net:
            continue
        ln = board.GetLayerName(t.GetLayer())
        if ln not in REF:
            over[(ln, 'inner layer track')] += t.GetLength() * MM
            continue
        a, b = t.GetStart(), t.GetEnd()
        x1, y1, x2, y2 = a.x * MM, a.y * MM, b.x * MM, b.y * MM
        L = math.hypot(x2 - x1, y2 - y1)
        n = max(1, int(L / 0.05))
        prev = None
        for i in range(n):
            f = (i + 0.5) / n
            x, y = x1 + f * (x2 - x1), y1 + f * (y2 - y1)
            u = under(REF[ln], x, y)
            over[(ln, u)] += L / n
            if prev is not None and u != prev[0]:
                changes.append((ln, prev[0], u, round(x, 2), round(y, 2)))
            prev = (u, x, y)
    print('%-16s' % net, ', '.join('%s over %s %.1f' % (k[0][0], k[1], v) for k, v in sorted(over.items())))
    # merge change points that are the two edges of one gap
    for c in changes:
        print('    %s: %s -> %s at (%.2f, %.2f)' % c)

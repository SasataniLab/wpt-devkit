#!/usr/bin/env python3
"""Physical audit of every net on the MCU: length per layer, vias, plane under the track, parallel neighbours.

usage: audit.py BOARD [REF=U2]
"""
import math
import sys
from collections import defaultdict

import pcbnew

MM = 1e-6
board = pcbnew.LoadBoard(sys.argv[1])
ref = sys.argv[2] if len(sys.argv) > 2 else 'U2'
short = lambda n: n.split('/')[-1]
REF = {'F.Cu': 'In1.Cu', 'B.Cu': 'In2.Cu'}
lid = {board.GetLayerName(i): i for i in board.GetEnabledLayers().Seq()}
fills = defaultdict(list)
for z in board.Zones():
    if z.GetIsRuleArea():
        continue
    for ln in ('In1.Cu', 'In2.Cu'):
        if z.IsOnLayer(lid[ln]):
            fills[ln].append((short(z.GetNetname()), z.GetFilledPolysList(lid[ln])))
segs = defaultdict(list)
nvia = defaultdict(int)
bylayer = defaultdict(list)
for t in board.GetTracks():
    n = short(t.GetNetname())
    if t.Type() == pcbnew.PCB_VIA_T:
        nvia[n] += 1
        continue
    a, b = t.GetStart(), t.GetEnd()
    s = (board.GetLayerName(t.GetLayer()), a.x * MM, a.y * MM, b.x * MM, b.y * MM, t.GetWidth() * MM)
    segs[n].append(s)
    bylayer[s[0]].append((n,) + s[1:])


def under(ln, x, y):
    p = pcbnew.VECTOR2I(int(round(x / MM)), int(round(y / MM)))
    for net, sps in fills[ln]:
        if sps.Contains(p):
            return net
    return '-'


def dseg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


fp = board.FindFootprintByReference(ref)
pins = defaultdict(list)
for p in fp.Pads():
    pins[short(p.GetNetname())].append(p.GetNumber() + ':' + p.GetPinFunction().split('/')[0][:6])
rows = []
for net in sorted(pins):
    if net in ('GND', '+3V3', '') or not segs[net]:
        continue
    L = defaultdict(float)
    over = defaultdict(float)
    beside = defaultdict(float)
    cross = 0
    for ln, x1, y1, x2, y2, w in segs[net]:
        l = math.hypot(x2 - x1, y2 - y1)
        L[ln] += l
        if ln not in REF:
            continue
        n = max(1, int(l / 0.1))
        prev = None
        others = [o for o in bylayer[ln] if o[0] != net and min(o[1], o[3]) - 1.5 < max(x1, x2) and max(o[1], o[3]) + 1.5 > min(x1, x2)
                  and min(o[2], o[4]) - 1.5 < max(y1, y2) and max(o[2], o[4]) + 1.5 > min(y1, y2)]
        for i in range(n):
            f = (i + 0.5) / n
            x, y = x1 + f * (x2 - x1), y1 + f * (y2 - y1)
            u = under(REF[ln], x, y)
            over[ln[0] + '/' + u] += l / n
            if prev and u != prev and '-' not in (u, prev):
                cross += 1
            if u != '-':
                prev = u
            hit = set()
            for o in others:
                if dseg(x, y, o[1], o[2], o[3], o[4]) - w / 2 - o[5] / 2 < 0.3:
                    hit.add(o[0])
            for h in hit:
                beside[h] += l / n
    tot = sum(L.values())
    rows.append((net, pins[net], tot, L, nvia[net], over, cross, beside))
print('%-18s %-12s %6s %5s %5s %5s %3s  %-34s %s' % ('net', 'pin', 'len', 'F', 'B', 'In2', 'via', 'plane under track (mm)', 'runs beside (<0.3 mm gap, >=2 mm)'))
for net, pn, tot, L, nv, over, cross, beside in rows:
    ov = ' '.join('%s %.0f' % (k, v) for k, v in sorted(over.items()) if v >= 0.95)
    bs = ' '.join('%s %.0f' % (k, v) for k, v in sorted(beside.items(), key=lambda kv: -kv[1]) if v >= 2)
    print('%-18s %-12s %6.1f %5.1f %5.1f %5.1f %3d  %-34s %s' % (net, ','.join(pn)[:12], tot, L['F.Cu'], L['B.Cu'], L['In2.Cu'], nv, ov, bs))

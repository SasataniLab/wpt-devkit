#!/usr/bin/env python3
"""Where do outer-layer tracks run over a gap or a change of plane?

usage: planegap.py BOARD [--min 0.5]
F.Cu tracks are checked against In1.Cu, B.Cu tracks against In2.Cu. A stretch counts when the track has no plane
copper under it, or a different plane net than before, and the place is not just the clearance hole of one of the
net's own vias or through-hole pads (within 0.8 mm of it). Reported per net: layer, what changes, where, how long.
"""
import math
import sys
from collections import defaultdict

import pcbnew

MM = 1e-6
board = pcbnew.LoadBoard(sys.argv[1])
minlen = float(sys.argv[sys.argv.index('--min') + 1]) if '--min' in sys.argv else 0.5
short = lambda n: n.split('/')[-1]
REF = {'F.Cu': 'In1.Cu', 'B.Cu': 'In2.Cu'}
lid = {board.GetLayerName(i): i for i in board.GetEnabledLayers().Seq()}
fills = defaultdict(list)
for z in board.Zones():
    if z.GetIsRuleArea():
        continue
    for ln in REF.values():
        if z.IsOnLayer(lid[ln]):
            fills[ln].append((short(z.GetNetname()), z.GetFilledPolysList(lid[ln])))
inner = defaultdict(list)
holes = []                                   # every drilled thing: its clearance hole in the planes is not a "gap in the plane"
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        holes.append((p.x * MM, p.y * MM, 0.75))
    else:
        ln = board.GetLayerName(t.GetLayer())
        if ln in REF.values():
            a, b = t.GetStart(), t.GetEnd()
            inner[ln].append((short(t.GetNetname()), a.x * MM, a.y * MM, b.x * MM, b.y * MM, t.GetWidth() * MM))
for fp in board.GetFootprints():
    for p in fp.Pads():
        if p.GetDrillSize().x > 0:
            c = p.GetPosition()
            holes.append((c.x * MM, c.y * MM, max(p.GetSize().x, p.GetSize().y) * MM / 2 + 0.45))


def under(ln, x, y):
    p = pcbnew.VECTOR2I(int(round(x / MM)), int(round(y / MM)))
    for net, sps in fills[ln]:
        if sps.Contains(p):
            return net
    for net, x1, y1, x2, y2, w in inner[ln]:
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / L2))
        if math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)) <= w / 2:
            return net
    return None


def near_hole(x, y):
    return any(abs(x - hx) < r and abs(y - hy) < r and math.hypot(x - hx, y - hy) < r for hx, hy, r in holes)


out = defaultdict(list)
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        continue
    ln = board.GetLayerName(t.GetLayer())
    if ln not in REF:
        continue
    net = short(t.GetNetname())
    a, b = t.GetStart(), t.GetEnd()
    x1, y1, x2, y2 = a.x * MM, a.y * MM, b.x * MM, b.y * MM
    L = math.hypot(x2 - x1, y2 - y1)
    n = max(1, int(L / 0.1))
    run = None
    for i in range(n):
        f = (i + 0.5) / n
        x, y = x1 + f * (x2 - x1), y1 + f * (y2 - y1)
        u = under(REF[ln], x, y)
        bad = u is None and not near_hole(x, y)
        if bad:
            if run is None:
                run = [x, y, 0.0]
            run[2] += L / n
        if (not bad or i == n - 1) and run is not None:
            out[net].append((ln, run[0], run[1], run[2]))
            run = None
tot = {n: sum(r[3] for r in v) for n, v in out.items()}
for net in sorted(tot, key=lambda k: -tot[k]):
    if tot[net] < minlen:
        continue
    by = defaultdict(float)
    for ln, x, y, l in out[net]:
        by[ln] += l
    places = sorted(out[net], key=lambda r: -r[3])[:4]
    print('%-22s %s   e.g. %s' % (net or '(no net)', ' '.join('%s %.1f mm' % (k, v) for k, v in by.items()),
                                 ' '.join('%s(%.1f,%.1f) %.1f' % (p[0][0], p[1], p[2], p[3]) for p in places)))

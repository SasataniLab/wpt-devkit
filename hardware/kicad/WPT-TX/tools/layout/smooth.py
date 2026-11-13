#!/usr/bin/env python3
"""Straighten auto-routed tracks: runs of short segments are replaced by the longest straight pieces that keep clearance.

usage: smooth.py BOARD REG.json

Only copper listed in REG (what the grid router added) is touched. A run is a chain of segments on one layer between
two points where something else is attached (pad, via, junction, hand-made track). A straight shortcut is accepted when
every point on it is free for this net in the router's clearance map, so the result obeys the same margins as routing.
"""
import collections
import gc
import json
import math
import sys

import numpy as np
import pcbnew

import router as R
from nego import rip_text, PROT

R.DEFAULT_CORRIDORS = ()
path, regfile = sys.argv[1:3]
MM = 1e6


def tup(k):
    return tuple(tuple(x) if isinstance(x, list) else x for x in k)


REG = {net: [tup(k) for k in ks] for net, ks in json.load(open(regfile)).items()}
r = R.Router(path, reg=REG, protected=PROT)
b = r.board
rnd = lambda p: (round(p[0], 3), round(p[1], 3))
# what is on the board, per net and layer
segs = collections.defaultdict(list)          # (net, layer) -> [(a, e, width, key)]
anchors = collections.defaultdict(set)        # net -> points where a via or pad sits
for t in b.GetTracks():
    net = t.GetNetname()
    if t.GetClass() == 'PCB_VIA':
        anchors[net].add(rnd((t.GetPosition().x / MM, t.GetPosition().y / MM)))
    else:
        ln = b.GetLayerName(t.GetLayer())
        a, e = rnd((t.GetStart().x / MM, t.GetStart().y / MM)), rnd((t.GetEnd().x / MM, t.GetEnd().y / MM))
        segs[(net, ln)].append((a, e, t.GetWidth() / MM, R.Router.tkey(net, ln, a, e)))
# pads and vias: a track that merely passes over one of them must keep passing over it
padbox = collections.defaultdict(list)        # net -> [(x0, y0, x1, y1, layers)]
for fp in b.GetFootprints():
    for pad in fp.Pads():
        net = pad.GetNetname()
        if not net:
            continue
        bb = pad.GetBoundingBox()
        lay = set(b.GetLayerName(l) for l in pad.GetLayerSet().Seq())
        padbox[net].append((bb.GetLeft() / MM - 0.05, bb.GetTop() / MM - 0.05, bb.GetRight() / MM + 0.05, bb.GetBottom() / MM + 0.05, lay))


def on_anchor(net, ln, p):
    if any(math.dist(p, v) < 0.32 for v in anchors[net]):
        return True
    return any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 and ln in lay for x0, y0, x1, y1, lay in padbox[net])


def on_segment(p, a, e):
    L = math.dist(a, e)
    if L < 1e-6:
        return False
    t = ((p[0] - a[0]) * (e[0] - a[0]) + (p[1] - a[1]) * (e[1] - a[1])) / L / L
    if t <= 0.02 / L or t >= 1 - 0.02 / L:
        return False
    return math.dist(p, (a[0] + t * (e[0] - a[0]), a[1] + t * (e[1] - a[1]))) < 0.03


kill, add = set(), []
stat = collections.Counter()
for (net, ln), lst in segs.items():
    regk = set(REG.get(net, []))
    if not regk or net in PROT or ln not in ('F.Cu', 'B.Cu', 'In2.Cu'):
        continue
    deg = collections.Counter()
    adj = collections.defaultdict(list)
    for i, (a, e, w, k) in enumerate(lst):
        deg[a] += 1
        deg[e] += 1
        adj[a].append(i)
        adj[e].append(i)
    used = set()
    # a segment that something joins in its middle stays exactly as it is
    ends = set(p for a, e, w, k in lst for p in (a, e)) | anchors[net]
    for i, (a, e, w, k) in enumerate(lst):
        x0, y0, x1, y1 = min(a[0], e[0]) - 0.05, min(a[1], e[1]) - 0.05, max(a[0], e[0]) + 0.05, max(a[1], e[1]) + 0.05
        if any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 and on_segment(p, a, e) for p in ends):
            used.add(i)
            deg[a] += 10
            deg[e] += 10

    def stop(p):
        return deg[p] != 2 or on_anchor(net, ln, p)

    for i0, (a0, e0, w0, k0) in enumerate(lst):
        if i0 in used or k0 not in regk:
            continue
        # grow the chain both ways through plain two-way points, staying on router copper of one width
        chain = collections.deque([i0])
        pts = collections.deque([a0, e0])
        used.add(i0)
        for side in (0, 1):
            while True:
                p = pts[0] if side == 0 else pts[-1]
                if stop(p):
                    break
                nxt = [j for j in adj[p] if j not in used]
                if len(nxt) != 1 or lst[nxt[0]][3] not in regk or abs(lst[nxt[0]][2] - w0) > 1e-6:
                    break
                j = nxt[0]
                used.add(j)
                q = lst[j][1] if lst[j][0] == p else lst[j][0]
                if side == 0:
                    chain.appendleft(j)
                    pts.appendleft(q)
                else:
                    chain.append(j)
                    pts.append(q)
        P = list(pts)
        if len(P) < 3:
            continue
        xs, ys = [p[0] for p in P], [p[1] for p in P]
        m = 1.0
        ix0, iy0 = max(0, int((min(xs) - m - R.X0) / R.RES)), max(0, int((min(ys) - m - R.Y0) / R.RES))
        ix1, iy1 = min(R.W, int((max(xs) + m - R.X0) / R.RES) + 1), min(R.H, int((max(ys) + m - R.Y0) / R.RES) + 1)
        if (ix1 - ix0) * (iy1 - iy0) > 4_000_000:
            continue
        free, via_ok, own = r.maps(net, (ix0, iy0, ix1, iy1), w0)
        ok = free[ln] | own[ln]

        def clear(p, q):
            n = max(2, int(math.dist(p, q) / 0.02) + 1)
            t = np.linspace(0.0, 1.0, n)
            cx = np.rint((p[0] + (q[0] - p[0]) * t - R.X0) / R.RES).astype(int) - ix0
            cy = np.rint((p[1] + (q[1] - p[1]) * t - R.Y0) / R.RES).astype(int) - iy0
            return bool(ok[cy, cx].all())

        out = [P[0]]
        i = 0
        while i < len(P) - 1:
            j = len(P) - 1
            while j > i + 1 and not clear(P[i], P[j]):
                j -= 1
            out.append(P[j])
            i = j
        if len(out) < len(P):
            for j in chain:
                kill.add(lst[j][3])
            for p, q in zip(out, out[1:]):
                add.append((net, ln, p, q, w0))
            stat['runs'] += 1
            stat['before'] += len(P) - 1
            stat['after'] += len(out) - 1
r.save()
del r, b
gc.collect()
gone = rip_text(path, kill)
for net in REG:
    REG[net] = [k for k in REG[net] if k not in kill]
r = R.Router(path, reg=REG, protected=PROT)
for net, ln, p, q, w in add:
    r.add_track(net, ln, p, q, w)
r.save()
json.dump(REG, open(regfile, 'w'), default=list)
print(f"runs straightened: {stat['runs']}; segments {stat['before']} -> {stat['after']} (removed {gone})")

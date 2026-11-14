#!/usr/bin/env python3
"""Put tracks on 0 / 45 / 90 degrees with as few segments as the clearances allow.

usage: smooth45.py BOARD REG.json BASE.kicad_pcb [--only NET,...] [--skip NET,...] [--dry]

What is touched
  A run is a chain of segments of one net on one layer between two points where something else is attached
  (pad, via, junction, a change of width). A run is laid out again when
    * it is copper the grid router added (listed in REG), or
    * it holds a segment that is not on 0 / 45 / 90 degrees,
  and it is not copper of the base board (BASE: the board the work started from; that copper is left alone,
  and a point where it meets newer copper stays where it is).

How
  From the start of the run, the farthest vertex of the old run that can be reached by one straight piece or by a
  dog-leg (one orthogonal + one diagonal piece, either order) with every point clear of other nets becomes the next
  corner; then on from there. A step that would turn back by more than 90 degrees is not taken. Where not even the
  next vertex can be reached that way, the old piece stays (any angle).
  Clearance is taken from the router's raster (0.05 mm) with a small margin, so a few results can come out too tight:
  KiCad's DRC runs afterwards and every net that shows a new violation (clearance, short, open connection ...) gets
  its old copper back. A new "track has an unconnected end" is not counted: a stub of a few hundredths of a
  millimetre can be left where two pieces only overlapped; cleanup.py removes those and checks that nothing opens.
"""
import collections
import gc
import json
import math
import subprocess
import sys

import numpy as np
import pcbnew
from scipy import ndimage

import router as R
from nego import rip_text

R.DEFAULT_CORRIDORS = ()
args = [a for a in sys.argv[1:] if not a.startswith('--')]
path, regfile, basefile = args[:3]


def opt(name):
    return set(sys.argv[sys.argv.index(name) + 1].split(',')) if name in sys.argv else set()


ONLY, SKIP, DRY = opt('--only'), opt('--skip'), '--dry' in sys.argv
if ONLY:
    args.remove(sys.argv[sys.argv.index('--only') + 1])
MM = 1e6
import os
MARGIN = float(os.environ.get('S45_MARGIN', '0.03'))   # added to clearance + half width when a new piece is tested on the raster
short = lambda n: n.split('/')[-1]
rnd = lambda p: (round(p[0], 4), round(p[1], 4))
tup = lambda q: tuple(tuple(x) if isinstance(x, list) else x for x in q)
REG = {net: [tup(k) for k in ks] for net, ks in json.load(open(regfile)).items()}
REGSET = {k for ks in REG.values() for k in ks}


def base_keys(p):
    b = pcbnew.LoadBoard(p)
    out = set()
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_VIA':
            a, e = (round(t.GetStart().x / MM, 3), round(t.GetStart().y / MM, 3)), (round(t.GetEnd().x / MM, 3), round(t.GetEnd().y / MM, 3))
            out.add((b.GetLayerName(t.GetLayer()),) + tuple(sorted([a, e])))
    del b
    gc.collect()
    return out


BASE = base_keys(basefile)


def octi(a, e):
    dx, dy = abs(e[0] - a[0]), abs(e[1] - a[1])
    return dx < 2e-3 or dy < 2e-3 or abs(dx - dy) < 2e-3


def proj(p, a, e):
    """closest point to p on segment a-e, its parameter 0..1 and the distance"""
    vx, vy = e[0] - a[0], e[1] - a[1]
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L2))
    q = (a[0] + t * vx, a[1] + t * vy)
    return q, t, math.dist(p, q)


def collect(board):
    segs = collections.defaultdict(list)          # (net, layer) -> [[a, e, w]]
    vias = collections.defaultdict(list)
    pads = collections.defaultdict(list)          # net -> [(centre, box, layers)]
    for t in board.GetTracks():
        net = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            vias[net].append(rnd((t.GetPosition().x / MM, t.GetPosition().y / MM)))
        else:
            a, e = rnd((t.GetStart().x / MM, t.GetStart().y / MM)), rnd((t.GetEnd().x / MM, t.GetEnd().y / MM))
            if a != e:
                segs[(net, board.GetLayerName(t.GetLayer()))].append([a, e, round(t.GetWidth() / MM, 4)])
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            net = pad.GetNetname()
            if net:
                bb = pad.GetBoundingBox()
                lay = set(board.GetLayerName(l) for l in pad.GetLayerSet().Seq())
                pads[net].append(((pad.GetPosition().x / MM, pad.GetPosition().y / MM),
                                  (bb.GetLeft() / MM, bb.GetTop() / MM, bb.GetRight() / MM, bb.GetBottom() / MM), lay))
    return segs, vias, pads


def chains_of(net, layer, sl, vias, pads):
    """Split the segments of one net on one layer at everything that is attached, return the runs as vertex lists."""
    sl = [list(s) for s in sl]
    anchor = set()
    # 1. points that must stay: via centres and pad centres, also where a segment only passes over them
    fixed_pts = [(v, 0.31) for v in vias] + [(c, min(b[2] - b[0], b[3] - b[1]) / 2) for c, b, lay in pads if layer in lay]
    changed = True
    while changed:
        changed = False
        for s in sl:
            a, e, w = s
            for p, rad in fixed_pts:
                q, t, d = proj(p, a, e)
                if d < min(rad, 0.31) and 1e-3 < t < 1 - 1e-3 and math.dist(q, a) > 0.02 and math.dist(q, e) > 0.02:
                    q = rnd(q)
                    sl.remove(s)
                    sl += [[a, q, w], [q, e, w]]
                    anchor.add(q)
                    changed = True
                    break
            if changed:
                break
    # 2. an end that rests on the middle of another segment
    changed = True
    while changed:
        changed = False
        cnt = collections.Counter(q for s in sl for q in s[:2])
        ends = {q for q, c in cnt.items() if c == 1}                        # free ends only
        for s in sl:
            a, e, w = s
            for p in ends:
                if p in (a, e):
                    continue
                q, t, d = proj(p, a, e)
                if d < 0.9 * w and math.dist(q, a) > 0.02 and math.dist(q, e) > 0.02:
                    q = rnd(q)
                    sl.remove(s)
                    sl += [[a, q, w], [q, e, w]]
                    anchor.update((q, p))
                    changed = True
                    break
            if changed:
                break
    deg = collections.defaultdict(list)
    for i, (a, e, w) in enumerate(sl):
        deg[a].append(i)
        deg[e].append(i)
    nodes = list(deg)
    nb = {p: {sl[i][0] if sl[i][1] == p else sl[i][1] for i in deg[p]} for p in nodes}
    for p in nodes:
        if len(deg[p]) != 2 or len({sl[i][2] for i in deg[p]}) > 1:
            anchor.add(p)
        elif any(math.dist(p, v) < 0.31 for v in vias):
            anchor.add(p)
        elif any(layer in lay and b[0] - 0.02 <= p[0] <= b[2] + 0.02 and b[1] - 0.02 <= p[1] <= b[3] + 0.02 for c, b, lay in pads):
            anchor.add(p)
    for p in nodes:                                   # a free end that only overlaps another vertex: that vertex stays
        if len(deg[p]) == 1:
            for q in nodes:
                if q != p and q not in nb[p] and math.dist(p, q) < 0.15:
                    anchor.add(q)
    used, out = set(), []
    for i0 in range(len(sl)):
        if i0 in used:
            continue
        # walk both ways from this segment until an anchor
        chain = [sl[i0][0], sl[i0][1]]
        used.add(i0)
        for side in (0, 1):
            while True:
                tip = chain[-1] if side else chain[0]
                if tip in anchor:
                    break
                nxt = [i for i in deg[tip] if i not in used]
                if not nxt:
                    break
                i = nxt[0]
                used.add(i)
                other = sl[i][1] if sl[i][0] == tip else sl[i][0]
                if side:
                    chain.append(other)
                else:
                    chain.insert(0, other)
        out.append((chain, sl[i0][2]))
    return out, sl


DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


def dir8(a, e):
    dx, dy = e[0] - a[0], e[1] - a[1]
    sx = 0 if abs(dx) < 2e-3 else (1 if dx > 0 else -1)
    sy = 0 if abs(dy) < 2e-3 else (1 if dy > 0 else -1)
    return DIRS.index((sx, sy)) if (sx, sy) != (0, 0) else None


def turn(d1, d2):
    k = abs(d1 - d2) % 8
    return min(k, 8 - k)                 # 0 = straight on, 4 = back


def doglegs(p, q):
    dx, dy = q[0] - p[0], q[1] - p[1]
    ax, ay = abs(dx), abs(dy)
    if ax < 2e-3 or ay < 2e-3 or abs(ax - ay) < 2e-3:
        return [[p, q]]
    sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
    if ax > ay:                          # orthogonal part is horizontal
        m1 = (p[0] + sx * (ax - ay), p[1])          # straight first
        m2 = (p[0] + sx * ay, q[1])                 # diagonal first
    else:
        m1 = (p[0], p[1] + sy * (ay - ax))
        m2 = (q[0], p[1] + sy * ax)
    return [[p, rnd(m1), q], [p, rnd(m2), q]]


class Clear:
    """distance to the copper of other nets, per layer, from the router's raster"""

    def __init__(self, r, net):
        self.r, self.n, self.d = r, r.nid(net), {}

    def dist(self, layer):
        if layer not in self.d:
            a = self.r.cv.arr(layer)
            other = (a != 0) & (a != self.n)
            self.d[layer] = ndimage.distance_transform_edt(~other) * R.RES if other.any() else np.full(a.shape, 1e6)
        return self.d[layer]

    def ok(self, layer, a, e, w):
        L = math.dist(a, e)
        n = max(2, int(L / 0.02) + 1)
        xs, ys = np.linspace(a[0], e[0], n), np.linspace(a[1], e[1], n)
        ix = np.clip(np.rint((xs - R.X0) / R.RES).astype(int), 0, R.W - 1)
        iy = np.clip(np.rint((ys - R.Y0) / R.RES).astype(int), 0, R.H - 1)
        return bool((self.dist(layer)[iy, ix] >= R.CLR + w / 2 + MARGIN).all())


def relay(chain, w, layer, clr):
    """new vertex list for one run"""
    k = len(chain) - 1
    out = [chain[0]]
    i, prev = 0, None
    while i < k:
        best = None
        for j in range(k, i, -1):
            cands = doglegs(chain[i], chain[j])
            good = []
            for c in cands:
                d0 = dir8(c[0], c[1])
                if prev is not None and d0 is not None and turn(prev, d0) > 2:
                    continue
                if all(clr.ok(layer, c[m], c[m + 1], w) for m in range(len(c) - 1)):
                    good.append(c)
            if good:
                # the one that goes straight on from the piece before, else the one whose pieces are more even
                good.sort(key=lambda c: (turn(prev, dir8(c[0], c[1])) if prev is not None else 0,
                                         -min(math.dist(c[m], c[m + 1]) for m in range(len(c) - 1))))
                best = (j, good[0])
                break
        if best is None:                 # keep the old piece
            j, c = i + 1, [chain[i], chain[i + 1]]
        else:
            j, c = best
        out += c[1:]
        prev = dir8(c[-2], c[-1])
        i = j
    # merge pieces that lie in one line
    res = [out[0]]
    for p in out[1:]:
        if p == res[-1]:
            continue
        if len(res) >= 2 and dir8(res[-2], res[-1]) is not None and dir8(res[-2], res[-1]) == dir8(res[-1], p) and octi(res[-2], res[-1]) and octi(res[-1], p):
            res[-1] = p
        else:
            res.append(p)
    return res


def drc(board_path):
    rpt = board_path.replace('.kicad_pcb', '_s45.json')
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--refill-zones', '--save-board', '--format', 'json', '--severity-all', '-o', rpt, board_path],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = json.load(open(rpt))
    bad = collections.Counter()
    import re
    for v in d.get('violations', []) + d.get('unconnected_items', []):
        ty = v.get('type', 'unconnected')
        if ty.startswith('silk') or ty.startswith('lib_') or ty in ('zones_intersect', 'courtyards_overlap', 'starved_thermal', 'track_dangling', 'via_dangling'):
            continue
        nets = tuple(sorted({m for i in v['items'] for m in re.findall(r'\[([^\]]+)\]', i['description'])}))
        bad[(ty, nets)] += 1
    return bad


# ------------------------------------------------------------------ plan
board = pcbnew.LoadBoard(path)
segs, vias, pads = collect(board)
del board
gc.collect()
before = drc(path)
plan = {}                                  # net -> (delete keys, [(layer, a, e, w, registered)])
stat = []
nets = sorted({n for n, l in segs})
for net in nets:
    if (ONLY and short(net) not in ONLY) or short(net) in SKIP:
        continue
    todo = []
    for (n, layer), sl in segs.items():
        if n != net:
            continue
        isbase = lambda s: (layer,) + R.Router.tkey(net, layer, s[0], s[1])[3:] in BASE
        legacy = [s for s in sl if isbase(s)]
        sl = [s for s in sl if not isbase(s)]
        if not sl:
            continue
        chs, sl2 = chains_of(net, layer, sl, vias[net] + [p for s in legacy for p in s[:2]], pads[net])
        for chain, w in chs:
            keys = [R.Router.tkey(net, layer, a, e) for a, e in zip(chain, chain[1:])]
            reg = all(k in REGSET for k in keys)
            if not reg and all(octi(a, e) for a, e in zip(chain, chain[1:])):
                continue
            todo.append((layer, chain, w, reg))
        # the split may have cut segments that belong to runs left alone: write those pieces back as they are
        plan.setdefault(net, [set(), []])
        orig = {R.Router.tkey(net, layer, a, e) for a, e, w in sl}
        new = {R.Router.tkey(net, layer, a, e): (a, e, w) for a, e, w in sl2}
        for k in orig - set(new):
            plan[net][0].add(k)
        for k in set(new) - orig:
            a, e, w = new[k]
            plan[net][1].append((layer, a, e, w, k in REGSET or any(o in REGSET for o in orig - set(new))))
    if not todo:
        if net in plan and not plan[net][0]:
            plan.pop(net)
        continue
    r = R.Router(path, reg={}, protected=set())
    clr = Clear(r, net)
    n0 = n1 = 0
    L0 = L1 = 0.0
    for layer, chain, w, reg in todo:
        new = relay(chain, w, layer, clr)
        n0 += len(chain) - 1
        n1 += len(new) - 1
        L0 += sum(math.dist(a, e) for a, e in zip(chain, chain[1:]))
        L1 += sum(math.dist(a, e) for a, e in zip(new, new[1:]))
        oldk = {R.Router.tkey(net, layer, a, e) for a, e in zip(chain, chain[1:])}
        newk = {R.Router.tkey(net, layer, a, e): (a, e) for a, e in zip(new, new[1:])}
        # pieces written back by the split step and now replaced
        plan[net][1] = [x for x in plan[net][1] if not (x[0] == layer and R.Router.tkey(net, layer, x[1], x[2]) in oldk - set(newk))]
        for k in oldk - set(newk):
            plan[net][0].add(k)
        for k in set(newk) - oldk:
            plan[net][1].append((layer, newk[k][0], newk[k][1], w, reg))
    left = sum(1 for x in plan[net][1] if not octi(x[1], x[2]))
    stat.append((short(net), n0, n1, L0, L1, left))
    del r, clr
    gc.collect()
for s in stat:
    print('%-24s segments %4d -> %4d   length %7.2f -> %7.2f mm%s' % (s[0], s[1], s[2], s[3], s[4], '   (%d pieces stay off 45 deg)' % s[5] if s[5] else ''), flush=True)
print('total segments %d -> %d' % (sum(s[1] for s in stat), sum(s[2] for s in stat)))
if DRY:
    sys.exit()


def apply(todo_nets):
    r = R.Router(path, reg=REG, protected=set())
    kill = set()
    for net in todo_nets:
        dels, adds = plan[net]
        kill |= dels
        REG[net] = [k for k in REG.get(net, []) if k not in dels]
        for layer, a, e, w, reg in adds:
            r._fixed = not reg
            r.add_track(net, layer, a, e, w)
    r.save()
    del r
    gc.collect()
    return rip_text(path, kill), len(kill)


import shutil
orig = path + '.s45.bak'
shutil.copy(path, orig)
reg0 = json.loads(json.dumps(REG, default=list))
todo_nets = list(plan)
for rnd_no in range(4):
    shutil.copy(orig, path)
    REG = {net: [tup(k) for k in ks] for net, ks in reg0.items()}
    gone, want = apply(todo_nets)
    after = drc(path)
    new = {k: v - before.get(k, 0) for k, v in after.items() if v > before.get(k, 0)}
    print('round %d: %d nets changed, removed %d of %d old pieces, new DRC items: %d' % (rnd_no, len(todo_nets), gone, want, sum(new.values())), flush=True)
    if not new or os.environ.get('S45_NOREVERT'):
        break
    culprits = {n for (ty, ns), v in new.items() for n in ns if n in todo_nets}
    for (ty, ns), v in new.items():
        print('   ', ty, [short(n) for n in ns], v)
    if not culprits:
        print('   new items do not name a changed net: stopping here')
        break
    todo_nets = [n for n in todo_nets if n not in culprits]
    print('    old copper back for:', sorted(short(n) for n in culprits), flush=True)
json.dump(REG, open(regfile, 'w'), default=list)
print('written', path)

#!/usr/bin/env python3
"""Find track runs that are longer than they need to be and lay them again as the shortest 0 / 45 / 90 degree
path on the same layer between the same two end points.

usage: shorten.py BOARD BASE [--min 0.4] [--extra 0.1] [--only NET,...] [--skip NET,...] [--all-copper]
                  [--apply OUT [--passes 12]] [--json FILE]
       shorten.py BOARD --replay FILE --apply OUT        lay recorded changes again (no search)

A run is a chain of segments of one net on one layer between two points where something else is attached: a pad, a
via, a junction, a change of width. (A via or a pad in the middle of a segment counts: the segment is cut there.)
For every run that is not copper of the base board (BASE: the board the work started from; --all-copper looks at
that copper as well) the script compares
    L   its length
    D   the octilinear distance between its ends (the shortest 45-degree route if nothing were in the way)
    S   the shortest route that keeps the clearance to everything else on that layer: A* on the 0.05 mm raster of
        router.py, eight directions, a small price per bend, no turn sharper than 90 degrees
and lists the runs with L - S >= --min, largest first. End points, layer and width never change, so vias, junctions,
the reference plane under the track and the order of the nets at the ends stay as they are.

Where may the new path go?
  * where a track of this width keeps --extra mm more than the design rule from foreign copper;
  * on the old run itself, however tight it is there; a new piece that lies on an old piece takes its exact line,
    so a lane between two neighbours stays exactly where it was;
  * within 0.6 mm of the old run, where foreign copper is farther away than it is from the old run at that place
    (the way out of a tight lane towards the open side).
It stays out of the reach of washers around the mounting holes, adds no crossing under the wall band of the slide
switch cover, does not touch other tracks of its own net except at its ends and does not leave a junction along
another branch (45 degrees to it is the least).

With --apply the listed runs are replaced one after the other; every later run sees the ones already moved. Then
KiCad's DRC runs on the result: a change that causes a new violation is taken back and not tried again. This repeats
(--passes) until nothing moves. --json records every accepted change as old and new polyline; --replay lays such a
record again, which is how the result is reproduced without the search. Tracks that run as a pair or as a bundle at
minimum spacing are better moved together by hand (name them in --skip): this script moves one run at a time.
"""
import heapq
import json
import math
import os
import re
import shutil
import subprocess
import sys

import numpy as np
import pcbnew
from scipy import ndimage

import router as R

R.DEFAULT_CORRIDORS = ()
MM = 1e6
NM = 1000000                    # integer units per mm: all new corners are computed in whole nanometres
SQ2 = math.sqrt(2.0)
RES = R.RES
RHO = 0.6                       # how far from the old run the "no closer than the old run" rule opens the way
TINY = 0.15                     # pieces shorter than this are removed from a new run where the geometry allows
args = [a for a in sys.argv[1:] if not a.startswith('--')]


def opt(name, default=None):
    if name in sys.argv:
        v = sys.argv[sys.argv.index(name) + 1]
        if v in args:
            args.remove(v)
        return v
    return default


MIN_GAIN = float(opt('--min', '0.4'))
EXTRA = float(opt('--extra', '0.1'))
ONLY = set(filter(None, (opt('--only', '') or '').split(',')))
SKIP = set(filter(None, (opt('--skip', '') or '').split(',')))
APPLY = opt('--apply')
JSON = opt('--json')
REPLAY = opt('--replay')
PASSES = int(opt('--passes', '12'))
ALL_COPPER = '--all-copper' in sys.argv
BEND = 3.0                      # price of a 45-degree bend, in cells (0.15 mm)
short = lambda n: n.split('/')[-1]
rnd = lambda p: (round(p[0], 6), round(p[1], 6))
POWER = ('GND', '+3V3', '+5V', 'VPP', 'VIN', '+7V', 'VBUS', 'OutA', 'OutB')
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]      # 45-degree steps round the circle
STEP = [1.0, SQ2] * 4
toi = lambda p: (int(round(p[0] * NM)), int(round(p[1] * NM)))
tof = lambda p: (p[0] / NM, p[1] / NM)


def octi(a, b):
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return max(dx, dy) + (SQ2 - 1) * min(dx, dy)


def length(pts):
    return sum(math.dist(p, q) for p, q in zip(pts, pts[1:]))


def seg_key(layer, a, b):
    return (layer,) + tuple(sorted([(round(a[0], 3), round(a[1], 3)), (round(b[0], 3), round(b[1], 3))]))


def base_keys(p):
    b = pcbnew.LoadBoard(p)
    out = set()
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_VIA':
            out.add(seg_key(b.GetLayerName(t.GetLayer()), (t.GetStart().x / MM, t.GetStart().y / MM), (t.GetEnd().x / MM, t.GetEnd().y / MM)))
    return out


def direction(p, q):
    """index into DIRS of the direction p -> q, or None if it is not on 0 / 45 / 90 degrees (1 nm)"""
    dx, dy = int(round((q[0] - p[0]) * NM)), int(round((q[1] - p[1]) * NM))
    if dx == 0 and dy == 0:
        return None
    if dx != 0 and dy != 0 and abs(dx) != abs(dy):
        return None
    return DIRS.index(((dx > 0) - (dx < 0), (dy > 0) - (dy < 0)))


def turn(d1, d2):
    k = abs(d1 - d2) % 8
    return min(k, 8 - k)


def on_segment(p, a, e, tol=0.002):
    """is p strictly inside the segment a-e (not at its ends)?"""
    dx, dy = e[0] - a[0], e[1] - a[1]
    L2 = dx * dx + dy * dy
    if L2 < 1e-12:
        return False
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2
    if t * math.sqrt(L2) < 0.003 or (1 - t) * math.sqrt(L2) < 0.003:
        return False
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy) <= tol


def foot(c, a, e):
    """point of the segment a-e nearest to c; exactly on the segment's line for 0 / 45 / 90 degree segments (nm)"""
    A, E, C = toi(a), toi(e), toi(c)
    d = direction(a, e)
    if d is None:
        dx, dy = e[0] - a[0], e[1] - a[1]
        t = max(0.0, min(1.0, ((c[0] - a[0]) * dx + (c[1] - a[1]) * dy) / (dx * dx + dy * dy)))
        return (a[0] + t * dx, a[1] + t * dy)
    ux, uy = DIRS[d]
    n = max(abs(E[0] - A[0]), abs(E[1] - A[1]))
    t = ((C[0] - A[0]) * ux + (C[1] - A[1]) * uy) // (ux * ux + uy * uy)
    t = max(0, min(n, t))
    return tof((A[0] + t * ux, A[1] + t * uy))


# ------------------------------------------------------------------ tracks as plain records, cut where something is attached
def records(board):
    """tracks: [net, layer, a, e, w, object]; vias: {net: set of centres}; pads: {net: [pad]}"""
    tracks, vias, pads = [], {}, {}
    for t in board.GetTracks():
        net = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            vias.setdefault(net, set()).add(rnd((t.GetPosition().x / MM, t.GetPosition().y / MM)))
        else:
            a, e = rnd((t.GetStart().x / MM, t.GetStart().y / MM)), rnd((t.GetEnd().x / MM, t.GetEnd().y / MM))
            if a != e:
                tracks.append([net, board.GetLayerName(t.GetLayer()), a, e, round(t.GetWidth() / MM, 4), t])
    for fp in board.GetFootprints():
        for p in fp.Pads():
            pads.setdefault(p.GetNetname(), []).append(p)
    return tracks, vias, pads


def cut_points(board, tracks, vias, pads):
    """for every track record: the points inside it where a via, another track end or a pad of its net is attached"""
    ends = {}
    for net, layer, a, e, w, t in tracks:
        ends.setdefault((net, layer), set()).update((a, e))
    out = []
    for net, layer, a, e, w, t in tracks:
        if short(net) in POWER or not net:
            out.append([])
            continue
        pts = {p for p in vias.get(net, ()) if on_segment(p, a, e)}
        pts |= {p for p in ends[(net, layer)] if on_segment(p, a, e)}
        lid = board.GetLayerID(layer)
        for pad in pads.get(net, ()):
            if not pad.IsOnLayer(lid):
                continue
            f = foot((pad.GetPosition().x / MM, pad.GetPosition().y / MM), a, e)
            if on_segment(f, a, e) and pad.HitTest(pcbnew.VECTOR2I(int(round(f[0] * NM)), int(round(f[1] * NM)))):
                if not any(math.dist(f, q) < 0.01 for q in pts):
                    pts.add(rnd(f))
        out.append(sorted(pts, key=lambda p: math.dist(p, a)))
    return out


def split_runs(board, base):
    tracks, vias, pads = records(board)
    cuts = cut_points(board, tracks, vias, pads)
    segs = {}
    for (net, layer, a, e, w, t), cp in zip(tracks, cuts):
        chain = [a] + cp + [e]
        isbase = seg_key(layer, a, e) in base
        for p, q in zip(chain, chain[1:]):
            segs.setdefault((net, layer), []).append((p, q, w, isbase))

    def in_pad(net, layer, pt):
        v = pcbnew.VECTOR2I(int(round(pt[0] * NM)), int(round(pt[1] * NM)))
        lid = board.GetLayerID(layer)
        return any(p.IsOnLayer(lid) and p.HitTest(v) for p in pads.get(net, ()))

    runs = []
    for (net, layer), ss in segs.items():
        if not net or layer not in ('F.Cu', 'B.Cu') or short(net) in POWER:
            continue
        adj = {}
        for i, (a, e, w, ib) in enumerate(ss):
            adj.setdefault(a, []).append(i)
            adj.setdefault(e, []).append(i)

        def terminal(pt):
            idx = adj[pt]
            return len(idx) != 2 or ss[idx[0]][2] != ss[idx[1]][2] or pt in vias.get(net, ()) or in_pad(net, layer, pt)

        used = set()
        for i0 in range(len(ss)):
            if i0 in used:
                continue
            used.add(i0)
            chain, ends = [i0], []
            for start in (ss[i0][0], ss[i0][1]):
                pts, cur, prev = [start], start, i0
                while not terminal(cur):
                    nxt = [j for j in adj[cur] if j != prev]
                    if not nxt or nxt[0] in used:
                        break
                    j = nxt[0]
                    used.add(j)
                    chain.append(j)
                    cur = ss[j][1] if ss[j][0] == cur else ss[j][0]
                    pts.append(cur)
                    prev = j
                ends.append(pts)
            poly = list(reversed(ends[0])) + ends[1]
            if poly[0] == poly[-1]:
                continue
            inrun = set(chain)
            others = [(ss[j][0], ss[j][1], ss[j][2]) for j in range(len(ss)) if j not in inrun]
            sib = []
            for end in (poly[0], poly[-1]):                      # directions of the other branches at each end
                ds = []
                for a, e, w in others:
                    if a == end or e == end:
                        d = direction(end, e if a == end else a)
                        if d is not None:
                            ds.append(d)
                sib.append(ds)
            runs.append({'net': net, 'layer': layer, 'w': ss[i0][2], 'pts': poly, 'others': others, 'sib': sib,
                         'base': all(ss[j][3] for j in chain),
                         'off': sum(1 for p, q in zip(poly, poly[1:]) if direction(p, q) is None)})
    return runs


# ------------------------------------------------------------------ obstacles that are not copper
def keepouts(rt):
    b = rt.board
    for fp in b.GetFootprints():                                  # reach of a washer round the mounting holes (see holechk.py)
        if not (fp.GetReference().startswith('REF') or fp.GetPath().AsString() in ('', '/')):
            continue
        for p in fp.Pads():
            d = p.GetDrillSize().x / MM
            if d >= 2.0:
                r = (3.6 if d >= 3.0 else d / 2 + 2.0) - 0.2
                for l in ('F.Cu', 'B.Cu'):
                    rt.cv.disk(l, (p.GetPosition().x / MM, p.GetPosition().y / MM), r, R.FORBID)
    for z in b.Zones():                                           # wall band of the slide switch cover: no new crossings on the top side
        if z.GetIsRuleArea() and z.GetZoneName().startswith('SW2 metal cover'):
            o = z.Outline()
            for i in range(o.OutlineCount()):
                c = o.Outline(i)
                rt.cv.poly('F.Cu', [(c.CPoint(k).x / MM, c.CPoint(k).y / MM) for k in range(c.PointCount())], R.FORBID)
    rt.cv.invalidate()


# ------------------------------------------------------------------ shortest path of one run
def astar(ok, old, s, g, ban_s, ban_g):
    """ok[y, x], old[y, x] (cells of the old run); s, g cells; ban_s / ban_g: directions not allowed for the first / last step"""
    h, w = ok.shape
    if not (ok[s[1], s[0]] and ok[g[1], g[0]]):
        return None

    def heur(x, y):
        dx, dy = abs(x - g[0]), abs(y - g[1])
        return max(dx, dy) + (SQ2 - 1) * min(dx, dy)
    best = {(s[0], s[1], -1): 0.0}
    pq = [(heur(*s), 0.0, s[0], s[1], -1)]
    came = {}
    while pq:
        f, c, x, y, d = heapq.heappop(pq)
        if (x, y) == g:
            out = [(x, y)]
            k = (x, y, d)
            while k in came:
                k = came[k]
                out.append((k[0], k[1]))
            return out[::-1]
        if c > best.get((x, y, d), 1e18) + 1e-9:
            continue
        for nd in range(8):
            if d == -1:
                if nd in ban_s:
                    continue
                pen = 0.0
            else:
                k = turn(d, nd)
                if k > 2:
                    continue
                pen = (0.0, BEND, 2 * BEND + 1.0)[k]
            dx, dy = DIRS[nd]
            nx, ny = x + dx, y + dy
            if not (0 <= nx < w and 0 <= ny < h) or not ok[ny, nx]:
                continue
            if dx and dy and not (ok[y, nx] and ok[ny, x]) and not (old[y, x] and old[ny, nx]):    # no squeezing through a diagonal gap
                continue
            if (nx, ny) == g and nd in ban_g:
                continue
            nc = c + STEP[nd] + pen
            if nc < best.get((nx, ny, nd), 1e18) - 1e-9:
                best[(nx, ny, nd)] = nc
                came[(nx, ny, nd)] = (x, y, d)
                heapq.heappush(pq, (nc + heur(nx, ny), nc, nx, ny, nd))
    return None


def meet(p, d1, q, d2):
    """intersection (integer nm) of the line through p along DIRS[d1] and the line through q along DIRS[d2]"""
    (a, b), (c, e) = DIRS[d1], DIRS[d2]
    det = a * e - b * c
    if det == 0:
        return None
    t2 = a * (q[1] - p[1]) - b * (q[0] - p[0])
    x, y = q[0] * det - t2 * c, q[1] * det - t2 * e
    if x % det or y % det:                                            # would fall on half a nanometre
        return None
    return (x // det, y // det)


def offset(p, d, q):
    """distance (mm) of q from the line through p along DIRS[d]"""
    ux, uy = DIRS[d]
    return abs(ux * (q[1] - p[1]) - uy * (q[0] - p[0])) / math.hypot(ux, uy) / NM


def rebuild(cells, ox, oy, old):
    """cell path -> polyline: exact end points, every piece on 0 / 45 / 90 degrees, pieces that lie on an old piece on
    its exact line, no tiny pieces. Works on lines (direction + one point) and intersects neighbours."""
    grid = lambda c: (int(round((ox + c[0] * RES) * NM)), int(round((oy + c[1] * RES) * NM)))
    p0, pn = toi(old[0]), toi(old[-1])
    v = [cells[0]]
    for a, b, c in zip(cells, cells[1:], cells[2:]):
        if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]):
            v.append(b)
    v.append(cells[-1])
    dirs = [DIRS.index((int(np.sign(b[0] - a[0])), int(np.sign(b[1] - a[1])))) for a, b in zip(v, v[1:])]
    anchor = [grid(c) for c in v[:-1]]                                # one point on each piece's line
    span = [(grid(a), grid(b)) for a, b in zip(v, v[1:])]
    fixed = [False] * len(dirs)
    oldp = [(toi(a), toi(b), direction(a, b)) for a, b in zip(old, old[1:])]
    for k in range(len(dirs)):                                        # a piece that lies on an old piece takes its line
        (ga, gb), d = span[k], dirs[k]
        ux, uy = DIRS[d]
        for a, b, od in oldp:
            if od is None or od % 4 != d % 4 or offset(a, od, ga) > 0.037:
                continue
            s0, s1 = sorted([(ga[0] * ux + ga[1] * uy), (gb[0] * ux + gb[1] * uy)])
            t0, t1 = sorted([(a[0] * ux + a[1] * uy), (b[0] * ux + b[1] * uy)])
            over = (min(s1, t1) - max(s0, t0)) / math.hypot(ux, uy) / NM
            if over >= min(0.3, 0.5 * (s1 - s0) / math.hypot(ux, uy) / NM) and over > 0.04:
                anchor[k], fixed[k] = a, True
                break

    def solve(dirs, anchor):
        n = len(dirs)
        an = list(anchor)
        an[0] = p0
        if n > 1:
            an[-1] = pn
        pts = [p0]
        for k in range(1, n):
            m = meet(an[k - 1], dirs[k - 1], an[k], dirs[k])
            if m is None:
                return None
            pts.append(m)
        pts.append(pn)
        return pts

    for _ in range(40):
        if len(dirs) == 1:
            d = direction(tof(p0), tof(pn))
            if d is not None:
                return [tof(p0), tof(pn)] if d == dirs[0] else None
            for d2 in ((dirs[0] + 1) % 8, (dirs[0] - 1) % 8):         # not exactly in line: a short piece of a neighbouring direction at the far end
                m = meet(p0, dirs[0], pn, d2)
                if m is not None and direction(tof(p0), tof(m)) == dirs[0] and direction(tof(m), tof(pn)) == d2:
                    return [tof(p0), tof(m), tof(pn)]
            return None
        pts = solve(dirs, anchor)
        if pts is None:
            return None
        lens = [math.dist(tof(a), tof(b)) for a, b in zip(pts, pts[1:])]
        got = [direction(tof(a), tof(b)) for a, b in zip(pts, pts[1:])]
        bad = [k for k in range(len(dirs)) if got[k] != dirs[k] or (lens[k] < TINY and not fixed[k])]    # a short piece of the old run stays
        if not bad:
            break
        k = min(bad, key=lambda i: lens[i] if got[i] == dirs[i] else -1)
        given = lambda i: fixed[i] or i == 0 or i == len(dirs) - 1    # its line is not free to move
        if 0 < k < len(dirs) - 1 and dirs[k - 1] == dirs[k + 1]:      # a small step between two parallel pieces: one line for both
            if given(k - 1) and given(k + 1):
                if got[k] == dirs[k]:
                    break                                             # both lines are given: the step stays
                return None
            keep = k - 1 if given(k - 1) else (k + 1 if given(k + 1) else (k - 1 if lens[k - 1] >= lens[k + 1] else k + 1))
            a_keep = p0 if keep == 0 else (pn if keep == len(dirs) - 1 else anchor[keep])
            f_keep = given(keep)
            dirs[k - 1:k + 2] = [dirs[k - 1]]
            anchor[k - 1:k + 2] = [a_keep]
            fixed[k - 1:k + 2] = [f_keep]
        else:
            del dirs[k], anchor[k], fixed[k]
        if not dirs:
            return None
    else:
        return None
    ds = [direction(tof(a), tof(b)) for a, b in zip(pts, pts[1:])]
    if None in ds or any(turn(d1, d2) > 2 for d1, d2 in zip(ds, ds[1:])):
        return None
    return [tof(p) for p in pts]


def paint(mask, ox, oy, a, b):
    """cells of a segment; for 0 / 45 / 90 degree segments one clean line of cells (the nearest grid line)"""
    h, w = mask.shape
    cell = lambda p: (int(round((p[0] - ox) / RES)), int(round((p[1] - oy) / RES)))

    def put(ix, iy):
        if 0 <= ix < w and 0 <= iy < h:
            mask[iy, ix] = True
    d = direction(a, b)
    if d is None:
        n = max(2, int(math.dist(a, b) / 0.02) + 1)
        for i in range(n + 1):
            put(*cell((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)))
        return
    (ix, iy), (jx, jy) = cell(a), cell(b)
    ux, uy = DIRS[d]
    for i in range(max(abs(jx - ix), abs(jy - iy)) + 1):
        put(ix + i * ux, iy + i * uy)
    put(jx, jy)


def plan(rt, r, extra, level=0):
    """level 0: as described above; 1: the way out of a tight lane needs more room; 2: no such way out at all"""
    pts, layer, w = r['pts'], r['layer'], r['w']
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    M, P = 3.0, 30
    ix0, iy0 = max(0, int((min(xs) - M - R.X0) / RES)), max(0, int((min(ys) - M - R.Y0) / RES))
    ix1, iy1 = min(R.W, int((max(xs) + M - R.X0) / RES) + 1), min(R.H, int((max(ys) + M - R.Y0) / RES) + 1)
    jx0, jy0, jx1, jy1 = max(0, ix0 - P), max(0, iy0 - P), min(R.W, ix1 + P), min(R.H, iy1 + P)
    a = rt.cv.arr(layer)[jy0:jy1, jx0:jx1]
    other = (a != 0) & (a != rt.nid(r['net']))
    dist = (ndimage.distance_transform_edt(~other) * RES if other.any() else np.full(other.shape, 1e6))[iy0 - jy0:iy1 - jy0, ix0 - jx0:ix1 - jx0]
    ox, oy = R.X0 + ix0 * RES, R.Y0 + iy0 * RES
    ok = dist >= R.CLR + w / 2 + RES + 0.02 + extra
    old = np.zeros(ok.shape, dtype=bool)
    for p, q in zip(pts, pts[1:]):
        paint(old, ox, oy, p, q)
    d_old, idx = ndimage.distance_transform_edt(~old, return_indices=True)
    if level < 2:                                                     # the way out of a tight lane, away from the neighbour
        ok |= (d_old * RES <= RHO) & (dist >= dist[idx[0], idx[1]] + (0.025, 0.075)[level])
    # other tracks of the same net: not to be touched, except where they join at the two ends
    sib = np.zeros(ok.shape, dtype=bool)
    for sa, se, wo in r['others']:
        if max(sa[0], se[0]) < ox - 1 or min(sa[0], se[0]) > ox + ok.shape[1] * RES + 1 or max(sa[1], se[1]) < oy - 1 or min(sa[1], se[1]) > oy + ok.shape[0] * RES + 1:
            continue
        paint(sib, ox, oy, sa, se)
    if sib.any():
        near = ndimage.distance_transform_edt(~sib) * RES < (w + 0.2)
        yy, xx = np.mgrid[0:ok.shape[0], 0:ok.shape[1]]
        for end in (pts[0], pts[-1]):
            near &= np.hypot(xx * RES + ox - end[0], yy * RES + oy - end[1]) > 1.0     # a branch at 45 degrees is 0.7 mm away by then
        ok &= ~near
    ok |= old                                                         # the old run is legal where it lies
    cell = lambda p: (int(round((p[0] - ox) / RES)), int(round((p[1] - oy) / RES)))
    ban_s = {d for d in range(8) if any(turn(d, s) < 1 for s in r['sib'][0])}             # not along another branch of the junction
    ban_g = {d for d in range(8) if any(turn((d + 4) % 8, s) < 1 for s in r['sib'][1])}
    cells = astar(ok, old, cell(pts[0]), cell(pts[-1]), ban_s, ban_g)
    if cells is None or len(cells) < 2:
        return None
    return rebuild(cells, ox, oy, pts)


# ------------------------------------------------------------------ board edits (only ever in a process of their own: see replay)
def write(src, dst, changes):
    """lay the changes on the board. Pieces of the old runs are carved out of the tracks that hold them (a track that
    also serves a neighbouring run keeps the rest). Removal comes last: pcbnew gets unstable after Remove."""
    b = pcbnew.LoadBoard(src)
    tracks, vias, pads = records(b)
    kill = []
    for ch in changes:
        for p, q in zip(ch['old'], ch['old'][1:]):
            for i, (net, layer, a, e, w, t) in enumerate(tracks):
                if net != ch['net'] or layer != ch['layer']:
                    continue
                inside = lambda x: math.dist(x, a) < 0.003 or math.dist(x, e) < 0.003 or on_segment(x, a, e)
                if inside(p) and inside(q):
                    break
            else:
                raise SystemExit('write: old piece %s - %s of %s not found on the board' % (p, q, ch['net']))
            if t is not None:
                kill.append(t)
            near, far = sorted([p, q], key=lambda x: math.dist(x, a))
            del tracks[i]
            if math.dist(a, near) > 0.003:
                tracks.append([net, layer, a, near, w, None])
            if math.dist(far, e) > 0.003:
                tracks.append([net, layer, far, e, w, None])
        for p, q in zip(ch['new'], ch['new'][1:]):
            tracks.append([ch['net'], ch['layer'], p, q, ch['w'], None])
    for net, layer, a, e, w, t in tracks:
        if t is None:
            s = pcbnew.PCB_TRACK(b)
            s.SetNet(b.FindNet(net))
            s.SetLayer(b.GetLayerID(layer))
            s.SetStart(pcbnew.VECTOR2I(*toi(a)))
            s.SetEnd(pcbnew.VECTOR2I(*toi(e)))
            s.SetWidth(int(round(w * MM)))
            b.Add(s)
    for t in kill:
        b.Remove(t)
    pcbnew.SaveBoard(dst, b)


def write_in_child(src, dst, changes):
    tmp = dst[:-10] + '.changes.json'
    json.dump(changes, open(tmp, 'w'))
    r = subprocess.run([sys.executable, os.path.abspath(__file__), src, '--replay', tmp, '--apply', dst], capture_output=True, text=True)
    os.remove(tmp)
    if r.returncode != 0 or not os.path.exists(dst):
        raise SystemExit('write failed: ' + (r.stderr or r.stdout)[-600:])


CARE = ('clearance', 'shorting_items', 'tracks_crossing', 'track_dangling', 'via_dangling', 'hole_clearance', 'copper_edge_clearance',
        'solder_mask_bridge', 'starved_thermal', 'unconnected_items', 'isolated_copper', 'hole_to_hole', 'track_angle', 'connection_width')


def drc(board):
    """{(type, positions): text} of the items that matter; the project rules must lie beside the board"""
    rpt = board[:-10] + '.drc.json'
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--severity-all', '--refill-zones', '--save-board', '--format', 'json', '-o', rpt, board],
                   capture_output=True, text=True)
    d = json.load(open(rpt))
    out = {}
    for v in d.get('violations', []) + [dict(u, type='unconnected_items') for u in d.get('unconnected_items', [])]:
        if v['type'] in CARE:
            pos = tuple(sorted((round(i['pos']['x'], 2), round(i['pos']['y'], 2)) for i in v['items']))
            out[(v['type'], pos)] = ' ; '.join(i['description'] for i in v['items'])
    return out


def with_rules(src_board, dst_board):
    for ext in ('.kicad_pro', '.kicad_dru'):
        s = src_board[:-10] + ext
        if os.path.exists(s) and os.path.abspath(s) != os.path.abspath(dst_board[:-10] + ext):
            shutil.copy(s, dst_board[:-10] + ext)


def culprits(typ, pos, desc, changes):
    """which of the changes caused this violation: by net name and layer if the text names them, else by distance"""
    reach = 2.5 if typ in ('unconnected_items', 'starved_thermal', 'isolated_copper') else 0.8
    names, layers = re.findall(r'\[([^\]]+)\]', desc), re.findall(r'on ([FB]\.Cu)', desc)
    near = [i for i, ch in enumerate(changes) if any(dist_to_poly(p, ch['new']) < reach for p in pos)]
    named = [i for i in near if changes[i]['net'] in names and (not layers or changes[i]['layer'] in layers)]
    return named or [i for i in near if not layers or changes[i]['layer'] in layers] or near


def dist_to_poly(pt, poly):
    best = 1e9
    for a, b in zip(poly, poly[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / L2))
        best = min(best, math.hypot(pt[0] - a[0] - t * dx, pt[1] - a[1] - t * dy))
    return best


# ------------------------------------------------------------------ main
if REPLAY:
    changes = json.load(open(REPLAY))
    write(args[0], APPLY, changes)
    print('replayed %d changes -> %s' % (len(changes), APPLY))
    sys.exit(0)

path, basefile = args[:2]
BASE = set() if ALL_COPPER else base_keys(basefile)
level = {}                      # run -> how often the DRC has thrown its change out (3: no further try)
record = []
cur = path
baseline = None
TMP = (APPLY[:-10] + '_try.kicad_pcb') if APPLY else None
if APPLY:
    with_rules(path, APPLY)
    with_rules(path, TMP)
    shutil.copy(path, APPLY)
    baseline = drc(APPLY)
    print('baseline: %d items that matter' % len(baseline))
for npass in range(PASSES if APPLY else 1):
    rt = R.Router(cur, corridors=())
    keepouts(rt)
    runs = split_runs(rt.board, BASE)
    cand = []
    for r in runs:
        r['L'], r['D'] = length(r['pts']), octi(r['pts'][0], r['pts'][-1])
        key = (r['net'], r['layer'], r['pts'][0], r['pts'][-1])
        if r['base'] or level.get(key, 0) > 2 or (ONLY and short(r['net']) not in ONLY) or short(r['net']) in SKIP:
            continue
        r['key'] = key
        r['tiny'] = sum(1 for p, q in zip(r['pts'], r['pts'][1:]) if math.dist(p, q) < 0.1)
        if r['L'] - r['D'] >= MIN_GAIN or r['off'] or r['tiny'] >= 2:
            cand.append(r)
    cand.sort(key=lambda r: -(r['L'] - r['D']))
    found = []
    for r in cand:
        new = plan(rt, r, EXTRA, level.get(r['key'], 0))
        if new is None:
            continue
        S = length(new)
        tidy = r['tiny'] >= 2 and S <= r['L'] + 0.02 and len(new) <= len(r['pts']) - 2      # a staircase of tiny steps becomes one line
        if r['L'] - S >= MIN_GAIN or (r['off'] and S <= r['L'] + 0.05) or tidy:
            r['new'], r['S'] = new, S
            found.append(r)
            if APPLY:                                                # the next runs see this one in its new place
                for p, q in zip(new, new[1:]):
                    rt.cv.seg(r['layer'], p, q, r['w'], rt.nid(r['net']))
                rt.cv.invalidate()
    found.sort(key=lambda r: -(r['L'] - r['S']))
    print('pass %d: %-18s %-5s %7s %7s %7s %6s  %s' % (npass + 1, 'net', 'layer', 'L', 'D', 'S', 'gain', 'from -> to   (corners old -> new)'))
    for r in found:
        print('        %-18s %-5s %7.2f %7.2f %7.2f %6.2f  (%.2f,%.2f) -> (%.2f,%.2f)   %d -> %d%s' % (
            short(r['net'])[:18], r['layer'], r['L'], r['D'], r['S'], r['L'] - r['S'], *r['pts'][0], *r['pts'][-1], len(r['pts']) - 2,
            len(r['new']) - 2, '   off-angle' if r['off'] else ('   tiny steps' if r['tiny'] >= 2 else '')))
    print('        %d runs, %.1f mm' % (len(found), sum(r['L'] - r['S'] for r in found)))
    changes = [{'net': r['net'], 'layer': r['layer'], 'w': r['w'], 'old': r['pts'], 'new': r['new'], 'L': round(r['L'], 3), 'S': round(r['S'], 3),
                'key': r['key']} for r in found]
    if not APPLY:
        if JSON:
            json.dump([{k: v for k, v in ch.items() if k != 'key'} for ch in changes], open(JSON, 'w'), indent=1)
        break
    while changes:
        write_in_child(cur, TMP, changes)
        now = drc(TMP)
        fresh = {k: v for k, v in now.items() if k not in baseline}
        if not fresh:
            break
        bad = set()
        for (typ, pos), desc in fresh.items():
            hit = culprits(typ, pos, desc, changes)
            print('        DRC %-18s %s  %s -> %s' % (typ, pos, desc[:110], [short(changes[i]['net']) for i in hit] or 'no run found'))
            bad.update(hit)
        if not bad:
            raise SystemExit('violations that no change explains: stopping')
        for i in bad:
            level[changes[i]['key']] = level.get(changes[i]['key'], 0) + 1
        changes = [ch for i, ch in enumerate(changes) if i not in bad]
    if not changes:
        if not found:
            break
        continue                                                      # everything of this pass was taken back: look once more without those runs
    shutil.copy(TMP, APPLY)
    record += [{k: v for k, v in ch.items() if k != 'key'} for ch in changes]
    baseline = now
    cur = APPLY
if APPLY:
    for ext in ('.kicad_pcb', '.kicad_pro', '.kicad_dru', '.kicad_prl', '.drc.json'):
        if os.path.exists(TMP[:-10] + ext):
            os.remove(TMP[:-10] + ext)
    print('%d changes written to %s' % (len(record), APPLY))
    if JSON:
        json.dump(record, open(JSON, 'w'), indent=1)

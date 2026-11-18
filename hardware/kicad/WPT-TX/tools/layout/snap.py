#!/usr/bin/env python3
"""Track ends inside a pad or via but off its centre, second pass after weld.py. usage: snap.py BOARD_IN BOARD_OUT [--all] [--skip NET,...]

  nudge   a two-pad part moves by at most 0.05 mm when that puts its pad centres on the lines of the pieces that end in
          them and no piece that already ends on a centre is disturbed (weld.py afterwards extends the ends)
  bend    otherwise the last piece is replaced by two: on along its own line, then a 45-degree (or, failing that,
          90-degree) piece onto the centre; both pieces at least 0.1 mm long, the corner at most 0.6 mm from the old end
Offsets too small for a bend and without a possible nudge are printed and left.
"""
import math, sys, collections
import pcbnew
src, dst = sys.argv[1:3]
SKIP = set(sys.argv[sys.argv.index('--skip') + 1].split(',')) if '--skip' in sys.argv else set()
b = pcbnew.LoadBoard(src); MM = 1e6
P = lambda v: (round(v.x / MM, 4), round(v.y / MM, 4))
V = lambda p: pcbnew.VECTOR2I(int(round(p[0] * MM)), int(round(p[1] * MM)))
REFS = ('U2', 'J2', 'J3', 'J4', 'U308', 'U309', 'U306', 'SW1', 'SW2', 'SW3')
want = None
if '--all' not in sys.argv:
    want = {p.GetNetname() for r in REFS for p in b.FindFootprintByReference(r).Pads()} - {'GND', '+3V3', '+5V', ''}
EPS = 0.0015
tracks = collections.defaultdict(list); vias = collections.defaultdict(list)
for t in b.GetTracks():
    n = t.GetNetname()
    if (want is not None and n not in want) or n.split('/')[-1] in SKIP:
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        vias[n].append((P(t.GetPosition()), t.GetWidth(pcbnew.F_Cu) / 2 / MM))
    else:
        tracks[(n, t.GetLayer())].append(t)
A = lambda t: P(t.GetStart()); E = lambda t: P(t.GetEnd())
def near(p, q, tol=EPS): return math.hypot(p[0] - q[0], p[1] - q[1]) < tol
def padinfo(p):
    bb = p.GetBoundingBox()
    return (P(p.GetPosition()), (bb.GetLeft() / MM, bb.GetTop() / MM, bb.GetRight() / MM, bb.GetBottom() / MM), p.GetLayerSet())
def inside(pt, bb): return bb[0] - EPS <= pt[0] <= bb[2] + EPS and bb[1] - EPS <= pt[1] <= bb[3] + EPS
def ends_in(pad):
    """[(piece, end point, other point, degree of the end)] of the pad's net inside the pad"""
    c, bb, ls = padinfo(pad); n = pad.GetNetname(); out = []
    for (nn, L), segs in tracks.items():
        if nn != n or not ls.Contains(L): continue
        for t in segs:
            for p, o in ((A(t), E(t)), (E(t), A(t))):
                if inside(p, bb) and not inside(o, bb) or near(p, c):
                    if near(p, o): continue
                    deg = sum(1 for t2 in segs if near(A(t2), p) or near(E(t2), p))
                    out.append((t, p, o, deg))
    return c, out
def perp(c, p, o):
    l = math.hypot(p[0] - o[0], p[1] - o[1]); d = ((p[0] - o[0]) / l, (p[1] - o[1]) / l)
    return (c[0] - p[0]) * (-d[1]) + (c[1] - p[1]) * d[0], d
log = collections.Counter(); left = []
# ---------------------------------------------------------------- nudge two-pad parts
for f in b.GetFootprints():
    pads = [p for p in f.Pads() if p.GetNetname()]
    if len(f.Pads()) != 2 or len(pads) == 0: continue
    def state(v):
        bad = fixed_hit = 0
        for pad in pads:
            c, es = ends_in(pad); c2 = (c[0] + v[0], c[1] + v[1])
            for t, p, o, deg in es:
                q, d = perp(c2, p, o)
                if abs(q) < 2e-4:
                    if near(p, c) and deg > 1 and (abs(v[0]) > 1e-6 or abs(v[1]) > 1e-6): fixed_hit += 1     # a node on the centre would be left behind
                else:
                    bad += 1
                    if near(p, c): fixed_hit += 1
        return bad, fixed_hit
    bad0, _ = state((0, 0))
    if bad0 == 0: continue
    cands = []
    lines = []
    for pad in pads:
        c, es = ends_in(pad)
        for t, p, o, deg in es:
            q, d = perp(c, p, o)
            if 2e-4 <= abs(q) <= 0.05: lines.append((q, d))
    for q, d in lines: cands.append((d[1] * q, -d[0] * q))             # onto one line: v = -q * normal, normal = (-d[1], d[0])
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            (q1, d1), (q2, d2) = lines[i], lines[j]
            n1, n2 = (-d1[1], d1[0]), (-d2[1], d2[0]); det = n1[0] * n2[1] - n1[1] * n2[0]
            if abs(det) > 1e-6:                                        # v with v.n1 = -q1 and v.n2 = -q2
                cands.append(((-q1 * n2[1] + q2 * n1[1]) / det, (-n1[0] * q2 + n2[0] * q1) / det))
    best = None
    for v in cands:
        v = (round(v[0], 4), round(v[1], 4))
        if math.hypot(*v) > 0.05: continue
        bad, hit = state(v)
        if hit == 0 and bad < bad0 and (best is None or bad < best[0]): best = (bad, v)
    if best:
        pos = f.GetPosition(); f.SetPosition(pcbnew.VECTOR2I(pos.x + int(round(best[1][0] * MM)), pos.y + int(round(best[1][1] * MM))))
        log['nudge'] += 1; print('nudge %-6s %+.4f %+.4f   bad ends %d -> %d' % (f.GetReference(), best[1][0], best[1][1], bad0, best[0]))
# ---------------------------------------------------------------- bend onto the centre
DIRS = [(1, 0), (0, 1), (1, 1), (1, -1)]
targets = collections.defaultdict(list)
for f in b.GetFootprints():
    for p in f.Pads():
        c, bb, ls = padinfo(p); targets[p.GetNetname()].append((c, bb, ls, None, f.GetReference() + '.' + p.GetNumber()))
for n, lst in vias.items():
    for c, r in lst: targets[n].append((c, None, None, r, 'via'))
for (n, L), segs in sorted(tracks.items()):
    for t in list(segs):
        for p, o in ((A(t), E(t)), (E(t), A(t))):
            if near(p, o): continue
            if sum(1 for t2 in segs if near(A(t2), p) or near(E(t2), p)) > 1: continue
            tgt = None
            for c, bb, ls, r, nm in targets[n]:
                if near(p, c): tgt = None; break
                if (bb is not None and ls.Contains(L) and inside(p, bb)) or (r is not None and math.hypot(p[0] - c[0], p[1] - c[1]) <= r): tgt = (c, nm)
            else:
                if tgt is None: continue
                c, nm = tgt; q, d = perp(c, p, o)
                if abs(q) < 2e-4: continue                           # weld.py extends this one
                best = None
                for fx, fy in DIRS:
                    den = d[0] * fy - d[1] * fx
                    if abs(den) < 1e-9: continue
                    s = ((c[0] - o[0]) * fy - (c[1] - o[1]) * fx) / den
                    m = (round(o[0] + s * d[0], 4), round(o[1] + s * d[1], 4))
                    leg2 = math.hypot(c[0] - m[0], c[1] - m[1]); dist = math.hypot(m[0] - p[0], m[1] - p[1])
                    if s < 0.1 or leg2 < 0.1 or dist > 0.6: continue
                    cosang = ((c[0] - m[0]) * d[0] + (c[1] - m[1]) * d[1]) / leg2          # 0.707: 45-degree turn, 0: 90 degrees
                    if cosang < -1e-6: continue
                    key = (-round(cosang, 3), dist)
                    if best is None or key < best[0]: best = (key, m)
                if best is None:
                    left.append((n.split('/')[-1], b.GetLayerName(L), p, nm, c, round(q, 4))); continue
                m = best[1]
                if A(t) == p: t.SetStart(V(m))
                else: t.SetEnd(V(m))
                s2 = pcbnew.PCB_TRACK(b); s2.SetNet(t.GetNet()); s2.SetLayer(L); s2.SetWidth(t.GetWidth()); s2.SetStart(V(m)); s2.SetEnd(V(c)); b.Add(s2); segs.append(s2)
                log['bend'] += 1; print('bend  %-18s %-5s %s -> %s -> %s (%s)' % (n.split('/')[-1], b.GetLayerName(L), o, m, c, nm))
                break
pcbnew.SaveBoard(dst, b)
print(dict(log))
for x in left: print('  left:', x)

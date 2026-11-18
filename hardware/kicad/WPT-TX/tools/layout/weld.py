#!/usr/bin/env python3
"""Make track ends meet as nodes. usage: weld.py BOARD_IN BOARD_OUT [--all]

Repairs what joints.py reports, keeping every piece on 0 / 45 / 90 degrees:
  collinear   two pieces in one line whose ends overlap or meet at a plain point become one piece
  cross       two pieces whose ends lie in each other's copper are cut / extended to the crossing of their centre lines
  T           a piece that ends on the middle of another one: the other one is split there
  pad / via   an end inside a pad or via but off its centre: extended along its own line to the centre if the centre
              lies on that line; shifted sideways (at most 0.03 mm, the neighbouring piece follows along its own line)
              if it is that close; otherwise a new piece joins the end to the centre when that piece is on 0 / 45 / 90
Whatever cannot be done this way is left and printed. Without --all only the nets of the STM32 part (as joints.py).
Pieces are changed in place (no Remove), pieces that become superfluous get zero length and are deleted by text at the end.
"""
import math, sys, collections, re
import pcbnew
src, dst = sys.argv[1:3]
b = pcbnew.LoadBoard(src); MM = 1e6
P = lambda v: (round(v.x / MM, 4), round(v.y / MM, 4))
V = lambda p: pcbnew.VECTOR2I(int(round(p[0] * MM)), int(round(p[1] * MM)))
REFS = ('U2', 'J2', 'J3', 'J4', 'U308', 'U309', 'U306', 'SW1', 'SW2', 'SW3')
want = None
if '--all' not in sys.argv:
    want = {p.GetNetname() for r in REFS for p in b.FindFootprintByReference(r).Pads()} - {'GND', '+3V3', '+5V', ''}
EPS = 0.0015
tracks = collections.defaultdict(list); vias = collections.defaultdict(list); pads = collections.defaultdict(list)
for t in b.GetTracks():
    n = t.GetNetname()
    if want is not None and n not in want:
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        vias[n].append((P(t.GetPosition()), t.GetWidth(pcbnew.F_Cu) / 2 / MM))
    else:
        tracks[(n, t.GetLayer())].append(t)
for f in b.GetFootprints():
    for p in f.Pads():
        bb = p.GetBoundingBox()
        pads[p.GetNetname()].append((f.GetReference() + '.' + p.GetNumber(), P(p.GetPosition()), (bb.GetLeft() / MM, bb.GetTop() / MM, bb.GetRight() / MM, bb.GetBottom() / MM), p.GetLayerSet()))
dead, new, log, left = [], [], collections.Counter(), []
A = lambda t: P(t.GetStart())
E = lambda t: P(t.GetEnd())
def ends(t): return (A(t), E(t))
def setend(t, old, p):
    if A(t) == old: t.SetStart(V(p))
    else: t.SetEnd(V(p))
def other(t, p): return E(t) if A(t) == p else A(t)
def near(p, q, tol=EPS): return math.hypot(p[0] - q[0], p[1] - q[1]) < tol
def direction(t):
    a, e = ends(t); l = math.hypot(e[0] - a[0], e[1] - a[1])
    return ((e[0] - a[0]) / l, (e[1] - a[1]) / l) if l > 1e-6 else None
def cross(p, d, q, f):
    den = d[0] * f[1] - d[1] * f[0]
    if abs(den) < 1e-9: return None
    u = ((q[0] - p[0]) * f[1] - (q[1] - p[1]) * f[0]) / den
    return (round(p[0] + u * d[0], 4), round(p[1] + u * d[1], 4))
def dseg(p, a, e):
    dx, dy = e[0] - a[0], e[1] - a[1]; l2 = dx * dx + dy * dy
    u = 0 if l2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    return math.hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dy), u
def ok45(a, e):
    dx, dy = abs(e[0] - a[0]), abs(e[1] - a[1])
    return dx < 2e-4 or dy < 2e-4 or abs(dx - dy) < 2e-4
def kill(t):
    t.SetEnd(t.GetStart()); dead.append(t.m_Uuid.AsString())
def clone(t, a, e):
    s = pcbnew.PCB_TRACK(b); s.SetNet(t.GetNet()); s.SetLayer(t.GetLayer()); s.SetWidth(t.GetWidth()); s.SetStart(V(a)); s.SetEnd(V(e)); b.Add(s); return s

for (n, L), segs in sorted(tracks.items()):
    segs = [t for t in segs if direction(t) is not None]
    def live():
        for t in segs:                                                    # a piece that has shrunk to a point is gone
            if t.m_Uuid.AsString() not in dead and direction(t) is None:
                dead.append(t.m_Uuid.AsString())
        return [t for t in segs if t.m_Uuid.AsString() not in dead]
    def node(p, me=None):
        """is p a proper node besides the piece `me`?"""
        if any(near(p, c) for c, r in vias[n]) or any(ls.Contains(L) and near(p, c) for nm, c, bb, ls in pads[n]): return True
        return any(t is not me and (near(A(t), p) or near(E(t), p)) for t in live())
    def degree(p): return sum(1 for t in live() if near(A(t), p) or near(E(t), p))
    for rnd in range(4):
        changed = False
        for t in live():
            for p in ends(t):
                d = direction(t)
                if d is None: break
                if node(p, t): continue
                # pad or via centre
                tgt = None
                for nm, c, bb, ls in pads[n]:
                    if ls.Contains(L) and bb[0] - EPS <= p[0] <= bb[2] + EPS and bb[1] - EPS <= p[1] <= bb[3] + EPS: tgt = c
                for c, r in vias[n]:
                    if math.hypot(p[0] - c[0], p[1] - c[1]) <= r: tgt = c
                if tgt is not None:
                    v = (tgt[0] - p[0], tgt[1] - p[1]); perp = v[0] * (-d[1]) + v[1] * d[0]
                    if abs(perp) < 2e-4:
                        setend(t, p, tgt); log['extend'] += 1; changed = True
                    elif abs(perp) <= 0.25:
                        o = other(t, p); nb = [t2 for t2 in live() if t2 is not t and (near(A(t2), o) or near(E(t2), o))]
                        sh = (-d[1] * perp, d[0] * perp)
                        if len(nb) == 1 and not any(near(o, c) for c, r in vias[n]) and not any(ls.Contains(L) and near(o, c) for nm, c, bb, ls in pads[n]):
                            x = cross((o[0] + sh[0], o[1] + sh[1]), d, A(nb[0]), direction(nb[0]))
                            if x:
                                setend(nb[0], o, x); setend(t, o, x); setend(t, p, tgt); log['shift'] += 1; changed = True; continue
                        if ok45(p, tgt) and math.hypot(v[0], v[1]) > 0.05:
                            segs.append(clone(t, p, tgt)); log['joined'] += 1; changed = True
                        else:
                            left.append(('pad/via off by %.3f, no free neighbour' % perp, n, b.GetLayerName(L), p, tgt))
                    elif ok45(p, tgt):
                        segs.append(clone(t, p, tgt)); log['joined'] += 1; changed = True
                    else:
                        left.append(('pad/via centre not on 45', n, b.GetLayerName(L), p, tgt))
                    continue
                # other pieces whose copper holds this end
                hit = None
                for t2 in live():
                    if t2 is t or any(near(q, r) for q in ends(t) for r in ends(t2)): continue      # already joined at a node
                    dist, u = dseg(p, A(t2), E(t2))
                    if dist <= (t.GetWidth() + t2.GetWidth()) / 2 / MM + 1e-6: hit = (t2, dist, u); break
                if hit:
                    t2, dist, u = hit; d2 = direction(t2)
                    par = abs(d[0] * d2[1] - d[1] * d2[0]) < 1e-6
                    if par and dist < EPS:                                   # same line, ends overlap: one piece
                        pts = sorted([A(t), E(t), A(t2), E(t2)], key=lambda q: q[0] * d[0] + q[1] * d[1])
                        inner = pts[1:3]
                        if all(not node(q, t) or q in ends(t2) for q in inner if q in ends(t)) and t.GetWidth() == t2.GetWidth() \
                                and not any(node(q, t2) and not near(q, p) and degree(q) > 1 for q in inner if q in ends(t2)):
                            t.SetStart(V(pts[0])); t.SetEnd(V(pts[3])); kill(t2); log['collinear'] += 1; changed = True; break
                    if par and EPS <= dist <= 0.12:
                        o = other(t, p); nb = [t3 for t3 in live() if t3 is not t and (near(A(t3), o) or near(E(t3), o))]
                        q = min(ends(t2), key=lambda q: math.hypot(q[0] - p[0], q[1] - p[1]))
                        perp = (q[0] - p[0]) * (-d[1]) + (q[1] - p[1]) * d[0]
                        sh = (-d[1] * perp, d[0] * perp)
                        if len(nb) == 1 and not any(near(o, c) for c, r in vias[n]) and not any(ls.Contains(L) and near(o, c) for nm, c, bb, ls in pads[n]):
                            x = cross((o[0] + sh[0], o[1] + sh[1]), d, A(nb[0]), direction(nb[0]))
                            if x:
                                setend(nb[0], o, x); setend(t, o, x); setend(t, p, q); log['side'] += 1; changed = True; break
                    if not par:
                        x = cross(A(t), d, A(t2), d2)
                        if x and math.hypot(x[0] - p[0], x[1] - p[1]) < 0.4:
                            du, uu = dseg(x, A(t2), E(t2))
                            setend(t, p, x)
                            if du > EPS:                                     # the crossing lies beyond the end of the other piece: it follows
                                q = min(ends(t2), key=lambda q: math.hypot(q[0] - x[0], q[1] - x[1]))
                                if degree(q) == 1: setend(t2, q, x)
                            elif 1e-4 < uu < 1 - 1e-4 and not near(x, A(t2)) and not near(x, E(t2)):
                                e2 = E(t2); t2.SetEnd(V(x)); segs.append(clone(t2, x, e2))      # T: split
                            log['cross'] += 1; changed = True; break
            if changed: break
        if not changed: break
    # two pieces in one line meeting at a plain point
    again = True
    while again:
        again = False
        for t in live():
            for p in ends(t):
                if any(near(p, c) for c, r in vias[n]) or any(ls.Contains(L) and near(p, c) for nm, c, bb, ls in pads[n]): continue
                nb = [t2 for t2 in live() if t2 is not t and (near(A(t2), p) or near(E(t2), p))]
                if len(nb) == 1 and nb[0].GetWidth() == t.GetWidth():
                    d, d2 = direction(t), direction(nb[0])
                    if d and d2 and abs(d[0] * d2[1] - d[1] * d2[0]) < 1e-6:
                        a, e = other(t, p), other(nb[0], p)
                        if not near(a, e):
                            t.SetStart(V(a)); t.SetEnd(V(e)); kill(nb[0]); log['merged'] += 1; again = True; break
            if again: break
for t in b.GetTracks():
    if t.Type() != pcbnew.PCB_VIA_T and t.GetStart() == t.GetEnd() and t.m_Uuid.AsString() not in dead:
        dead.append(t.m_Uuid.AsString())
pcbnew.SaveBoard(dst, b)
txt = open(dst, encoding='utf-8').read().split('\n'); out = []; i = 0; gone = 0
while i < len(txt):
    if txt[i] == '\t(segment':
        j = i
        while txt[j] != '\t)': j += 1
        blk = '\n'.join(txt[i:j + 1]); m = re.search(r'\(uuid "([^"]+)"\)', blk)
        if m and m.group(1) in dead:
            gone += 1; i = j + 1; continue
    out.append(txt[i]); i += 1
open(dst, 'w', encoding='utf-8').write('\n'.join(out))
print(dict(log), 'pieces removed', gone)
for x in sorted(set(left)): print('  left:', x)

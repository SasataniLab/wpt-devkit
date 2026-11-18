#!/usr/bin/env python3
"""Track ends that are connected only by overlap. usage: joints.py BOARD [--all]

A track end is a proper joint when it sits exactly on the end of another track of its net and layer, on the centre of
a via of its net, or on the centre of a pad of its net. Reported:
  OFFPAD   the end lies inside a pad but not on its centre
  OFFVIA   the end lies inside a via but not on its centre
  MID      the end lies on the middle of another track (a T without a node)
  OVERLAP  the end lies inside the copper of another track without touching its centre line
  OPEN     none of these (a dangling end)
Also: COLLINEAR = two pieces in one straight line that meet at a point where nothing else is attached.
Without --all only nets with at least one pad on U2, J2, J3, J4, U308, U309, U306 or SW1..SW3 are listed (the STM32 part).
"""
import math, sys, collections
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); MM = 1e6
P = lambda v: (round(v.x / MM, 4), round(v.y / MM, 4))
REFS = ('U2', 'J2', 'J3', 'J4', 'U308', 'U309', 'U306', 'SW1', 'SW2', 'SW3')
want = None
if '--all' not in sys.argv:
    want = {p.GetNetname() for r in REFS for p in b.FindFootprintByReference(r).Pads()} - {'GND', '+3V3', '+5V', ''}
tr = collections.defaultdict(list); vias = collections.defaultdict(list); pads = collections.defaultdict(list)
for t in b.GetTracks():
    n = t.GetNetname()
    if t.Type() == pcbnew.PCB_VIA_T:
        vias[n].append((P(t.GetPosition()), t.GetWidth(pcbnew.F_Cu) / 2 / MM))
    else:
        tr[(n, t.GetLayer())].append((P(t.GetStart()), P(t.GetEnd()), t.GetWidth() / MM))
for f in b.GetFootprints():
    for p in f.Pads():
        bb = p.GetBoundingBox()
        pads[p.GetNetname()].append((f.GetReference() + '.' + p.GetNumber(), P(p.GetPosition()), (bb.GetLeft() / MM, bb.GetTop() / MM, bb.GetRight() / MM, bb.GetBottom() / MM), p.GetLayerSet()))
def dseg(p, a, e):
    dx, dy = e[0] - a[0], e[1] - a[1]; l2 = dx * dx + dy * dy
    u = 0 if l2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    return math.hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dy)
EPS = 0.0015
out = collections.Counter()
for (n, L), segs in sorted(tr.items()):
    if want is not None and n not in want:
        continue
    ends = collections.Counter()
    for a, e, w in segs:
        ends[a] += 1; ends[e] += 1
    for i, (a, e, w) in enumerate(segs):
        for pt in (a, e):
            if ends[pt] > 1 or any(math.hypot(pt[0] - c[0], pt[1] - c[1]) < EPS for c, r in vias[n]):
                continue
            if any(ls.Contains(L) and math.hypot(pt[0] - c[0], pt[1] - c[1]) < EPS for nm, c, bb, ls in pads[n]):
                continue
            kind, where = 'OPEN', ''
            for nm, c, bb, ls in pads[n]:
                if ls.Contains(L) and bb[0] - EPS <= pt[0] <= bb[2] + EPS and bb[1] - EPS <= pt[1] <= bb[3] + EPS:
                    kind, where = 'OFFPAD', '%s centre %s' % (nm, c)
            if kind == 'OPEN':
                for c, r in vias[n]:
                    if math.hypot(pt[0] - c[0], pt[1] - c[1]) <= r:
                        kind, where = 'OFFVIA', str(c)
            if kind == 'OPEN':
                for j, (a2, e2, w2) in enumerate(segs):
                    if j != i:
                        d = dseg(pt, a2, e2)
                        if d < EPS:
                            kind, where = 'MID', '%s-%s' % (a2, e2); break
                        if d <= (w + w2) / 2:
                            kind, where = 'OVERLAP', '%s-%s' % (a2, e2)
            out[kind] += 1
            print('%-8s %-22s %-5s %s  (piece %s-%s) %s' % (kind, n.split('/')[-1], b.GetLayerName(L), pt, a, e, where))
    # collinear pieces meeting at a plain point
    at = collections.defaultdict(list)
    for a, e, w in segs:
        at[a].append((a, e, w)); at[e].append((e, a, w))
    for pt, lst in at.items():
        if len(lst) == 2 and lst[0][2] == lst[1][2] and not any(math.hypot(pt[0] - c[0], pt[1] - c[1]) < EPS for c, r in vias[n]) \
                and not any(math.hypot(pt[0] - c[0], pt[1] - c[1]) < EPS for nm, c, bb, ls in pads[n]):
            (p0, q0, _), (p1, q1, _) = lst
            cr = (q0[0] - pt[0]) * (q1[1] - pt[1]) - (q0[1] - pt[1]) * (q1[0] - pt[0])
            dot = (q0[0] - pt[0]) * (q1[0] - pt[0]) + (q0[1] - pt[1]) * (q1[1] - pt[1])
            if abs(cr) < 1e-6 and dot < 0:
                out['COLLINEAR'] += 1
                print('COLLINEAR %-21s %-5s %s' % (n.split('/')[-1], b.GetLayerName(L), pt))
print(dict(out))

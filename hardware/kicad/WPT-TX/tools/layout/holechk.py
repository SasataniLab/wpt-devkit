#!/usr/bin/env python3
"""What is near the mounting holes? usage: holechk.py BOARD [R_COPPER R_PART]

For every mounting hole (footprints without a schematic symbol that carry a drilled pad of 2 mm or more) lists
  * tracks and vias of nets other than the hole's own net whose copper comes closer to the hole centre than R_COPPER
    (default: M3 -> 3.6 mm, the reach of a 7 mm washer plus 0.1 mm; smaller holes -> drill/2 + 2.0 mm)
  * pads of other footprints closer than R_PART (same radii), on either side
A washer, screw head or the hexagon of a standoff bears on the solder mask there; a signal track under it can end up shorted to the screw.
"""
import math
import sys

import pcbnew

MM = 1e-6
b = pcbnew.LoadBoard(sys.argv[1])
short = lambda n: n.split('/')[-1]


def dseg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


holes = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        d = p.GetDrillSize().x * MM
        if d >= 2.0 and (fp.GetReference().startswith('REF') or fp.GetPath().AsString() in ('', '/')):
            holes.append((fp, p, d))
bad = 0
for fp, p, d in holes:
    cx, cy = p.GetPosition().x * MM, p.GetPosition().y * MM
    R = float(sys.argv[2]) if len(sys.argv) > 2 else (3.6 if d >= 3.0 else d / 2 + 2.0)
    pad_d = p.GetSize(pcbnew.F_Cu).x * MM
    print('hole %s at (%.2f, %.2f)  drill %.2f  pad %.2f  net %s  check radius %.2f' % (fp.GetReference(), cx, cy, d, pad_d, p.GetNetname() or '-', R))
    own = p.GetNetname()
    for t in b.GetTracks():
        if t.GetNetname() == own:
            continue
        w = t.GetWidth() * MM if t.Type() != pcbnew.PCB_VIA_T else t.GetWidth(pcbnew.F_Cu) * MM
        if t.Type() == pcbnew.PCB_VIA_T:
            dist = math.hypot(t.GetPosition().x * MM - cx, t.GetPosition().y * MM - cy) - w / 2
            what = 'via'
        else:
            a, e = t.GetStart(), t.GetEnd()
            dist = dseg(cx, cy, a.x * MM, a.y * MM, e.x * MM, e.y * MM) - w / 2
            what = 'track ' + b.GetLayerName(t.GetLayer())
        if dist < R:
            bad += 1
            print('    %-12s %-22s copper reaches %.2f mm from the centre' % (what, short(t.GetNetname()), dist))
    for f2 in b.GetFootprints():
        if f2 is fp:
            continue
        for q in f2.Pads():
            sz = q.GetSize(pcbnew.F_Cu)
            dist = math.hypot(q.GetPosition().x * MM - cx, q.GetPosition().y * MM - cy) - min(sz.x, sz.y) * MM / 2
            if dist < R:
                bad += 1
                print('    pad %s.%s (%s, %s side) reaches about %.2f mm from the centre' % (f2.GetReference(), q.GetNumber(), short(q.GetNetname()) or 'no net', 'B' if f2.IsFlipped() else 'F', dist))
print('items inside the check radii:', bad)

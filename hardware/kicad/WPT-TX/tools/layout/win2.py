#!/usr/bin/env python3
"""List copper inside a window: win2.py BOARD x0 y0 x1 y1 [layer]"""
import sys
import pcbnew
MM = 1e-6
b = pcbnew.LoadBoard(sys.argv[1])
x0, y0, x1, y1 = map(float, sys.argv[2:6])
only = sys.argv[6] if len(sys.argv) > 6 else None
short = lambda n: n.split('/')[-1]
def clip(ax, ay, bx, by):
    # does the segment touch the window?
    if max(ax, bx) < x0 or min(ax, bx) > x1 or max(ay, by) < y0 or min(ay, by) > y1:
        return False
    n = 40
    return any(x0 <= ax + (bx - ax) * i / n <= x1 and y0 <= ay + (by - ay) * i / n <= y1 for i in range(n + 1))
rows = []
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        if x0 <= p.x * MM <= x1 and y0 <= p.y * MM <= y1:
            rows.append(('via', short(t.GetNetname()), '(%.2f,%.2f)' % (p.x * MM, p.y * MM), 'd%.2f' % (t.GetWidth(pcbnew.F_Cu) * MM)))
    else:
        ln = b.GetLayerName(t.GetLayer())
        if only and ln != only:
            continue
        a, e = t.GetStart(), t.GetEnd()
        if clip(a.x * MM, a.y * MM, e.x * MM, e.y * MM):
            rows.append((ln, short(t.GetNetname()), '(%.2f,%.2f)-(%.2f,%.2f)' % (a.x * MM, a.y * MM, e.x * MM, e.y * MM), 'w%.2f' % (t.GetWidth() * MM)))
for fp in b.GetFootprints():
    for p in fp.Pads():
        c = p.GetPosition()
        if x0 <= c.x * MM <= x1 and y0 <= c.y * MM <= y1:
            s = p.GetSize()
            lay = 'F' if p.IsOnLayer(pcbnew.F_Cu) else ''
            lay += 'B' if p.IsOnLayer(pcbnew.B_Cu) else ''
            rows.append(('pad' + lay, short(p.GetNetname()), '%s.%s (%.2f,%.2f)' % (fp.GetReference(), p.GetNumber(), c.x * MM, c.y * MM), '%.2fx%.2f r%g' % (s.x * MM, s.y * MM, fp.GetOrientationDegrees())))
for r in sorted(rows):
    print('%-6s %-22s %-34s %s' % r)

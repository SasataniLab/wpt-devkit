#!/usr/bin/env python3
"""List copper in a window. usage: win.py BOARD x0 y0 x1 y1 [layer]"""
import sys
import pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1])
x0, y0, x1, y1 = map(float, sys.argv[2:6])
lay = sys.argv[6] if len(sys.argv) > 6 else None
inside = lambda x, y: x0 <= x <= x1 and y0 <= y <= y1
for t in b.GetTracks():
    net = t.GetNetname().split('/')[-1]
    if t.GetClass() == 'PCB_VIA':
        c = (t.GetPosition().x / MM, t.GetPosition().y / MM)
        if inside(*c):
            print('VIA', net, c)
    else:
        ln = b.GetLayerName(t.GetLayer())
        a = (round(t.GetStart().x / MM, 3), round(t.GetStart().y / MM, 3)); e = (round(t.GetEnd().x / MM, 3), round(t.GetEnd().y / MM, 3))
        if (lay is None or ln == lay) and (inside(*a) or inside(*e)) and t.GetLength() / MM >= 0.2:
            print(ln, net, a, e, t.GetWidth() / MM)
for fp in b.GetFootprints():
    for p in fp.Pads():
        c = (round(p.GetPosition().x / MM, 3), round(p.GetPosition().y / MM, 3))
        if inside(*c):
            bb = p.GetBoundingBox()
            print('PAD', fp.GetReference(), p.GetNumber(), p.GetNetname().split('/')[-1], c, 'bbox', round(bb.GetLeft() / MM, 2), round(bb.GetTop() / MM, 2), round(bb.GetRight() / MM, 2), round(bb.GetBottom() / MM, 2), 'THT' if p.GetDrillSize().x else [b.GetLayerName(l) for l in p.GetLayerSet().Seq() if b.GetLayerName(l).endswith('.Cu')][0], p.GetShape(pcbnew.F_Cu))

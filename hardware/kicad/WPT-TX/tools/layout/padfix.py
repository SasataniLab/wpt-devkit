#!/usr/bin/env python3
"""Extend tracks that end exactly on the edge of an MCU pad to the pad centre (KiCad counts an end on the edge as dangling).

usage: padfix.py BOARD [REF ...]
"""
import sys

import pcbnew

MM = 1e6
path = sys.argv[1]
refs = sys.argv[2:] or ['U2']
b = pcbnew.LoadBoard(path)
tracks = [t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA']
n = 0
for ref in refs:
    fp = b.FindFootprintByReference(ref)
    for pad in fp.Pads():
        net = pad.GetNetname()
        if not net or net.startswith('unconnected'):
            continue
        bb = pad.GetBoundingBox()
        x0, y0, x1, y1 = bb.GetLeft() / MM, bb.GetTop() / MM, bb.GetRight() / MM, bb.GetBottom() / MM
        c = pad.GetPosition()
        lay = [l for l in pad.GetLayerSet().Seq() if b.GetLayerName(l).endswith('.Cu')][0]
        for t in tracks:
            if t.GetNetname() != net or t.GetLayer() != lay:
                continue
            for p in (t.GetStart(), t.GetEnd()):
                x, y = p.x / MM, p.y / MM
                on_box = x0 - 0.03 <= x <= x1 + 0.03 and y0 - 0.03 <= y <= y1 + 0.03
                deep = x0 + 0.06 <= x <= x1 - 0.06 and y0 + 0.06 <= y <= y1 - 0.06
                if on_box and not deep and (abs(x - c.x / MM) > 0.05 or abs(y - c.y / MM) > 0.05):
                    s = pcbnew.PCB_TRACK(b)
                    s.SetStart(pcbnew.VECTOR2I(p.x, p.y))
                    s.SetEnd(pcbnew.VECTOR2I(c.x, c.y))
                    s.SetWidth(int(0.2 * MM))
                    s.SetLayer(lay)
                    s.SetNet(pad.GetNet())
                    b.Add(s)
                    n += 1
print('pad-edge track ends extended to the pad centre:', n)
pcbnew.SaveBoard(path, b)

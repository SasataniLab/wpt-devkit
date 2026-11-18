#!/usr/bin/env python3
"""List ground pour pieces on the outer layers that contain no ground via / through-hole pad. usage: islands.py BOARD"""
import sys
import numpy as np
import pcbnew
from matplotlib.path import Path
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1])
anch, smd, trk = [], [], []
for t in b.GetTracks():
    if t.GetNetname() != 'GND':
        continue
    if t.GetClass() == 'PCB_VIA':
        anch.append((t.GetPosition().x / MM, t.GetPosition().y / MM))
    else:
        trk.append(((t.GetStart().x / MM, t.GetStart().y / MM), b.GetLayerName(t.GetLayer())))
        trk.append(((t.GetEnd().x / MM, t.GetEnd().y / MM), b.GetLayerName(t.GetLayer())))
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() != 'GND':
            continue
        p = (pad.GetPosition().x / MM, pad.GetPosition().y / MM)
        if pad.GetDrillSize().x > 0:
            anch.append(p)
        else:
            lay = [b.GetLayerName(l) for l in pad.GetLayerSet().Seq() if b.GetLayerName(l).endswith('.Cu')][0]
            smd.append((p, lay, fp.GetReference() + '.' + pad.GetNumber()))
anch = np.array(anch)
for z in b.Zones():
    if z.GetNetname() != 'GND' or z.GetIsRuleArea():
        continue
    for li in z.GetLayerSet().Seq():
        ln = b.GetLayerName(li)
        if ln not in ('F.Cu', 'B.Cu'):
            continue
        polys = z.GetFilledPolysList(li)
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            pts = np.array([(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())])
            if len(pts) < 3:
                continue
            pth = Path(pts)
            if pth.contains_points(anch, radius=0.75).any() or pth.contains_points(anch, radius=-0.75).any():
                continue
            area = 0.5 * abs(np.dot(pts[:, 0], np.roll(pts[:, 1], 1)) - np.dot(pts[:, 1], np.roll(pts[:, 0], 1)))
            near = [s[2] for s in smd if s[1] == ln and (pth.contains_point(s[0], radius=0.6) or pth.contains_point(s[0], radius=-0.6))]
            tr = sum(1 for p, l in trk if l == ln and (pth.contains_point(p, radius=0.2) or pth.contains_point(p, radius=-0.2)))
            if area > 0.05:
                print(ln, 'area', round(area, 2), 'bbox', [round(float(v), 2) for v in (*pts.min(axis=0), *pts.max(axis=0))], 'SMD pads:', near, 'GND track ends on it:', tr)

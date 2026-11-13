#!/usr/bin/env python3
"""Clean-up after routing: plane stubs, ground stitching of isolated pour islands, starved thermals, dangling copper.

usage: post_route.py BOARD [passes]
"""
import collections
import math
import re
import sys

import numpy as np
import pcbnew
from matplotlib.path import Path
from scipy import ndimage

import router as R

MM = 1e6
path = sys.argv[1]
passes = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 3
NEW_PREFIX_OK = None      # filled below: references of parts placed in this work


def blocks_of(txt):
    return [b for b in re.split(r'\n(?=\[)', txt) if b.startswith('[')]


def items(b):
    out = []
    for line in b.split('\n'):
        m = R.ITEM.search(line)
        if m:
            out.append((float(m.group(1)), float(m.group(2)), m.group(3)))
    return out


def stitch_islands(r):
    """Add a GND via to every outer-layer ground pour island that has no via / through-hole pad of its own."""
    b = r.board
    gnd_pts = []
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND':
            gnd_pts.append((t.GetPosition().x / MM, t.GetPosition().y / MM))
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == 'GND' and pad.GetDrillSize().x > 0:
                gnd_pts.append((pad.GetPosition().x / MM, pad.GetPosition().y / MM))
    gnd_pts = np.array(gnd_pts)
    added = 0
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
                x0, y0 = pts.min(axis=0)
                x1, y1 = pts.max(axis=0)
                area = 0.5 * abs(np.dot(pts[:, 0], np.roll(pts[:, 1], 1)) - np.dot(pts[:, 1], np.roll(pts[:, 0], 1)))
                if area < 0.6 or area > 400:
                    continue
                pth = Path(pts)
                if len(gnd_pts) and pth.contains_points(gnd_pts, radius=0.3).any():
                    continue
                # candidate cells inside the island, far enough from its edge and legal for a via
                ix0, iy0 = max(0, int((x0 - R.X0) / R.RES)), max(0, int((y0 - R.Y0) / R.RES))
                ix1, iy1 = min(R.W, int((x1 - R.X0) / R.RES) + 2), min(R.H, int((y1 - R.Y0) / R.RES) + 2)
                if ix1 - ix0 < 8 or iy1 - iy0 < 8:
                    continue
                free, via_ok, own = r.maps('GND', (ix0, iy0, ix1, iy1))
                yy, xx = np.mgrid[iy0:iy1, ix0:ix1]
                cx = R.X0 + xx * R.RES
                cy = R.Y0 + yy * R.RES
                inside = pth.contains_points(np.column_stack([cx.ravel(), cy.ravel()])).reshape(cx.shape)
                for h in range(polys.HoleCount(i)):
                    ho = polys.Hole(i, h)
                    hp = Path(np.array([(ho.CPoint(k).x / MM, ho.CPoint(k).y / MM) for k in range(ho.PointCount())]))
                    inside &= ~hp.contains_points(np.column_stack([cx.ravel(), cy.ravel()])).reshape(cx.shape)
                if not inside.any():
                    continue
                depth = ndimage.distance_transform_edt(inside) * R.RES
                cand = via_ok & (depth >= 0.4)
                if not cand.any():
                    continue
                k = np.argmax(np.where(cand, depth, -1))
                py, pxx = np.unravel_index(k, cand.shape)
                pos = (round(float(cx[py, pxx]), 3), round(float(cy[py, pxx]), 3))
                r.add_via('GND', pos)
                gnd_pts = np.vstack([gnd_pts, pos]) if len(gnd_pts) else np.array([pos])
                added += 1
    return added


for it in range(passes):
    txt = R.run_drc(path, path.replace('.kicad_pcb', f'_post{it}.rpt'))
    bl = blocks_of(txt)
    cnt = collections.Counter(b.split(']')[0][1:] for b in bl)
    print(f'--- post pass {it}:', {k: v for k, v in cnt.items() if k in ('unconnected_items', 'starved_thermal', 'track_dangling', 'via_dangling', 'clearance', 'shorting_items', 'hole_clearance', 'solder_mask_bridge')})
    r = R.Router(path)
    b = r.board
    changed = 0

    # 1. plane nets: SMD pad that only hangs on a pour -> its own stub and via
    for a, c in R.parse_unconnected(txt):
        if a['net'] not in ('GND', '+3V3'):
            continue
        for itx in (a, c):
            if itx['kind'] == 'Pad' and len(itx['layers']) == 1:
                if r.stub_via(a['net'], itx['x'], itx['y'], itx['layers'][0], max_len=6.0):
                    changed += 1
    # 2. ground islands
    n = stitch_islands(r)
    changed += n
    # 3. starved thermals on the small SMD ground pads: connect solid
    for blk in bl:
        if not blk.startswith('[starved_thermal]'):
            continue
        for x, y, desc in items(blk):
            m = re.search(r'Pad (\S+) \[GND\] of (\S+) on', desc)
            if not m:
                continue
            fp = b.FindFootprintByReference(m.group(2))
            if fp is None or m.group(2) in ('U201', 'U207'):
                continue          # the two legacy regulators keep their thermal pads as they were
            for pad in fp.Pads():
                if pad.GetNumber() == m.group(1) and pad.GetNetname() == 'GND':
                    pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
                    changed += 1
    # 4. dangling stubs (only on request: on a net that is still open this eats into good copper)
    kill = []
    for blk in bl:
        kind = blk.split(']')[0][1:]
        if '--dangling' not in sys.argv or kind not in ('track_dangling', 'via_dangling'):
            continue
        its = items(blk)
        if not its:
            continue
        x, y, desc = its[0]
        net = re.search(r'\[([^\]]*)\]', desc).group(1)
        for t in b.GetTracks():
            if t.GetNetname() != net:
                continue
            if kind == 'via_dangling' and t.GetClass() == 'PCB_VIA':
                if abs(t.GetPosition().x / MM - x) < 0.003 and abs(t.GetPosition().y / MM - y) < 0.003:
                    kill.append(t)
            elif kind == 'track_dangling' and t.GetClass() != 'PCB_VIA':
                for p in (t.GetStart(), t.GetEnd()):
                    if abs(p.x / MM - x) < 0.003 and abs(p.y / MM - y) < 0.003:
                        kill.append(t)
                        break
    seen = set()
    for t in kill:
        if id(t) not in seen:
            seen.add(id(t))
            b.Remove(t)
            changed += 1
    r.save()
    print(f'    stubs+stitching+fixes applied: {changed} (islands stitched {n}, dangling removed {len(seen)})')
    if not changed:
        break
txt = R.run_drc(path, path.replace('.kicad_pcb', '_post_final.rpt'))
cnt = collections.Counter(b.split(']')[0][1:] for b in blocks_of(txt))
print('final:', dict(cnt))

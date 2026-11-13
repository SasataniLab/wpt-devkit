#!/usr/bin/env python3
"""Give every surface-mount GND / +3V3 pad in the reworked area its own via when it only hangs on a copper pour.

usage: planefix.py BOARD
"""
import sys

import pcbnew

import router as R

R.DEFAULT_CORRIDORS = ()
MM = 1e6
path = sys.argv[1]
WIN = (150.0, 135.0, 200.0, 168.0)
r = R.Router(path)
b = r.board
ends = {}
for t in b.GetTracks():
    net = t.GetNetname()
    if net not in ('GND', '+3V3'):
        continue
    if t.GetClass() == 'PCB_VIA':
        ends.setdefault(net, []).append((t.GetPosition().x / MM, t.GetPosition().y / MM, None))
    else:
        ln = b.GetLayerName(t.GetLayer())
        for p in (t.GetStart(), t.GetEnd()):
            ends.setdefault(net, []).append((p.x / MM, p.y / MM, ln))
todo = []
for fp in b.GetFootprints():
    for pad in fp.Pads():
        net = pad.GetNetname()
        if net not in ('GND', '+3V3') or pad.GetDrillSize().x > 0:
            continue
        x, y = pad.GetPosition().x / MM, pad.GetPosition().y / MM
        if not (WIN[0] <= x <= WIN[2] and WIN[1] <= y <= WIN[3]):
            continue
        layer = [b.GetLayerName(l) for l in pad.GetLayerSet().Seq() if b.GetLayerName(l).endswith('.Cu')][0]
        bb = pad.GetBoundingBox()
        x0, y0, x1, y1 = bb.GetLeft() / MM - 0.05, bb.GetTop() / MM - 0.05, bb.GetRight() / MM + 0.05, bb.GetBottom() / MM + 0.05
        wired = any(x0 <= ex <= x1 and y0 <= ey <= y1 and (el is None or el == layer) for ex, ey, el in ends.get(net, []))
        if not wired:
            todo.append((fp.GetReference(), pad.GetNumber(), net, x, y, layer))
ok = bad = 0
for ref, num, net, x, y, layer in todo:
    if r.stub_via(net, x, y, layer, max_len=6.0):
        ok += 1
    else:
        bad += 1
        print('   no via site for', ref, num, net, (x, y), layer)
r.save()
print(f'pads that only hung on a pour: {len(todo)}; via added for {ok}, failed {bad}')

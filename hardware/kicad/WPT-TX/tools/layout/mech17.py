#!/usr/bin/env python3
"""Revision 7b: ADC_VDC takes the inner layer past the encoder. usage: mech17.py BOARD_IN BOARD_OUT
(BOARD_IN = board after shorten_rev7b.json)

The line from the input divider (R201 / R202) to PA1x of the MCU went round the west side of the encoder with four
layer changes: 82.8 mm, 6 vias. On the outer layers nothing shorter exists (router.py with everything else in place
finds 80 mm and 7 vias). With 14.7 mm on In2 (+3V3 plane, between the encoder and the MCU where only slow lines cross)
it is 67 mm and 4 vias. The path follows what router.py found (inner=True), drawn here as 0 / 45 / 90 degree pieces.
"""
import re, sys
import pcbnew
import newfp
from newfp import P
src, dst = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
net = [str(k) for k in b.GetNetInfo().NetsByName().keys() if str(k).split('/')[-1] == 'ADC_VDC'][0]
dead, south = [], None
for t in b.GetTracks():
    if t.GetNetname() != net:
        continue
    a, e = P(t.GetStart()), P(t.GetEnd())
    if all(p[0] > 182.1 for p in (a, e)) or all(p[1] > 181.0 for p in (a, e)):      # the MCU end and the divider end stay
        for p in (a, e):
            if abs(p[0] - 160.15) < 1e-3 and p[1] < 182: south = p
        continue
    dead.append(t.m_Uuid.AsString())
assert south is not None and len(dead) == 23, (south, len(dead))
V1, V2 = (166.75, 162.95), (173.3, 150.95)
newfp.seg(b, net, [south, (160.15, 172.7), (162.5, 170.35), (162.5, 169.45), (164.05, 167.9), (164.05, 166.25), (166.75, 163.55), V1], layer='B.Cu')
newfp.via(b, net, V1)
newfp.seg(b, net, [V1, (169.45, 160.25), (169.45, 158.15), (169.95, 157.65), (169.95, 155.25), (171.05, 154.15), (171.05, 153.25), (173.3, 151.0), V2], layer='In2.Cu')
newfp.via(b, net, V2)
newfp.seg(b, net, [V2, (175.8, 150.95), (176.5, 151.65), (182.15, 151.65), (182.5, 151.3)], layer='B.Cu')
pcbnew.SaveBoard(dst, b)
txt = open(dst, encoding='utf-8').read().split('\n'); out = []; i = 0; gone = 0
while i < len(txt):
    if txt[i] in ('\t(segment', '\t(via'):
        j = i
        while txt[j] != '\t)':
            j += 1
        m = re.search(r'\(uuid "([^"]+)"\)', '\n'.join(txt[i:j + 1]))
        if m and m.group(1) in dead:
            gone += 1; i = j + 1; continue
    out.append(txt[i]); i += 1
open(dst, 'w', encoding='utf-8').write('\n'.join(out))
print('pieces and vias removed', gone)

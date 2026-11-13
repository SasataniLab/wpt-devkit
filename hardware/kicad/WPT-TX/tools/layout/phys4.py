#!/usr/bin/env python3
"""Leg-A sense line: straight up the gap between the two gate-signal pairs, on the back, without a via.

usage: phys4.py BOARD_IN REG_IN.json BOARD_OUT REG_OUT.json

Before: the tap of the leg-A divider reached R343 (at the MCU) by going 10 mm south, over the leg-A gate pair on the
top side, and 28 mm north again beside those gate signals: 42.5 mm, 2 vias.
The four gate signals change from the top side to the back in one cluster of vias; south of that cluster leg A runs
south and leg B south-east, and the divider of leg A sits in the wedge between them. Opening a 0.85 mm gap between the
via pairs lets the sense line stay in that wedge all the way: 18 mm, no via, and beside a gate signal only for the
2.5 mm of the via cluster (0.55 mm gap).
  * leg-B gate signals (top-side trunk south of the MCU, their vias and the first part of their back-side run) move
    0.8 mm east; both by the same amount, so the pair stays matched
  * the legacy clock line (only used when the Si5351 variant is fitted) moves east with them
  * J301 branch of the same net: starts at the T next to R343 and crosses the comparator line of leg B on the top side
"""
import json
import shutil
import sys

import pcbnew

import router as R
from nego import rip_text

R.DEFAULT_CORRIDORS = ()
MM = 1e6
src, regin, dst, regout = sys.argv[1:5]
shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)
P = lambda v: (round(v.x / MM, 3), round(v.y / MM, 3))
T, VK = R.Router.tkey, R.Router.vkey
net = lambda s: [str(n) for n in b.GetNetsByName().asdict().keys() if str(n).split('/')[-1] == s][0]
N = {s: net(s) for s in ('HRTIM1_CHD1', 'HRTIM1_CHD2', 'Net-(U301-A)', 'VSWA_SENSE')}
pad = lambda ref, num: [P(p.GetPosition()) for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
r343_2, c338_2 = pad('R343', '2'), pad('C338', '2')

kill = set()
k = lambda n, lay, a, e: kill.add(T(N[n], lay, a, e))
# leg-B gate signals between the end of their diagonal and the start of their back-side diagonal
k('HRTIM1_CHD1', 'F.Cu', (183.1, 161.25), (187.1, 165.25)); k('HRTIM1_CHD1', 'F.Cu', (187.1, 165.25), (187.1, 168.9))
k('HRTIM1_CHD1', 'B.Cu', (187.1, 168.9), (187.1, 170.0)); k('HRTIM1_CHD1', 'B.Cu', (187.1, 170.0), (191.2, 174.1))
kill.add(VK(N['HRTIM1_CHD1'], (187.1, 168.9)))
k('HRTIM1_CHD2', 'F.Cu', (183.35, 160.75), (187.75, 165.15)); k('HRTIM1_CHD2', 'F.Cu', (187.75, 165.15), (187.75, 169.6))
k('HRTIM1_CHD2', 'B.Cu', (187.75, 169.6), (187.75, 169.85)); k('HRTIM1_CHD2', 'B.Cu', (187.75, 169.85), (191.4, 173.5))
kill.add(VK(N['HRTIM1_CHD2'], (187.75, 169.6)))
# legacy clock
k('Net-(U301-A)', 'F.Cu', (195.1, 164.5), (188.75, 164.5)); k('Net-(U301-A)', 'F.Cu', (188.75, 164.5), (188.45, 164.8))
k('Net-(U301-A)', 'F.Cu', (188.45, 164.8), (188.45, 170.9))
# leg-A sense line: everything between the divider and the via at (192.4, 165.2), where the J301 branch goes north
ins = lambda p: 181.0 <= p[0] <= 191.5 and 164.3 <= p[1] <= 192.0
for t in b.GetTracks():
    if t.GetNetname() != N['VSWA_SENSE']:
        continue
    if t.GetClass() == 'PCB_VIA':
        if ins(P(t.GetPosition())):
            kill.add(VK(N['VSWA_SENSE'], P(t.GetPosition())))
    else:
        a, e = P(t.GetStart()), P(t.GetEnd())
        if ins(a) and ins(e):
            kill.add(T(N['VSWA_SENSE'], b.GetLayerName(t.GetLayer()), a, e))
k('VSWA_SENSE', 'B.Cu', (190.85, 181.15), (193.2, 183.5))            # dead end left behind by an earlier pass
k('VSWA_SENSE', 'B.Cu', (190.71, 179.6), c338_2)                     # link to the place R343 used to have
k('VSWA_SENSE', 'F.Cu', (192.4, 165.2), (189.55, 165.2))
del b
print('removed', rip_text(dst, kill), 'of', len(kill), 'pieces')
reg = json.load(open(regin))


def tup(q):
    return tuple(tuple(x) if isinstance(x, list) else x for x in q)


reg = {n: [list(q) for q in map(tup, ks) if q not in kill] for n, ks in reg.items()}
r = R.Router(dst, reg={n: [tup(q) for q in ks] for n, ks in reg.items()})
r._fixed = True
F = lambda n, pts, w=0.2: [r.add_track(N[n], 'F.Cu', p, q, w) for p, q in zip(pts, pts[1:])]
B = lambda n, pts, w=0.2: [r.add_track(N[n], 'B.Cu', p, q, w) for p, q in zip(pts, pts[1:])]
Vi = lambda n, c: r.add_via(N[n], c)

# leg-B gate signals: same diagonals, 0.8 mm longer; vias 0.7 mm apart along the run as before
F('HRTIM1_CHD1', [(183.1, 161.25), (187.9, 166.05), (187.9, 168.3)]); Vi('HRTIM1_CHD1', (187.9, 168.3))
B('HRTIM1_CHD1', [(187.9, 168.3), (187.9, 170.8), (191.2, 174.1)])
F('HRTIM1_CHD2', [(183.35, 160.75), (188.55, 165.95), (188.55, 169.0)]); Vi('HRTIM1_CHD2', (188.55, 169.0))
B('HRTIM1_CHD2', [(188.55, 169.0), (188.55, 170.65), (191.4, 173.5)])
# legacy clock: past the +5V test point TP223 on its west side, then back to the old approach to U304
F('Net-(U301-A)', [(195.1, 164.5), (189.35, 164.5), (189.05, 164.8), (189.05, 167.9), (189.3, 168.15), (189.3, 169.6), (188.45, 170.45), (188.45, 170.9)])

# leg-A sense line, back side, from the tap (C338 pad) to R343 next to the MCU
jn = (r343_2[0] + 1.19, r343_2[1] + 1.19)                                # T where the J301 branch leaves, on the 45 degree run into R343
top = (187.15, round(r343_2[1] + 2.15, 3))
# South of the via cluster it keeps going straight for 2 mm, so that it leaves the leg-B pair at a right distance, and passes
# the ground via of U304 on the far side; the diagonal then runs 1.9 mm from the leg-B gate signals instead of beside them.
B('VSWA_SENSE', [c338_2, (191.6, 179.28), (191.6, 177.2), (187.15, 172.75), top, jn, r343_2])
# J301 branch: east on the back under the gate signals, over the leg-B comparator line on the top side, down again at the existing via
B('VSWA_SENSE', [jn, (190.0, jn[1])]); Vi('VSWA_SENSE', (190.0, jn[1]))
F('VSWA_SENSE', [(190.0, jn[1]), (190.4, 165.2), (192.4, 165.2)])
r.save()
json.dump({n: [list(q) for q in ks] for n, ks in r.reg.items()}, open(regout, 'w'))
print('written', dst, 'jn', jn, 'top', top)

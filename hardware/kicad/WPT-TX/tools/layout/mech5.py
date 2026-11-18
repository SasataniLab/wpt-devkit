#!/usr/bin/env python3
"""Third revision: copper out of the reach of the hardware on the mounting holes. usage: mech5.py BOARD_IN BOARD_OUT

holechk.py lists every track that comes closer to a hole than a washer does. Three places were left after mech4.py:

  * M3 hole at (155, 200), back side: the latch line ~{WLAT} passed 3.13 mm from the centre, under a 7 mm washer and
    under the corners of a 5.5 mm hexagonal standoff (3.18 mm). It now goes round at 4.2 mm.
  * 2 mm ground screw hole at (195, 162.35), back side: the divider tap of leg A (VSWA_SENSE) squeezed past the pad at
    2.0 mm from the centre; a nut of an M2 screw reaches 2.3 mm. Its lane moves from x = 192.9 to 192.4 (2.5 mm), next to
    the tap of leg B (0.2 mm gap for 4 mm; about 0.2 pF between two nodes of 15 pF each).
  * same hole, top side: the USB pair passed at 2.35 mm. Its two columns move 0.5 mm west (2.85 mm).
The track of the first design that hugs the pad of this hole on the top side (clock of the legacy variant) stays.

Also: three fiducials on each side for the placement machine (1 mm copper, 2 mm mask opening, the pour kept 0.6 mm away;
no schematic symbol, not in the BOM or the placement files). Top FID1-3, bottom FID4-6, at the same three places:
(163.0, 133.2), (209.5, 127.4), (160.5, 202.0) - nothing but ground pour within 1.8 mm of any of them.
"""
import shutil
import sys

import pcbnew

from nego import rip_text

MM = 1e6
src, dst = sys.argv[1:3]
shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)
V = lambda x, y: pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
P = lambda v: (round(v.x / MM, 3), round(v.y / MM, 3))
short = lambda n: n.split('/')[-1]

# (net, layer, width) -> old polyline that goes, new polyline that comes
JOBS = [
    ('~{WLAT}', 'B.Cu', 0.2,
     [(157.19, 196.09), (157.92, 196.82), (157.92, 198.62), (158.825, 198.625)],
     [(157.19, 196.09), (158.825, 197.725), (158.825, 198.625)]),
    ('VSWA_SENSE', 'B.Cu', 0.2,
     [(193.40, 141.04), (193.40, 159.90), (192.90, 160.40), (192.90, 165.05), (193.05, 165.20)],
     [(193.40, 141.04), (193.40, 159.40), (192.40, 160.40), (192.40, 164.55), (193.05, 165.20)]),
    ('USB_D_N', 'F.Cu', 0.3,
     [(186.65, 163.20), (192.00, 163.20), (192.50, 162.70), (192.50, 159.5071), (193.40, 158.6071)],
     [(186.65, 163.20), (191.50, 163.20), (192.00, 162.70), (192.00, 160.0071), (193.40, 158.6071)]),
    ('USB_D_P', 'F.Cu', 0.3,
     [(187.05, 162.70), (191.60, 162.70), (192.00, 162.30), (192.00, 159.30), (192.90, 158.40)],
     [(187.05, 162.70), (191.10, 162.70), (191.50, 162.30), (191.50, 159.80), (192.90, 158.40)]),
]


def on_line(p, a, e, tol=0.02):
    """is p on the segment a-e (within tol)?"""
    dx, dy = e[0] - a[0], e[1] - a[1]
    L2 = dx * dx + dy * dy
    u = 0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return ((p[0] - a[0] - u * dx) ** 2 + (p[1] - a[1] - u * dy) ** 2) ** 0.5 < tol


kill = set()
for net, layer, w, old, new in JOBS:
    full = [n for n in (x.GetNetname() for x in b.GetNetInfo().NetsByName().values()) if short(n) == net]
    assert len(full) == 1, (net, full)
    full = full[0]
    n = 0
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != full or b.GetLayerName(t.GetLayer()) != layer:
            continue
        a, e = P(t.GetStart()), P(t.GetEnd())
        if any(on_line(a, p, q) and on_line(e, p, q) for p, q in zip(old, old[1:])):
            kill.add(('T', full, layer) + tuple(sorted([a, e])))
            n += 1
    assert n >= len(old) - 1, (net, n)
    ni = b.FindNet(full)
    for p, q in zip(new, new[1:]):
        dx, dy = abs(q[0] - p[0]), abs(q[1] - p[1])
        assert dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-3, ('not on 45 degrees', net, p, q)
        s = pcbnew.PCB_TRACK(b)
        s.SetNet(ni); s.SetLayer(b.GetLayerID(layer)); s.SetStart(V(*p)); s.SetEnd(V(*q)); s.SetWidth(int(round(w * MM)))
        b.Add(s)
    print('%-12s %s: %d old pieces out, %d new' % (net, layer, n, len(new) - 1))
FID = ((163.0, 133.2), (209.5, 127.4), (160.5, 202.0))
k = 0
for side in ('F', 'B'):
    for x, y in FID:
        k += 1
        fp = pcbnew.FootprintLoad('/usr/share/kicad/footprints/Fiducial.pretty', 'Fiducial_1mm_Mask2mm')
        fp.SetFPIDAsString('Fiducial:Fiducial_1mm_Mask2mm')
        fp.SetReference('FID%d' % k)
        fp.SetValue('Fiducial')
        b.Add(fp)
        fp.SetPosition(V(x, y))
        if side == 'B':
            fp.Flip(V(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
print('fiducials:', k)
pcbnew.SaveBoard(dst, b)
del b
print('removed', rip_text(dst, kill), 'of', len(kill), 'track pieces')

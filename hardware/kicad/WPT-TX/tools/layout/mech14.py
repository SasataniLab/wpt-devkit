#!/usr/bin/env python3
"""Revision 7a: what weld.py cannot decide by itself. usage: mech14.py BOARD_IN BOARD_OUT   (BOARD_IN = output of weld.py)

weld.py moves a piece sideways onto a pad centre when the pad is up to 0.25 mm off its line. In five places that came
too close to a neighbour, or the end needed a different shape; they are drawn here by hand. Four parts of revision 7
move by 0.005 to 0.03 mm so that their pads stand on the lines that end in them (R336, C340, C344, R346).
"""
import re, sys
import pcbnew
import newfp
from newfp import on_line, P, V
src, dst = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
dead = []


def full(short):
    hit = [n for n in (str(k) for k in b.GetNetInfo().NetsByName().keys()) if n == short or n.split('/')[-1] == short]
    assert len(hit) == 1, (short, hit)
    return hit[0]


def redraw(short, layer, old, new, w=None):
    """the pieces of the net on the polyline `old` go, the polyline `new` comes (same width)"""
    name, got = full(short), []
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != name or b.GetLayerName(t.GetLayer()) != layer or t.m_Uuid.AsString() in dead:
            continue
        a, e = P(t.GetStart()), P(t.GetEnd())
        if any(on_line(a, p, q, 0.012) and on_line(e, p, q, 0.012) for p, q in zip(old, old[1:])):
            got.append(t)
    assert got, (short, layer, old)
    width = w or got[0].GetWidth() / 1e6
    for t in got:
        dead.append(t.m_Uuid.AsString())
    newfp.seg(b, name, new, w=width, layer=layer)


def nudge(ref, dx, dy):
    f = b.FindFootprintByReference(ref)
    p = f.GetPosition()
    f.SetPosition(pcbnew.VECTOR2I(p.x + int(round(dx * 1e6)), p.y + int(round(dy * 1e6))))


nudge('R336', 0, 0.01)
nudge('C340', -0.005, 0)
nudge('C344', -0.01, 0)
nudge('R346', 0.03, 0)
redraw('GND', 'B.Cu', [(189.4, 161.81), (189.89, 161.81), (190.2, 161.5)], [(189.4, 161.82), (189.88, 161.82), (190.2, 161.5)])
redraw('ZVS_VTH', 'B.Cu', [(176.5, 165.53), (176.5, 165.6), (179.6625, 165.6)], [(176.5, 165.4), (179.4625, 165.4), (179.6625, 165.6)])
redraw('ZVS_VTH', 'B.Cu', [(176.5, 165.53), (176.5, 164.58)], [(176.5, 165.53), (176.5, 165.4), (176.5, 164.58)])
redraw('ZVS_VTH', 'B.Cu', [(176.85, 172.85), (179.41, 172.85), (180.06, 172.2)], [(176.85, 172.85), (179.4, 172.85), (180.05, 172.2)])
redraw('BOOT0', 'B.Cu', [(187.9, 152.05), (184.65, 152.05), (182.0, 149.4)], [(187.9, 152.05), (187.8, 151.95), (184.55, 151.95), (182.0, 149.4)])
redraw('Net-(U2-PF1)', 'F.Cu', [(183.75, 146.9), (183.48, 146.63), (183.48, 144.78)], [(183.75, 146.9), (183.35, 146.5), (183.35, 144.91), (183.48, 144.78)])
redraw('~{WLAT}', 'B.Cu', [(153.0, 189.731), (157.19, 193.921), (157.19, 196.09), (158.825, 197.725)],
       [(153.0, 189.7314), (157.188, 193.9194), (157.188, 196.088), (158.825, 197.725)])
redraw('HRTIM1_FLT3', 'F.Cu', [(175.65, 157.0), (176.05, 156.6), (177.3, 156.6)], [(175.65, 157.0), (176.0, 156.65), (178.225, 156.65)])
redraw('USB_D_N', 'F.Cu', [(194.55, 132.6), (194.55, 133.75)], [(194.55, 132.355), (194.55, 133.75)])
redraw('USB_D_P', 'F.Cu', [(194.05, 133.35), (194.05, 132.6)], [(194.05, 133.35), (194.05, 132.355)])
redraw('HSE_EXT', 'F.Cu', [(187.3, 144.85), (187.3, 145.9)], [(187.32, 144.85), (187.32, 145.9)])
redraw('Net-(U306-CLK1)', 'F.Cu', [(188.31, 144.85), (189.3, 144.85)], [(188.34, 144.85), (189.3, 144.85)])
pcbnew.SaveBoard(dst, b)
txt = open(dst, encoding='utf-8').read().split('\n'); out = []; i = 0; gone = 0
while i < len(txt):
    if txt[i] == '\t(segment':
        j = i
        while txt[j] != '\t)':
            j += 1
        m = re.search(r'\(uuid "([^"]+)"\)', '\n'.join(txt[i:j + 1]))
        if m and m.group(1) in dead:
            gone += 1; i = j + 1; continue
    out.append(txt[i]); i += 1
open(dst, 'w', encoding='utf-8').write('\n'.join(out))
print('pieces replaced', gone)

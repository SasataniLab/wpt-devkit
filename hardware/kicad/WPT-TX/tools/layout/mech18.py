#!/usr/bin/env python3
"""Revision 7b: pieces of a few hundredths of a millimetre on signal lines of the STM32 part. usage: mech18.py BOARD_IN BOARD_OUT
(BOARD_IN = output of mech17.py)

Where a line missed a pad or via centre by 0.01 to 0.05 mm and a tiny piece bridged the step, the line itself moves.
Left as they are: the MCU's VDDA filter (hand-made), ZVS_A_IN at R335 and ~{WLAT} at its last via (the neighbours fix
both ends), and ground stubs of the power part.
"""
import re, sys
import pcbnew
import newfp
from newfp import P
src, dst = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
dead = []


def full(short):
    hit = [n for n in (str(k) for k in b.GetNetInfo().NetsByName().keys()) if n == short or n.split('/')[-1] == short]
    assert len(hit) == 1, (short, hit)
    return hit[0]


def near(p, q):
    return abs(p[0] - q[0]) < 0.0015 and abs(p[1] - q[1]) < 0.0015


def drop(short, layer, *pieces):
    """remove the pieces (a, e) of the net; returns the width of the last one"""
    name, w = full(short), None
    for a, e in pieces:
        hit = [t for t in b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T and t.GetNetname() == name and b.GetLayerName(t.GetLayer()) == layer
               and t.m_Uuid.AsString() not in dead and ((near(P(t.GetStart()), a) and near(P(t.GetEnd()), e)) or (near(P(t.GetStart()), e) and near(P(t.GetEnd()), a)))]
        assert len(hit) == 1, (short, layer, a, e, len(hit))
        dead.append(hit[0].m_Uuid.AsString()); w = hit[0].GetWidth() / 1e6
    return w


def redraw(short, layer, old, new):
    """the polyline `old` (given corner by corner) goes, the polyline `new` comes with the same width"""
    w = drop(short, layer, *zip(old, old[1:]))
    newfp.seg(b, full(short), new, w=w, layer=layer)


def nudge(ref, dx, dy):
    f = b.FindFootprintByReference(ref)
    p = f.GetPosition()
    f.SetPosition(pcbnew.VECTOR2I(p.x + int(round(dx * 1e6)), p.y + int(round(dy * 1e6))))


def move_via(short, old, new):
    name, n = full(short), 0
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == name and near(P(t.GetPosition()), old):
            t.SetPosition(pcbnew.VECTOR2I(int(round(new[0] * 1e6)), int(round(new[1] * 1e6)))); n += 1
    assert n == 1, (short, old, n)


redraw('GPIO_ENCODER_PUSH', 'B.Cu', [(173.18, 148.63), (172.2, 147.65), (172.2, 147.31), (172.19, 147.3)], [(173.18, 148.63), (172.19, 147.64), (172.19, 147.3)])
redraw('GPIO_SW_MISC1', 'B.Cu', [(188.2, 154.15), (188.6, 153.75), (188.6, 149.25), (188.65, 149.2)], [(188.2, 154.15), (188.65, 153.7), (188.65, 149.2)])
redraw('HRTIM1_FLT3', 'F.Cu', [(174.7, 158.1), (173.3, 158.1), (170.7, 155.5), (170.65, 155.5)], [(174.7, 158.1), (173.25, 158.1), (170.65, 155.5)])
redraw('~{ALERT}', 'F.Cu', [(169.85, 162.4), (169.85, 163.3), (170.4, 163.85), (171.676, 163.85), (171.701, 163.875)], [(169.85, 162.4), (169.85, 163.325), (170.4, 163.875), (171.701, 163.875)])
for t in b.GetTracks():                                       # pieces of no length
    if t.Type() != pcbnew.PCB_VIA_T and t.GetStart() == t.GetEnd():
        dead.append(t.m_Uuid.AsString())
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
print('pieces removed', gone)

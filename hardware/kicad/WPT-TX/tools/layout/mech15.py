#!/usr/bin/env python3
"""Revision 7a, last joints. usage: mech15.py BOARD_IN BOARD_OUT   (BOARD_IN = output of mech14.py)

The eleven track ends that weld.py / mech14.py left inside a pad but off its centre:
  encoder A / B   R4, R5 (+0.01 mm) and C13, C14 (-0.02 mm) move in x so that the pads of each pair stand on one line
                  x = 162.10; the lines from the encoder pins are redrawn onto the pad centres (channel B loses two bends)
  I2C pull-ups    SDA: one piece from pad centre to pad centre; SCL: the two vias and the pieces between them move
                  0.006 mm onto the pad row y = 163.144
  USB D-          the 45-degree piece runs on into pad 4 of U3 and ends on its centre
  crystal         the line from PF0 ends with a 45-degree piece on the centre of Y1.1; C11 moves 0.025 mm in y so that
                  the line Y1.1 - C11.1 is straight (weld.py had bridged the step with a 0.035 mm piece)
"""
import re, sys
import pcbnew
import newfp
from newfp import on_line, P
src, dst = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
dead = []


def full(short):
    hit = [n for n in (str(k) for k in b.GetNetInfo().NetsByName().keys()) if n == short or n.split('/')[-1] == short]
    assert len(hit) == 1, (short, hit)
    return hit[0]


def redraw(short, layer, old, new):
    """the pieces of the net on the polyline `old` go, the polyline `new` comes (same width)"""
    name, got = full(short), []
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != name or b.GetLayerName(t.GetLayer()) != layer or t.m_Uuid.AsString() in dead:
            continue
        a, e = P(t.GetStart()), P(t.GetEnd())
        if any(on_line(a, p, q, 0.012) and on_line(e, p, q, 0.012) for p, q in zip(old, old[1:])):
            got.append(t)
    assert len(got) == len(old) - 1, (short, layer, old, len(got))
    for t in got:
        dead.append(t.m_Uuid.AsString())
    newfp.seg(b, name, new, w=got[0].GetWidth() / 1e6, layer=layer)


def nudge(ref, dx, dy):
    f = b.FindFootprintByReference(ref)
    p = f.GetPosition()
    f.SetPosition(pcbnew.VECTOR2I(p.x + int(round(dx * 1e6)), p.y + int(round(dy * 1e6))))


def move_via(short, old, new):
    name, n = full(short), 0
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == name and P(t.GetPosition()) == old:
            t.SetPosition(pcbnew.VECTOR2I(int(round(new[0] * 1e6)), int(round(new[1] * 1e6)))); n += 1
    assert n == 1, (short, old, n)


# encoder channel A
nudge('R4', 0.01, 0); nudge('C13', -0.02, 0)
redraw('TIM3_CH1_ENCODER', 'B.Cu', [(160.55, 148.0), (161.25, 147.3), (162.09, 147.3)], [(160.4, 148.1), (161.2, 147.3), (162.1, 147.3)])
redraw('TIM3_CH1_ENCODER', 'B.Cu', [(162.1, 147.5), (162.1, 148.7)], [(162.1, 147.3), (162.1, 148.9)])
redraw('TIM3_CH1_ENCODER', 'B.Cu', [(162.12, 148.9), (162.12, 149.07), (164.55, 151.5)], [(162.1, 148.9), (162.1, 149.05), (164.55, 151.5)])
# encoder channel B
nudge('R5', 0.01, 0); nudge('C14', -0.02, 0)
redraw('TIM3_CH2_ENCODER', 'B.Cu', [(160.4, 153.1), (160.9, 153.1), (161.0, 153.2), (161.39, 153.2), (162.09, 153.9)],
       [(160.4, 153.1), (161.3, 153.1), (162.1, 153.9)])
redraw('TIM3_CH2_ENCODER', 'B.Cu', [(162.1, 152.5), (162.1, 153.7)], [(162.1, 152.3), (162.1, 153.9)])
redraw('TIM3_CH2_ENCODER', 'B.Cu', [(162.09, 153.9), (166.59, 158.4), (170.15, 158.4)], [(162.1, 153.9), (166.6, 158.4), (170.15, 158.4)])
# I2C pull-ups
redraw('SDA', 'F.Cu', [(163.1, 163.15), (163.7, 163.15)], [(162.9, 163.144), (163.9, 163.144)])
move_via('SCL', (161.2, 163.15), (161.2, 163.144)); move_via('SCL', (165.6, 163.15), (165.6, 163.144))
redraw('SCL', 'B.Cu', [(161.2, 163.15), (165.6, 163.15)], [(161.2, 163.144), (165.6, 163.144)])
redraw('SCL', 'F.Cu', [(161.7, 163.15), (161.2, 163.15)], [(161.9, 163.144), (161.2, 163.144)])
redraw('SCL', 'F.Cu', [(171.95, 161.25), (167.5, 161.25), (165.6, 163.15), (165.1, 163.15)],
       [(171.95, 161.25), (167.494, 161.25), (165.6, 163.144), (164.9, 163.144)])
# USB D-
redraw('USB_D_N', 'F.Cu', [(194.55, 133.75), (194.05, 134.25), (193.4, 134.25)], [(194.55, 133.75), (193.4375, 134.8625), (193.25, 134.8625)])
# crystal
nudge('C11', 0, 0.025)
redraw('HSE_EXT', 'F.Cu', [(185.65, 148.225), (185.65, 146.2)], [(185.65, 148.225), (185.65, 146.25), (185.975, 145.925)])
redraw('HSE_EXT', 'F.Cu', [(185.975, 145.925), (187.295, 145.925), (187.32, 145.9)], [(185.975, 145.925), (187.32, 145.925)])
redraw('HSE_EXT', 'F.Cu', [(187.32, 144.85), (187.32, 145.9)], [(187.32, 144.85), (187.32, 145.925)])
redraw('GND', 'F.Cu', [(188.28, 145.9), (188.7, 145.9)], [(188.28, 145.925), (188.7, 145.925)])
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

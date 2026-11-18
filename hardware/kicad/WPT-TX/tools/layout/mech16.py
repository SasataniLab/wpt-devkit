#!/usr/bin/env python3
"""Revision 7b: joints of the whole board that the rules leave. usage: mech16.py BOARD_IN BOARD_OUT
(BOARD_IN = output of weld.py --all --skip VBUS, snap.py --all --skip VBUS, weld.py --all --skip VBUS)

Doubled and floating pieces go; ends are redrawn onto pad and via centres; five vias move by 0.005 to 0.05 mm and
C338, D311, R201 by 0.005 to 0.025 mm. VBUS at the USB connector keeps its offset from the pad centres (the
tracks stand 0.2 mm off to clear the locating holes) and gets a 45-degree piece onto each centre instead.
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


# MCU pin 16 (+3V3): the via stands under the pad line
move_via('+3V3', (180.1, 147.0), (180.15, 147.0))
redraw('+3V3', 'F.Cu', [(180.1, 148.05), (180.1, 147.0)], [(180.15, 148.225), (180.15, 147.0)])
# +5V: a doubled piece on the front, a broken corner on the back
drop('+5V', 'F.Cu', ((196.806, 155.7), (196.806, 154.175)))
redraw('+5V', 'B.Cu', [(159.7, 161.2), (159.7, 163.0)], [(159.7, 161.2), (159.7, 163.0), (159.95, 163.25)])
drop('+5V', 'B.Cu', ((159.7, 162.95), (159.75, 163.0)), ((159.75, 163.0), (159.75, 163.05)), ((159.75, 163.05), (159.95, 163.25)))
# SDA_5V: the branch meets the line in a T
drop('SDA_5V', 'F.Cu', ((169.4505, 165.0505), (168.6, 164.2)))
redraw('SDA_5V', 'F.Cu', [(169.501, 165.0), (160.1878, 165.0)], [(169.501, 165.0), (169.4, 165.0), (160.1878, 165.0)])
newfp.seg(b, full('SDA_5V'), [(168.6, 164.2), (169.4, 165.0)], w=0.2, layer='F.Cu')
# H_Sig2 at D311
nudge('D311', 0, -0.025)
redraw('H_Sig2', 'F.Cu', [(191.1, 172.2), (191.7, 172.2)], [(191.1, 172.2), (191.875, 172.2)])
redraw('H_Sig2', 'F.Cu', [(191.875, 172.225), (191.875, 173.475)], [(191.875, 172.2), (191.875, 173.475)])
# OutB tap of the leg-B divider: a floating piece, and a three-piece link to R341
drop('OutB', 'B.Cu', ((193.8, 168.75), (193.75, 168.7)))
redraw('OutB', 'B.Cu', [(193.95, 168.85), (193.88, 168.85), (193.845, 168.885), (193.125, 168.885), (193.01, 169.0)], [(193.95, 168.85), (193.8, 169.0), (193.01, 169.0)])
# leg-A sense line through R343, C338, R339 (pad pitches differ: one 0.014 mm piece stays at R339)
nudge('C338', -0.02, 0)
redraw('VSWA_SENSE', 'B.Cu', [(191.9, 179.45), (191.9, 178.52)], [(191.9, 179.6), (191.9, 178.52)])
redraw('VSWA_SENSE', 'B.Cu', [(191.92, 179.6), (191.92, 180.87), (191.89, 180.9)], [(191.9, 179.6), (191.9, 180.89), (191.89, 180.9)])
redraw('OutA', 'B.Cu', [(192.88, 179.6), (192.88, 180.87), (192.91, 180.9)], [(192.86, 179.6), (192.86, 180.85), (192.91, 180.9)])
# ground of the crystal
move_via('GND', (185.97, 142.47), (185.975, 142.47))
redraw('GND', 'F.Cu', [(185.97, 144.47), (185.97, 142.47)], [(185.975, 144.475), (185.975, 142.47)])
redraw('GND', 'F.Cu', [(188.28, 145.925), (188.7, 145.925)], [(188.28, 145.925), (188.675, 145.925), (188.9, 145.7)])
drop('GND', 'F.Cu', ((188.7, 145.9), (188.9, 145.7)))
# ground stubs in the power part
drop('GND', 'F.Cu', ((201.07, 190.73), (201.07, 190.5295)), ((201.07, 190.5295), (201.07, 190.58)), ((202.919, 141.875), (202.919, 142.175)))
move_via('GND', (204.394, 151.925), (204.419, 151.925))
drop('GND', 'F.Cu', ((204.419, 151.95), (204.394, 151.925)), ((204.419, 151.7), (204.294, 151.825)), ((204.294, 151.825), (204.394, 151.925)))
redraw('GND', 'F.Cu', [(204.419, 152.825), (204.419, 151.95)], [(204.419, 152.825), (204.419, 151.925)])
# R202 / R201 (input divider of ADC_VDC): two parallel pieces 5 um apart become one
nudge('R201', -0.005, 0)
drop('ADC_VDC', 'F.Cu', ((166.535, 187.475), (166.53, 187.48)), ((166.535, 188.485), (166.535, 187.475)), ((166.53, 188.48), (166.535, 188.485)))
redraw('ADC_VDC', 'F.Cu', [(166.53, 187.48), (166.53, 188.48)], [(166.53, 187.48), (166.53, 188.485)])
redraw('ADC_VDC', 'F.Cu', [(167.085, 188.485), (166.535, 188.485)], [(167.085, 188.485), (166.53, 188.485)])
move_via('GND', (168.4, 187.5), (168.4, 187.48))
redraw('GND', 'F.Cu', [(167.55, 187.5), (168.4, 187.5)], [(167.53, 187.48), (168.4, 187.48)])
# ground at the comparators
redraw('GND', 'B.Cu', [(179.1, 166.95), (179.1, 172.2)], [(179.09, 166.95), (179.09, 172.18), (179.11, 172.2)])
redraw('GND', 'B.Cu', [(180.8, 164.66), (181.9375, 164.66)], [(180.8, 164.66), (181.9275, 164.66), (181.9375, 164.65)])
move_via('GND', (163.9, 148.1), (163.86, 148.1))
redraw('GND', 'B.Cu', [(163.25, 148.75), (163.9, 148.1)], [(163.06, 148.9), (163.86, 148.1)])
# VPP: the wide piece from C305 ends on the thin line
newfp.seg(b, full('VPP'), [(202.0, 186.0), (202.0, 186.15)], w=0.2, layer='F.Cu')
redraw('VPP', 'F.Cu', [(201.45, 186.15), (202.1, 186.15)], [(201.45, 186.15), (202.0, 186.15), (202.1, 186.15)])
# L_Sig2 at R330: the two lines keep their place (moved onto the centre they take a spoke from the ground pad beside it)
redraw('L_Sig2', 'B.Cu', [(192.7, 174.51), (192.7, 174.79), (191.89, 175.6)], [(192.7, 174.51), (192.7, 174.68), (191.89, 175.49), (191.89, 175.6)])
redraw('L_Sig2', 'B.Cu', [(192.85, 176.3), (192.59, 176.3), (191.89, 175.6)], [(192.85, 176.3), (192.5, 176.3), (191.89, 175.69), (191.89, 175.6)])
# CN301 (edge SMA): the front lug at (217.25, 174.52) had no copper to the back lug under it, the one old unconnected item
for x in (216.0, 217.25, 218.5):
    newfp.via(b, full('OutB'), (x, 174.52), size=0.8, drill=0.4)
# VBUS
redraw('VBUS', 'F.Cu', [(192.3, 135.1), (192.3, 135.95)], [(192.3, 134.8625), (192.3, 135.95)])
redraw('VBUS', 'F.Cu', [(196.0, 131.2), (196.0, 132.2)], [(196.0, 131.2), (196.0, 132.155), (196.2, 132.355)])
redraw('VBUS', 'F.Cu', [(196.2, 132.6), (196.2, 133.9)], [(196.2, 132.355), (196.2, 133.9)])
redraw('VBUS', 'F.Cu', [(191.6, 131.2), (191.6, 132.2)], [(191.6, 131.2), (191.6, 132.155), (191.4, 132.355)])
redraw('VBUS', 'F.Cu', [(196.2, 134.6), (197.2, 135.6), (197.6, 136.0), (197.6, 136.4), (197.6, 146.49)], [(196.2, 134.6), (197.6, 136.0), (197.6, 146.49)])
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

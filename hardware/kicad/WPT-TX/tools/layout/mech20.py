#!/usr/bin/env python3
"""After the hand edit d47c658 ("minor trace edits"): what the edit left behind. usage: mech20.py BOARD_IN BOARD_OUT

  SDA_5V   a 0.43 mm stub at R222 pad 1 that ends nowhere (DRC: track_dangling): removed.
           The new branch from R222 ran 7.7 mm beside the bus, up to a via, back down on the other side and through a
           second via onto the bus. It now joins the bus on the front side where it first comes alongside
           ((160.6, 164.55) -> (161.05, 165.0)); the two vias and 11 mm of track go.
  ADC_VDC  a piece of 0.0075 mm between two diagonals and a 0.1 mm piece at the via on In2: the diagonals on both
           layers now end on the via (which stays, 0.2 mm from the SCL track); one piece on each layer.
"""
import sys
import pcbnew
import newfp
from newfp import P, V

src, dst = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
short = lambda n: n.split('/')[-1]
gone = []


def near(p, q, tol=0.0015):
    return abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) < tol


def full(net_short):
    hit = [n for n in (str(k) for k in b.GetNetInfo().NetsByName().keys()) if short(n) == net_short]
    assert len(hit) == 1, (net_short, hit)
    return hit[0]


def piece(net_short, layer, a, e):
    hit = [t for t in b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T and short(t.GetNetname()) == net_short and b.GetLayerName(t.GetLayer()) == layer
           and not any(t is x for x in gone)
           and ((near(P(t.GetStart()), a) and near(P(t.GetEnd()), e)) or (near(P(t.GetStart()), e) and near(P(t.GetEnd()), a)))]
    assert len(hit) == 1, (net_short, layer, a, e, len(hit))
    return hit[0]


def via_at(net_short, c):
    hit = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and short(t.GetNetname()) == net_short and near(P(t.GetPosition()), c)]
    assert len(hit) == 1, (net_short, c, len(hit))
    return hit[0]


def drop(net_short, layer, *polys):
    for poly in polys:
        for a, e in zip(poly, poly[1:]):
            gone.append(piece(net_short, layer, a, e))


def move_end(t, old, new):
    if near(P(t.GetStart()), old):
        t.SetStart(V(*new))
    else:
        assert near(P(t.GetEnd()), old)
        t.SetEnd(V(*new))


# ---- SDA_5V
drop('SDA_5V', 'F.Cu', [(162.9, 161.7097), (162.9, 162.144)])                                   # the stub
drop('SDA_5V', 'F.Cu', [(159.6015, 164.55), (167.3414, 164.55), (168.3, 163.5914), (168.3, 162.4)], [(168.6, 164.2), (169.4, 165.0)])
drop('SDA_5V', 'B.Cu', [(168.3, 162.4), (168.3, 163.9), (168.6, 164.2)])
gone.append(via_at('SDA_5V', (168.3, 162.4)))
gone.append(via_at('SDA_5V', (168.6, 164.2)))
bus = piece('SDA_5V', 'F.Cu', (169.4, 165.0), (160.188, 165.0))                                  # split at the new junction
west = [q for q in (P(bus.GetStart()), P(bus.GetEnd())) if near(q, (160.188, 165.0))][0]        # its exact end (160.1878)
move_end(bus, west, (161.05, 165.0))
newfp.seg(b, full('SDA_5V'), [west, (161.05, 165.0)], w=0.2, layer='F.Cu', allow_any_angle=True)
newfp.seg(b, full('SDA_5V'), [(159.6015, 164.55), (160.6, 164.55), (161.05, 165.0)], w=0.2, layer='F.Cu')

# ---- ADC_VDC: the via stays where it was put (0.2 mm from the SCL track); the diagonals on both layers end on it
move_end(piece('ADC_VDC', 'B.Cu', (166.75, 162.8425), (166.75, 163.55)), (166.75, 162.8425), (166.75, 162.85))
drop('ADC_VDC', 'B.Cu', [(166.75, 162.8425), (167.6884, 161.9041), (167.6959, 161.9041), (168.95, 160.65)])
newfp.seg(b, full('ADC_VDC'), [(166.75, 162.85), (168.95, 160.65)], w=0.2, layer='B.Cu')
drop('ADC_VDC', 'In2.Cu', [(168.95, 160.65), (169.05, 160.65), (169.45, 160.25)])
move_end(piece('ADC_VDC', 'In2.Cu', (169.45, 160.25), (169.45, 158.15)), (169.45, 160.25), (169.45, 160.15))
newfp.seg(b, full('ADC_VDC'), [(168.95, 160.65), (169.45, 160.15)], w=0.2, layer='In2.Cu')

for t in gone:
    b.Remove(t)
pcbnew.SaveBoard(dst, b)
print('removed items:', len(gone))

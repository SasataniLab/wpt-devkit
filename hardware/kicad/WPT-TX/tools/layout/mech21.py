#!/usr/bin/env python3
"""After the review of revision 8 (2026-11-18): BOOT0 button in the north-west, J202 away from C224.
usage: mech21.py BOARD_IN BOARD_OUT NETLIST        (netlist of the schematic after ../schematic/edit_sch14.py)

BOOT0   J1 (jumper on the west edge, 4 mm beside the 36 V header J202) is gone. SW4, the same side-actuated switch as
        the reset switch SW3, stands on the top edge 5.75 mm east of SW3: it can be pressed with the display board
        fitted (the free band behind it lies under that board, which is why a jumper could not go there).
        The net kept its run under the MCU up to the via at (173.25, 152.5). From there it used to go south-west to
        J1 (30 mm, two vias); now it goes north: back side beside HRTIM1_FLT3 (x = 170.575: 0.225 mm to the vias of
        FLT3 on one side and to a GND via on the other), front side between TP304 and J2 across the SCL track of the
        back side, back side again under the two SWD tracks, up to the east pad of SW4. 28 mm, three vias.
        Whole net: 49 mm and six vias (was 51 mm and five). It is a static line with a 10 k pull-down.
        The west pad of SW4 gets +3V3 from the inner plane through a via, as R331 does.
J202    2.54 mm to the north (pins at y = 166.06 and 168.60): 3.1 mm between its body and the base of C224 (was 0.6).
        The link to D204 leaves the pin at 45 degrees. The via that feeds the logic supply of U204 from the +3V3
        plane moves 0.6 mm east, out of the way of the pad; the diagonal behind it is the same line, shorter.
Silk    "BOOT0" moves to SW4; "36V" and "+" move with J202. The reference of J201 had stood under the can of C224
        since revision 8 (the capacitor was put on top of it): now south of the jack, where it can be read.
"""
import sys
import pcbnew
import newfp
from newfp import P, V

src, dst, netlist = sys.argv[1:4]
b = pcbnew.LoadBoard(src)
comps = newfp.load_netlist(netlist)
short = lambda n: n.split('/')[-1]
gone = []


def near(p, q, tol=0.0015):
    return abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) < tol


def full(net_short):
    hit = [n for n in (str(k) for k in b.GetNetInfo().NetsByName().keys()) if short(n) == net_short]
    assert len(hit) == 1, (net_short, hit)
    return hit[0]


def tracks(net_short):
    return [t for t in b.GetTracks() if short(t.GetNetname()) == net_short and not any(t is x for x in gone)]


def piece(net_short, layer, a, e, tol=0.0015):
    hit = [t for t in tracks(net_short) if t.Type() != pcbnew.PCB_VIA_T and b.GetLayerName(t.GetLayer()) == layer
           and ((near(P(t.GetStart()), a, tol) and near(P(t.GetEnd()), e, tol)) or (near(P(t.GetStart()), e, tol) and near(P(t.GetEnd()), a, tol)))]
    assert len(hit) == 1, (net_short, layer, a, e, len(hit))
    return hit[0]


def via_at(net_short, c):
    hit = [t for t in tracks(net_short) if t.Type() == pcbnew.PCB_VIA_T and near(P(t.GetPosition()), c)]
    assert len(hit) == 1, (net_short, c, len(hit))
    return hit[0]


def move_end(t, old, new):
    if near(P(t.GetStart()), old):
        t.SetStart(V(*new))
    else:
        assert near(P(t.GetEnd()), old), (P(t.GetStart()), P(t.GetEnd()), old)
        t.SetEnd(V(*new))


def pad(ref, num):
    return [P(p.GetPosition()) for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]


def board_text(s):
    hit = [d for d in b.GetDrawings() if d.GetClass() == 'PCB_TEXT' and d.GetText() == s and b.GetLayerName(d.GetLayer()) == 'F.Silkscreen']
    assert len(hit) == 1, (s, len(hit))
    return hit[0]


def in_plane(net_name, layer, c):
    return any(z.GetNetname() == net_name and b.GetLayerName(z.GetLayer()) == layer and z.Outline().Contains(V(*c)) for z in b.Zones())


BOOT0, P3V3 = full('BOOT0'), '+3V3'

# ================================================================= BOOT0: the old run to J1
old = [t for t in tracks('BOOT0') if (t.Type() == pcbnew.PCB_VIA_T and P(t.GetPosition())[1] > 160)
       or (t.Type() != pcbnew.PCB_VIA_T and all(q[0] < 171.9 and q[1] > 152.4 for q in (P(t.GetStart()), P(t.GetEnd()))))]
n_via = sum(1 for t in old if t.Type() == pcbnew.PCB_VIA_T)
old_len = sum(t.GetLength() for t in old if t.Type() != pcbnew.PCB_VIA_T) / 1e6
assert (len(old) - n_via, n_via) == (17, 2), (len(old) - n_via, n_via)
gone += old
j1 = b.FindFootprintByReference('J1')
assert j1 is not None and near(P(j1.GetPosition()), (156.4, 164.0))
gone.append(j1)

# ================================================================= SW4 and the new run
sw4 = newfp.place(b, comps, 'SW4', 167.75, 126.25, rot=0, hide_ref=True)
sw3 = b.FindFootprintByReference('SW3')
sw4.SetAttributes(sw3.GetAttributes())
E, W = pad('SW4', '2'), pad('SW4', '1')                      # east pad: BOOT0, west pad: +3V3
assert near(E, (169.45, 126.25)) and near(W, (166.05, 126.25)), (E, W)
assert comps['SW4']['pins'] == {'1': P3V3, '2': BOOT0}, comps['SW4']['pins']
COL = 170.575                                                 # between the vias of HRTIM1_FLT3 (169.95) and a GND via (171.2, 148.9)
t = piece('BOOT0', 'B.Cu', (171.85, 152.5), (173.25, 152.5))
move_end(t, (171.85, 152.5), (171.325, 152.5))
newfp.seg(b, BOOT0, [(171.325, 152.5), (COL, 151.75), (COL, 138.55)], w=0.2, layer='B.Cu')
newfp.via(b, BOOT0, (COL, 138.55))
newfp.seg(b, BOOT0, [(COL, 138.55), (169.45, 137.425), (169.45, 134.3)], w=0.2, layer='F.Cu')      # across SCL_3.3V (back side, y = 135.2)
newfp.via(b, BOOT0, (169.45, 134.3))
newfp.seg(b, BOOT0, [(169.45, 134.3), (169.45, 127.75)], w=0.2, layer='B.Cu')                      # under SWDIO / SWCLK (front side)
newfp.via(b, BOOT0, (169.45, 127.75))
newfp.seg(b, BOOT0, [(169.45, 127.75), E], w=0.2, layer='F.Cu')
assert in_plane(P3V3, 'In2.Cu', (166.05, 127.75))
newfp.via(b, P3V3, (166.05, 127.75))
newfp.seg(b, P3V3, [W, (166.05, 127.75)], w=0.25, layer='F.Cu')
t = board_text('BOOT0')
t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
t.SetPosition(V(170.5, 126.25))                               # east of the switch, as "RST" stands west of SW3

# ================================================================= J202 2.54 mm north
D = 2.54
j202 = b.FindFootprintByReference('J202')
assert near(pad('J202', '1'), (152.4, 171.14)) and near(pad('J202', '2'), (152.4, 168.6))
j202.SetPosition(V(152.4, 169.87 - D))
PLUS = pad('J202', '1')
assert near(PLUS, (152.4, 168.6)) and near(pad('J202', '2'), (152.4, 166.06)), (PLUS, pad('J202', '2'))
DA = pad('D204', '2')
assert near(DA, (157.05, 171.14))
JNET = full('Net-(D204-A)')
gone.append(piece('Net-(D204-A)', 'F.Cu', (152.4, 171.14), DA))
newfp.seg(b, JNET, [PLUS, (154.94, 171.14), DA], w=1.0, layer='F.Cu')
# the +3V3 via beside the new place of the GND pin
assert in_plane(P3V3, 'In2.Cu', (154.2, 165.5))
via_at('+3V3', (153.6, 165.5)).SetPosition(V(154.2, 165.5))
t = piece('+3V3', 'B.Cu', (153.6, 165.5), (153.6, 166.55))
t.SetStart(V(154.2, 165.5))
t.SetEnd(V(154.2, 167.15))
move_end(piece('+3V3', 'B.Cu', (153.6, 166.55), (155.4, 168.35)), (153.6, 166.55), (154.2, 167.15))
board_text('36V').SetPosition(V(155.3, 169.3 - D))
board_text('+').SetPosition(V(154.75, 171.3 - D))

# ================================================================= the reference of J201, out from under C224
r = b.FindFootprintByReference('J201').Reference()
assert near(P(r.GetPosition()), (155.9, 179.2)), P(r.GetPosition())
r.SetTextAngleDegrees(0)
r.SetPosition(V(153.5, 193.9))

for t in gone:
    b.Remove(t)
pcbnew.SaveBoard(dst, b)
new_len = sum(t.GetLength() for t in b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T and short(t.GetNetname()) == 'BOOT0') / 1e6
print('BOOT0: %.1f mm and %d vias of the old run removed; the net is now %.1f mm with %d vias'
      % (old_len, n_via, new_len, sum(1 for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and short(t.GetNetname()) == 'BOOT0')))
print('removed items:', len(gone))

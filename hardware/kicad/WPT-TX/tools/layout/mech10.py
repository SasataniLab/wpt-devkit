#!/usr/bin/env python3
"""Revision 6: reset button, series resistor at PB4, clearance holes for the screws. usage: mech10.py BOARD_IN BOARD_OUT NETLIST

What the schematic edit tools/schematic/edit_sch10.py asks for, with hand-chosen coordinates.

SW3 (reset, Omron B3U-3000P-B, side-actuated) at the top edge, x = 162.0. The body ends at the board edge and the
plunger stands 0.7 mm over it, so the button is pressed from the side and stays reachable with a display board on
J2. NRST leaves the west pad through one via and runs on the back side to pin 12 of J3 (18.2 mm, two bends): the
front side is closed there by the two SWD tracks. The line keeps 5.3 mm from the centre of the M3 hole, 2.7 mm from
the back-side fiducial and 0.5 mm from the pads of J2 pin 1 and J3 pin 10. The footprint is the project-local
Button_Switch_BoardEdge:SW_SPST_B3U-3000P-B_BoardEdge (the stock one prints the outline of the plunger, which here
lies beyond the board edge). The legend of the test pads is shortened to make room, and "RST" is printed beside
the button.

R13 (1 kohm) on the back side under the north pin row of the MCU, in the existing track of HV_SW_STATE at
(184.80, 147.30). The copper between R13 and PB4 changes its net name to /MCU/GPIO_SW_MISC2; nothing else moves.

Screw holes. The two 2 mm holes at (195.00, 162.35) and (205.00, 197.70): drill 2.0 -> 2.4 mm. The line between them
passes over all four GaN FETs, so they are where a heat-sink bar across both half bridges is screwed on. A plated
hole of nominal 2.0 mm (finished size +/- 0.08 mm) does not reliably pass an M2 screw and never a 2-56 screw (2.18 mm,
the hardware of the EPC9065 heat-sink kit); 2.4 mm is the medium clearance hole for M2 (ISO 273) and passes both.
The four M3 corner holes: 3.0 -> 3.2 mm for the same reason (fine clearance hole for M3). All pads stay as they are.
The two library footprints (lib/footprints/TestPoint.pretty) carry the same sizes.
"""
import shutil
import sys

import pcbnew

import newfp
from newfp import seg, via, rip, place, pads, net, flush, P, V

src, dst, netlist = sys.argv[1:4]
shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)
comps = newfp.load_netlist(netlist)
N = lambda s: newfp.full_name(b, s)
MM = newfp.MM


def put(ref, x, y, side, want, rots=(0, 180, 90, 270), ref_pos=None):
    """place a new footprint and turn it until its pads are where `want` says;
    ref_pos = where its reference goes on the silkscreen (None: not shown)"""
    fp = place(b, comps, ref, x, y, rot=rots[0], side=side, hide_ref=ref_pos is None)
    for r in rots:
        fp.SetOrientationDegrees(r)
        got = pads(fp)
        if all(abs(got[k][0] - v[0]) < 0.006 and abs(got[k][1] - v[1]) < 0.006 for k, v in want.items()):
            break
    else:
        raise AssertionError((ref, got, want))
    t = fp.Reference()
    t.SetPosition(V(*(ref_pos or (x, y))))
    t.SetTextAngleDegrees(0)
    return fp


def renet(old, new, layer, poly):
    """the track pieces of net `old` on the polyline go to net `new`"""
    n = net(b, new)
    k = 0
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != old or b.GetLayerName(t.GetLayer()) != layer:
            continue
        a, e = P(t.GetStart()), P(t.GetEnd())
        if any(newfp.on_line(a, p, q) and newfp.on_line(e, p, q) for p, q in zip(poly, poly[1:])):
            t.SetNet(n)
            k += 1
    assert k >= len(poly) - 1, (old, new, poly, k)


def renet_via(old, new, c):
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == old and P(t.GetPosition()) == (round(c[0], 4), round(c[1], 4)):
            t.SetNet(net(b, new))
            return
    raise AssertionError(('no via', old, c))


def retext(old, new):
    for d in b.GetDrawings():
        if d.GetClass() == 'PCB_TEXT' and d.GetText() == old:
            d.SetText(new)
            return
    raise AssertionError(('no text', old))


NRST, GND, HV, PB4 = N('NRST'), 'GND', N('HV_SW_STATE'), '/MCU/GPIO_SW_MISC2'
assert b.FindNet(PB4) is None and comps['R13']['pins'] == {'1': PB4, '2': HV}, comps['R13']['pins']
net(b, PB4)                                               # new with this revision: the piece between R13 and PB4

# ---- SW3: reset button at the top edge, plunger over the edge (rotation 0 only: the plunger must face north)
sw = put('SW3', 162.00, 126.25, 'F', {'1': (160.30, 126.25), '2': (163.70, 126.25)}, rots=(0,))
assert pads(sw)['1'] == (160.30, 126.25) and sw.GetOrientationDegrees() == 0
assert sum(1 for g in sw.GraphicalItems() if g.GetLayer() == pcbnew.F_SilkS) == 3     # the project-local footprint: nothing printed beyond the edge
seg(b, NRST, [(160.30, 126.25), (160.30, 127.75)])
via(b, NRST, (160.30, 127.75))
seg(b, NRST, [(160.30, 127.75), (160.30, 136.90), (154.36, 142.84), (153.67, 142.84)], layer='B.Cu')
seg(b, GND, [(163.70, 126.25), (163.70, 127.75)], w=0.25)
via(b, GND, (163.70, 127.75))
retext('TP301:VSW_A TP302:VSW_B TP303:VTH TP304:FLT3', 'TP301-304: VSW_A VSW_B VTH FLT3')
newfp.text(b, 'RST', 159.40, 126.25, justify='right')

# ---- R13: 1 kohm in the line from the slide switch to PB4, back side under the MCU
rip(b, HV, 'B.Cu', [(186.90, 147.30), (183.25, 147.30)], expect=1)
put('R13', 184.80, 147.30, 'B', {'2': (184.29, 147.30), '1': (185.31, 147.30)}, ref_pos=(185.40, 146.25))
seg(b, HV, [(183.25, 147.30), (184.29, 147.30)], layer='B.Cu')
seg(b, PB4, [(185.31, 147.30), (186.90, 147.30)], layer='B.Cu')
renet(HV, PB4, 'B.Cu', [(186.90, 147.30), (187.60, 148.00), (189.50, 148.00), (190.10, 148.60)])
renet_via(HV, PB4, (190.10, 148.60))
renet(HV, PB4, 'F.Cu', [(190.10, 148.60), (190.75, 149.25), (190.75, 153.40), (190.50, 153.65), (189.575, 153.65)])
pin = [p for p in b.FindFootprintByReference('U2').Pads() if p.GetNumber() == '57']
assert len(pin) == 1 and pin[0].GetNetname() == HV and comps['U2']['pins']['57'] == PB4
pin[0].SetNet(net(b, PB4))

# ---- screw holes: clearance holes for the screws they are meant for (the pads stay as they are)
n = {'Screw_PTH_2mm': 0, 'Screw_PTH_3mm': 0}
for fp in b.GetFootprints():
    v = fp.GetValue()
    if v in n:
        old, new = {'Screw_PTH_2mm': (2.0, 2.4), 'Screw_PTH_3mm': (3.0, 3.2)}[v]
        for p in fp.Pads():
            assert p.GetDrillSize().x == int(old * MM), (v, p.GetDrillSize().x)
            p.SetDrillSize(pcbnew.VECTOR2I(int(new * MM), int(new * MM)))
            n[v] += 1
assert n == {'Screw_PTH_2mm': 2, 'Screw_PTH_3mm': 4}, n

print('items removed:', flush(b))
pcbnew.SaveBoard(dst, b)
print('saved', dst)

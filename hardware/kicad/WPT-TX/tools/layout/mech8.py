#!/usr/bin/env python3
"""Fourth revision, part 2: fast comparators on the board, J301 removed. usage: mech8.py BOARD_IN BOARD_OUT NETLIST

What the schematic edit (tools/schematic/edit_sch8.py) asks for, placed and routed by hand-chosen coordinates.

At the dividers (back side, beside the power stage; no existing part moves except R343):
  * C340 / C341 (36 pF, tap to ground) directly beside R340 / R342. C341 takes the place of TP223, the second +5 V test
    point (plated hole) on the same In2 trunk as TP213.
  * R343 moves from the MCU end of the tap line to the divider (191.90, 178.01), so that both taps are a few millimetres
    of copper and everything behind them sits behind 100 ohm. The old line keeps its copper and becomes VSWA_CMP.
  * The two lines to the top strip used to start at the taps. They now start behind R343 / R344 (nets VSWA_CMP /
    VSWB_CMP): leg A needs no new copper at all (the branch point is behind the new place of R343), leg B gets 0.5 mm.

Top strip (front side, where J301 stood):
  * U308 (leg A) and U309 (leg B), SOT-23-5 turned so that the three-pin row faces south: OUT south-west, GND south,
    IN+ south-east, IN- north-east, VCC north-west. Three vias under each body: +3V3, GND, and the tap from the back.
  * C342 / C343 (supply) on the back side under the comparators, between the +3V3 and GND vias.
  * C344 / C345 (threshold) north of the IN- pins, joined by a 3.5 mm bus; the threshold comes from R345, which sits in
    the place of R333 in the resistor row, along y = 131.55 (TP303 on the way).
  * U308 OUT -> R335 (in its old place) -> HRTIM1_EEV1 (old copper).
    U309 OUT -> 3.5 mm along the old lane y = 139.6 -> R337, which moves east of the SDA via with R338
    -> HRTIM1_EEV2 (the rest of the old lane). The old loop of EEV2 through the resistor row is removed.
  * The tap lines come in on the back side, leg A on y = 136.30 and leg B on y = 137.30, each through a via in the
    middle of a test pad (TP301 / TP302) east of the SDA via.
  * HRTIM1_FLT3 and ZVS_VTH_DAC (PB11) arrived on the back side at pads of J301 that linked them to the front; each
    gets a via there (the one of FLT3 inside test pad TP304).
"""
import shutil
import sys

import pcbnew

import newfp
from newfp import seg, via, rip, rip_via, place, pads, net, flush, P, V

src, dst, netlist = sys.argv[1:4]
shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)
comps = newfp.load_netlist(netlist)
N = lambda s: newfp.full_name(b, s)


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
    return k


def renet_via(old, new, c):
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == old and P(t.GetPosition()) == (round(c[0], 4), round(c[1], 4)):
            t.SetNet(net(b, new))
            return
    raise AssertionError(('no via', old, c))


def put(ref, x, y, rot, side, want, ref_pos=None, ref_rot=0.0):
    """place a new footprint, trying the given rotation and the opposite one until the pads are where `want` says;
    ref_pos = where its reference goes on the silkscreen (None: not shown, the dense places have no room for it)"""
    fp = place(b, comps, ref, x, y, rot=rot, side=side, hide_ref=ref_pos is None)
    for r in (rot, rot + 180):
        fp.SetOrientationDegrees(r)
        got = pads(fp)
        if all(abs(got[k][0] - v[0]) < 0.006 and abs(got[k][1] - v[1]) < 0.006 for k, v in want.items()):
            break
    else:
        raise AssertionError((ref, got, want))
    t = fp.Reference()
    t.SetPosition(V(*(ref_pos or (x, y))))
    t.SetTextAngleDegrees(ref_rot)
    return fp


def ref_to(ref, pos, show=True):
    t = b.FindFootprintByReference(ref).Reference()
    t.SetPosition(V(*pos))
    t.SetTextAngleDegrees(0)
    t.SetTextSize(pcbnew.VECTOR2I(int(0.7 * 1e6), int(0.8 * 1e6)))
    t.SetTextThickness(int(0.15 * 1e6))
    t.SetVisible(show)


VSWA_S, VSWB_S = N('VSWA_SENSE'), N('VSWB_SENSE')
VSWA_C, VSWB_C = N('VSWA_CMP'), N('VSWB_CMP')
EEV1, EEV2 = N('HRTIM1_EEV1'), N('HRTIM1_EEV2')
FLT3, FLT4 = N('HRTIM1_FLT3'), N('HRTIM1_FLT4')
ZA, ZB = N('ZVS_A_IN'), N('ZVS_B_IN')
DAC = comps['R345']['pins']['1']
VTH = comps['R345']['pins']['2']
assert DAC.endswith('ZVS_VTH_DAC') and VTH.endswith('ZVS_VTH') and comps['U2']['pins']['33'] == DAC
GND, V33 = 'GND', '+3V3'

# ================================================================== what goes
for ref in ('J301', 'R333', 'TP223'):
    newfp.remove_footprint(b, ref)
# J301 texts on the silkscreen
for d in list(b.GetDrawings()):
    if d.GetClass() == 'PCB_TEXT' and b.GetLayerName(d.GetLayer()) == 'F.Silkscreen':
        s = d.GetText()
        if s.startswith('J301  1:VSW_A') or s.startswith('6:ZVS_B') or s.startswith('J2  1:GND') or s.startswith('7:CS 8:DC'):
            newfp._PENDING.append(d)
        elif s == 'J2 / J301: 3.3 V MAX':
            d.SetText('J2: 3.3 V MAX')
# the loop of EEV2 through the resistor row and its lane west of the comb
rip(b, EEV2, 'F.Cu', [(174.81, 134.11), (175.18, 134.11), (175.44, 133.84), (175.44, 133.09), (176.08, 133.09), (176.08, 131.80), (176.38, 131.50),
                      (179.59, 131.50), (179.89, 131.80), (179.89, 139.30), (180.19, 139.60), (190.1157, 139.60)], expect=11)
rip(b, GND, 'F.Cu', [(174.81, 133.09), (174.81, 132.20)], expect=1)
rip_via(b, GND, (174.81, 132.20))                                   # ground via of R338 in its old place
rip(b, V33, 'F.Cu', [(169.73, 133.09), (169.73, 132.20)], expect=1)
rip_via(b, V33, (169.73, 132.20))                                   # +3V3 via of R333
rip(b, ZA, 'F.Cu', [(178.62, 134.11), (178.62, 136.42)], expect=1)
rip(b, ZB, 'F.Cu', [(176.08, 134.11), (176.08, 136.42)], expect=1)
# ends of the two tap lines in the strip
rip(b, VSWA_S, 'B.Cu', [(193.40, 141.04), (188.78, 136.42)], expect=1)
rip(b, VSWB_S, 'B.Cu', [(189.85, 138.90), (186.18, 138.90), (183.70, 136.42)], expect=2)
# starts of the two lines at the dividers
rip(b, VSWB_S, 'B.Cu', [(191.75, 168.11), (192.15, 168.11), (192.45, 167.81), (192.45, 165.55), (192.00, 165.10)], expect=4)
rip(b, VSWA_S, 'B.Cu', [(191.92, 179.60), (191.60, 179.28), (191.60, 177.20)], expect=2)

# ================================================================== nets of copper that stays
renet(FLT4, DAC, 'F.Cu', [(169.73, 134.11), (171.00, 134.11), (171.00, 136.42)])
for t in b.GetTracks():                                             # the rest of PB11's copper (back side, MCU end)
    if t.GetNetname() == FLT4:
        t.SetNet(net(b, DAC))
renet(VSWA_S, VSWA_C, 'B.Cu', [(191.60, 177.20), (187.15, 172.75), (187.15, 166.56), (186.19, 165.60), (185.00, 164.41)])
renet(VSWA_S, VSWA_C, 'B.Cu', [(186.19, 165.60), (190.00, 165.60)])
renet_via(VSWA_S, VSWA_C, (190.00, 165.60))
renet(VSWA_S, VSWA_C, 'F.Cu', [(190.00, 165.60), (190.40, 165.20), (192.40, 165.20), (193.05, 165.20)])
renet_via(VSWA_S, VSWA_C, (193.05, 165.20))
renet(VSWA_S, VSWA_C, 'B.Cu', [(193.05, 165.20), (192.40, 164.55), (192.40, 160.40), (193.40, 159.40), (193.40, 141.04)])
renet(VSWB_S, VSWB_C, 'B.Cu', [(192.00, 165.10), (192.00, 141.05), (189.85, 138.90)])

# ================================================================== dividers
fp = b.FindFootprintByReference('R343')
fp.SetPosition(V(191.90, 178.01))
for rot in (90.0, 270.0):
    fp.SetOrientationDegrees(rot)
    if abs(pads(fp)['2'][1] - 178.52) < 0.006:
        break
assert pads(fp) == {'1': (191.9, 177.5), '2': (191.9, 178.52)}, pads(fp)
for p in fp.Pads():
    p.SetNet(net(b, comps['R343']['pins'][p.GetNumber()]))
ref_to('R343', (193.95, 178.01))
seg(b, VSWA_S, [(191.90, 179.45), (191.90, 178.52)], layer='B.Cu')                 # C338 pad 2 -> R343
seg(b, VSWA_C, [(191.90, 177.50), (191.60, 177.20)], layer='B.Cu')                 # R343 -> the old line
seg(b, VSWA_C, [(185.00, 164.41), (185.00, 163.39)], layer='B.Cu')                 # across the old place of R343
put('C340', 190.20, 179.75, 0.0, 'B', {'1': (190.68, 179.75), '2': (189.72, 179.75)}, ref_pos=(189.85, 178.70))
seg(b, VSWA_S, [(190.70, 179.75), (190.70, 180.90)], layer='B.Cu')
seg(b, GND, [(189.70, 179.75), (189.70, 180.90)], w=0.25, layer='B.Cu')
put('C341', 190.15, 167.85, 0.0, 'B', {'1': (190.63, 167.85), '2': (189.67, 167.85)}, ref_pos=(190.15, 166.45))
seg(b, VSWB_S, [(190.63, 167.85), (190.63, 168.37), (190.96, 168.70), (190.96, 169.00)], layer='B.Cu')
seg(b, GND, [(189.67, 167.85), (189.67, 168.43), (189.94, 168.70), (189.94, 169.00)], w=0.25, layer='B.Cu')
seg(b, VSWB_C, [(191.75, 165.45), (192.00, 165.20), (192.00, 165.10)], layer='B.Cu')   # R344 -> the line north

# ================================================================== top strip: parts
u308 = put('U308', 179.75, 137.20, 90.0, 'F', {'1': (178.80, 138.3375), '3': (180.70, 138.3375), '4': (180.70, 136.0625), '5': (178.80, 136.0625)},
           )
u309 = put('U309', 183.25, 137.20, 90.0, 'F', {'1': (182.30, 138.3375), '3': (184.20, 138.3375), '4': (184.20, 136.0625), '5': (182.30, 136.0625)},
           )
put('C342', 179.275, 138.35, 0.0, 'B', {'1': (178.795, 138.35), '2': (179.755, 138.35)}, ref_pos=(179.275, 139.55))
put('C343', 182.775, 138.35, 0.0, 'B', {'1': (182.295, 138.35), '2': (183.255, 138.35)}, ref_pos=(182.775, 139.55))
put('C344', 180.70, 134.10, 90.0, 'F', {'1': (180.70, 134.58), '2': (180.70, 133.62)})
put('C345', 184.20, 134.10, 90.0, 'F', {'1': (184.20, 134.58), '2': (184.20, 133.62)})
put('R345', 169.73, 133.60, 90.0, 'F', {'1': (169.73, 134.11), '2': (169.73, 133.09)}, ref_pos=(167.68, 133.60))
for ref, x, y, want in (('R337', 187.00, 138.70, {'1': (186.49, 138.70), '2': (187.51, 138.70)}),
                        ('R338', 188.90, 138.19, {'1': (188.90, 138.70), '2': (188.90, 137.68)})):
    fp = b.FindFootprintByReference(ref)
    fp.SetPosition(V(x, y))
    for rot in (0.0, 90.0, 180.0, 270.0):
        fp.SetOrientationDegrees(rot)
        got = pads(fp)
        if all(abs(got[k][0] - v[0]) < 0.006 and abs(got[k][1] - v[1]) < 0.006 for k, v in want.items()):
            break
    else:
        raise AssertionError((ref, got))
    for p in fp.Pads():
        p.SetNet(net(b, comps[ref]['pins'][p.GetNumber()]))
ref_to('R337', (187.00, 138.70), show=False)                  # no room on the silkscreen east of the SDA via: see the assembly drawing
ref_to('R338', (188.90, 138.19), show=False)
ref_to('R335', (179.21, 130.55))                               # its place east of the row is taken by C344
ref_to('R12', (151.55, 146.40))
b.FindFootprintByReference('R12').Reference().SetTextAngleDegrees(90)
tp301 = put('TP301', 187.90, 136.30, 0.0, 'F', {'1': (187.90, 136.30)})
tp302 = put('TP302', 186.10, 137.30, 0.0, 'F', {'1': (186.10, 137.30)})
tp303 = put('TP303', 182.60, 133.00, 0.0, 'F', {'1': (182.60, 133.00)})
tp304 = put('TP304', 173.54, 136.42, 0.0, 'F', {'1': (173.54, 136.42)})
# nets of pads whose net changed with the schematic (PB11, the resistors that stay)
for ref in ('U2', 'R334', 'R335', 'R336', 'R337', 'R338', 'R344', 'R332', 'R331'):
    for p in b.FindFootprintByReference(ref).Pads():
        nm = comps[ref]['pins'].get(p.GetNumber())
        if nm is not None and p.GetNetname() != nm:
            p.SetNet(net(b, nm))

# ================================================================== top strip: copper
# U308: vias under the body, supply capacitor on the back
via(b, V33, (178.80, 137.10)); seg(b, V33, [(178.80, 137.10), (178.80, 136.40)], w=0.25)
via(b, GND, (179.75, 137.20)); seg(b, GND, [(179.75, 137.20), (179.75, 138.00)], w=0.25)
via(b, VSWA_C, (180.70, 137.30)); seg(b, VSWA_C, [(180.70, 137.30), (180.70, 138.00)])
seg(b, V33, [(178.80, 137.10), (178.80, 138.35)], w=0.25, layer='B.Cu')
seg(b, GND, [(179.75, 137.20), (179.75, 138.35)], w=0.25, layer='B.Cu')
# U309
via(b, V33, (182.30, 137.10)); seg(b, V33, [(182.30, 137.10), (182.30, 136.40)], w=0.25)
via(b, GND, (183.25, 137.20)); seg(b, GND, [(183.25, 137.20), (183.25, 138.00)], w=0.25)
via(b, VSWB_C, (184.20, 137.30)); seg(b, VSWB_C, [(184.20, 137.30), (184.20, 138.00)])
seg(b, V33, [(182.30, 137.10), (182.30, 138.35)], w=0.25, layer='B.Cu')
seg(b, GND, [(183.25, 137.20), (183.25, 138.35)], w=0.25, layer='B.Cu')
# tap lines on the back, through the test pads
seg(b, VSWA_C, [(193.40, 141.04), (188.66, 136.30), (181.70, 136.30), (180.70, 137.30)], layer='B.Cu')
via(b, VSWA_C, (187.90, 136.30))
seg(b, VSWB_C, [(189.85, 138.90), (188.25, 137.30), (184.20, 137.30)], layer='B.Cu')
via(b, VSWB_C, (186.10, 137.30))
# outputs
seg(b, ZA, [(178.80, 138.3375), (178.10, 138.3375), (178.10, 134.63), (178.62, 134.11)])
seg(b, ZB, [(182.30, 138.3375), (182.30, 139.30), (182.60, 139.60), (185.99, 139.60), (186.49, 139.10), (186.49, 138.70)])
seg(b, EEV2, [(187.51, 138.70), (188.90, 138.70), (188.90, 139.30), (189.20, 139.60), (190.1157, 139.60)])   # the old lane ends there
seg(b, GND, [(188.90, 137.68), (188.90, 136.60), (189.50, 136.00)], w=0.25)
via(b, GND, (189.50, 136.00))
# threshold
seg(b, VTH, [(169.73, 133.09), (169.73, 131.85), (170.03, 131.55), (182.30, 131.55), (182.60, 131.85), (182.60, 134.58)])
seg(b, VTH, [(180.70, 134.58), (184.20, 134.58)])
seg(b, VTH, [(180.70, 134.58), (180.70, 135.70)])
seg(b, VTH, [(184.20, 134.58), (184.20, 135.70)])
seg(b, GND, [(180.70, 133.62), (180.70, 132.75)], w=0.25); via(b, GND, (180.70, 132.75))
seg(b, GND, [(184.20, 133.62), (184.20, 132.75)], w=0.25); via(b, GND, (184.20, 132.75))
# the two nets that changed layer in a pad of J301
via(b, FLT3, (173.54, 136.42))
via(b, DAC, (171.00, 136.42))

# silkscreen: the two legend lines of J301 become one for the test pads and one for the comparators; the pin list of J2
# moves west of the comparators (three lines instead of two); a word beside each pad
newfp.text(b, 'TP301:VSW_A TP302:VSW_B TP303:VTH TP304:FLT3', 188.9, 127.3, justify='right')
newfp.text(b, 'U308: leg A > EEV1  U309: leg B > EEV2', 188.9, 128.6, justify='right')
newfp.text(b, 'J2  1:GND 2:+3V3 3:SCK', 157.6, 137.35)
newfp.text(b, '4:MISO 5:MOSI 6:ADC 7:CS 8:DC', 157.6, 138.45)
newfp.text(b, '9:RST 10:IO 11:+3V3 12:GND', 157.6, 139.55)
newfp.text(b, 'A', 189.05, 135.40, justify='center')
newfp.text(b, 'B', 186.10, 135.90, justify='center')
newfp.text(b, 'VTH', 182.60, 131.55, justify='center')
newfp.text(b, 'FLT3', 174.65, 136.42)

print('items removed:', flush(b))
pcbnew.SaveBoard(dst, b)
print('saved', dst)

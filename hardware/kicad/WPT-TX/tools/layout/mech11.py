#!/usr/bin/env python3
"""Revision 7, part 1: the switch-node comparators move to the back side beside the MCU. usage: mech11.py BOARD_IN BOARD_OUT NETLIST

What tools/schematic/edit_sch11.py asks for (detection part), with hand-chosen coordinates. All new parts are on the back.

Why here. A through via needs a free spot on the front side too, and south of the MCU the front side is nearly closed.
Three islands are left: R1 (a slanted band about 180.6..183.2 / 165.0..165.9 with a tip at (182.3, 166.45)),
R2 (175..180.5 / 166.0..167.9, narrowing down to (179, 169.6)) and R3 (181.9..184.3 / 170.4..177.6). The inner layer In2 is
the +3V3 plane north of y = 163.2 and the +5V plane south of it, so every supply via of the comparators hangs on a short
In2 track ("finger") that starts in the +3V3 plane. The pad of TP213 (through hole, with a round courtyard) stands in the
middle; the line of leg B passes north of it, the line of leg A south of it.

  U309 (leg B)  (180.80, 164.65), pins towards east: OUT north, GND, IN+ south. Ground via under the body.
                C341 and R342 (lower leg) directly across the GND and IN+ pins; R337 and R338 at the output.
  U308 (leg A)  (179.10, 169.60), turned by 90 degrees: OUT, GND, IN+ on the north row, IN+ at the east end.
                C340 across the GND and IN+ pins, R340 on the line, R335 at the output.
  lines         leg B: R344 - north - west along y = 165.55 - R342 - C341 - IN+ (10.8 mm, was 55 mm).
                leg A: R343 - the old diagonal - north along x = 187.15 - west - between TP213 and the gate line of
                HRTIM1_CHC2 - west along y = 168.46 - R340 - IN+ (19.2 mm, was 80 mm).
  outputs       leg B = HRTIM1_EEV1: R337 - R338 - x = 185.3 north - via under the MCU - front side - pin 54 (PC12), 12.9 mm.
                leg A = HRTIM1_EEV2: R335 - between the two comparators - via (182.3, 166.45) - In2 (9.3 mm) -
                via (188.6, 160.8) with R336 beside it - back side - via under the MCU - front side - pin 53 (PC11),
                23.8 mm. On one layer this output would have to cross the line of leg B; the hop is the price of
                keeping both lines on one layer without a via. Under the MCU the western of the two vias can only
                reach pin 54, which is why the two event inputs changed places (edit_sch11.py).
  supply        +3V3 of U309: via in the strip between the I2C track "SDA" and the comparator, directly into the +3V3
                plane (the SDA track on the back moves 0.4 mm north for it, to 0.45 mm beside SCL).
                +3V3 of U308: via in R2 on a finger of the +3V3 plane (4.9 mm on In2).
  threshold     ZVS_VTH_DAC comes on In2 (6.5 mm) from the via under the MCU to a via in the same strip; R334, R345
                and C345 there; the filtered threshold goes east to U309 and south, round the west side of U308,
                to C344 and U308.
  test pads     TP302 on the line of leg B, TP301 on a 3 mm branch of the line of leg A, TP303 on the threshold
                (front-side track from a via). The front side has no room for them at the comparators.

Everything of the old arrangement goes: the parts of the top strip, both long lines, the branches to PA1 / PC1.
"""
import shutil
import sys

import pcbnew

import newfp
from newfp import seg, via, place, pads, net, flush, P, V

src, dst, netlist = sys.argv[1:4]
shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)
comps = newfp.load_netlist(netlist)
MM = newfp.MM
NETS = {n for c in comps.values() for n in c['pins'].values()}


def N(short):
    hit = [n for n in NETS if n == short or n.split('/')[-1] == short]
    assert len(hit) == 1, (short, hit)
    net(b, hit[0])
    return hit[0]


def put(ref, x, y, want, rots=(0, 90, 180, 270), side='B'):
    """remove the footprint `ref` (if the board has it) and place a new one; turn it until the pads named in `want` are there"""
    if b.FindFootprintByReference(ref) is not None:
        newfp.remove_footprint(b, ref)
    fp = place(b, comps, ref, x, y, rot=rots[0], side=side)
    for r in rots:
        fp.SetOrientationDegrees(r)
        got = pads(fp)
        if all(abs(got[k][0] - v[0]) < 0.02 and abs(got[k][1] - v[1]) < 0.02 for k, v in want.items()):
            break
    else:
        raise AssertionError((ref, got, want))
    t = fp.Reference()
    t.SetPosition(V(x, y))
    t.SetTextAngleDegrees(0)
    return fp


def uid(item):
    return item.m_Uuid.AsString()


def gone():
    """the items already marked for removal (two proxies of one board item are different Python objects: compare by UUID)"""
    return {uid(x) for x in newfp._PENDING}


def tracks_at(pt, layer, netname):
    out, g = [], gone()
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != netname or b.GetLayerName(t.GetLayer()) != layer:
            continue
        if uid(t) in g:
            continue
        if P(t.GetStart()) == pt or P(t.GetEnd()) == pt:
            out.append(t)
    return out


def vias_at(pt, netname):
    g = gone()
    return [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == netname and P(t.GetPosition()) == pt
            and uid(t) not in g]


def rip_net(short, keep=()):
    """all copper of the net but the pieces on the polylines in `keep` ((layer, points), ...) and the vias at their ends"""
    name = [n for n in (str(k) for k in b.GetNetInfo().NetsByName().keys()) if n == short or n.split('/')[-1] == short]
    assert name, short
    k, g = 0, gone()
    for nm in name:
        for t in list(b.GetTracks()):
            if t.GetNetname() != nm or uid(t) in g:
                continue
            if t.Type() == pcbnew.PCB_VIA_T:
                c = P(t.GetPosition())
                if any(newfp.on_line(c, p, q) for _, pts in keep for p, q in zip(pts, pts[1:])):
                    continue
            else:
                a, e, lay = P(t.GetStart()), P(t.GetEnd()), b.GetLayerName(t.GetLayer())
                if any(l == lay and newfp.on_line(a, p, q) and newfp.on_line(e, p, q) for l, pts in keep for p, q in zip(pts, pts[1:])):
                    continue
            newfp._PENDING.append(t)
            k += 1
    return k


def rip_stub(pt, layer, short):
    """the dead-end piece of track that starts at `pt`: followed until a point where something else of the net hangs
    (a third track, a pad that stays); a via that is left without tracks goes too"""
    name = newfp.full_name(b, short) if short not in ('GND', '+3V3') else short
    here, k = (round(pt[0], 4), round(pt[1], 4)), 0
    while True:
        ts = tracks_at(here, layer, name)
        if len(ts) != 1:
            break
        t = ts[0]
        newfp._PENDING.append(t)
        k += 1
        here = P(t.GetEnd()) if P(t.GetStart()) == here else P(t.GetStart())
        vs = vias_at(here, name)
        if vs:
            if not any(tracks_at(here, l, name) for l in ('F.Cu', 'B.Cu', 'In1.Cu', 'In2.Cu')):
                newfp._PENDING.extend(vs)
            break
    assert k, ('nothing at', pt, layer, short)
    return k


# ------------------------------------------------------------------ what goes
OLD = {r: {p.GetNumber(): (P(p.GetPosition()), 'B.Cu' if b.FindFootprintByReference(r).IsFlipped() else 'F.Cu')
           for p in b.FindFootprintByReference(r).Pads()}
       for r in ('U308', 'U309', 'C342', 'C343', 'C344', 'C345', 'R334', 'R336', 'R338', 'R340', 'C340', 'R342', 'C341')}   # (kept for reference)
for short in ('VSWA_CMP', 'VSWB_CMP', 'HRTIM1_EEV1', 'HRTIM1_EEV2', 'ZVS_VTH', 'ZVS_A_IN', 'ZVS_B_IN'):
    rip_net(short)
rip_net('ZVS_VTH_DAC', keep=(('F.Cu', [(180.15, 160.325), (180.15, 159.575), (179.925, 159.35), (178.45, 159.35), (176.4, 157.3), (176.3, 157.3)]),))
# the lower legs leave the taps
for a, e in (((190.63, 167.85), (190.63, 168.37)), ((190.63, 168.37), (190.96, 168.7)), ((190.96, 168.7), (190.96, 169.0)), ((191.99, 169.0), (190.96, 169.0))):
    newfp.rip(b, N('VSWB_SENSE'), 'B.Cu', [a, e], expect=1)
for a, e in (((190.71, 180.9), (191.89, 180.9)), ((190.7, 179.75), (190.7, 180.9))):
    newfp.rip(b, N('VSWA_SENSE'), 'B.Cu', [a, e], expect=1)
# ground and supply stubs of the parts that move
for pt, layer, short in (((188.9, 137.68), 'F.Cu', 'GND'), ((183.25, 138.0), 'F.Cu', 'GND'), ((184.2, 133.62), 'F.Cu', 'GND'), ((179.75, 138.0), 'F.Cu', 'GND'),
                         ((171.0, 133.09), 'F.Cu', 'GND'), ((180.7, 133.62), 'F.Cu', 'GND'), ((176.2, 137.29), 'F.Cu', 'GND'),
                         ((183.25, 138.35), 'B.Cu', 'GND'), ((179.75, 138.35), 'B.Cu', 'GND'),
                         ((189.67, 167.85), 'B.Cu', 'GND'), ((189.7, 179.75), 'B.Cu', 'GND'),
                         ((182.3, 136.4), 'F.Cu', '+3V3'), ((178.8, 136.4), 'F.Cu', '+3V3'), ((182.3, 138.35), 'B.Cu', '+3V3'), ((178.8, 138.35), 'B.Cu', '+3V3')):
    rip_stub(pt, layer, short)

# ------------------------------------------------------------------ the SDA track on the back makes room for a via
SDA = newfp.full_name(b, 'SDA')
newfp.rip(b, SDA, 'B.Cu', [(171.9, 162.65), (181.05, 162.65), (184.65, 159.05)], expect=2)
seg(b, SDA, [(171.9, 162.65), (172.3, 162.25), (181.45, 162.25), (184.65, 159.05)], layer='B.Cu')

# ------------------------------------------------------------------ U309, leg B -> HRTIM1_EEV1 (pin 54)
NX, NY = 180.8, 164.65
E, W = NX + 1.1375, NX - 1.1375
put('U309', NX, NY, {'1': (E, NY - 0.95), '3': (E, NY + 0.95), '5': (W, NY - 0.95)})
put('C341', 183.4, 165.04, {'1': (183.4, 165.52)})
put('R342', 184.42, 165.02, {'1': (184.42, 165.53)})
put('R337', 183.87, 163.5, {'1': (183.36, 163.5)})
put('R338', 185.47, 164.0, {'1': (185.47, 163.49)})
put('C343', 178.2, 164.18, {'1': (178.2, 163.7)})
G, V3, VTH, DAC = 'GND', '+3V3', N('ZVS_VTH'), N('ZVS_VTH_DAC')
via(b, G, (NX, 165.05))
seg(b, G, [(178.2, 164.66), (E, 164.66)], w=0.25, layer='B.Cu')                 # C343 - under the body - pin 2
seg(b, G, [(NX, 164.66), (NX, 165.05)], w=0.25, layer='B.Cu')
seg(b, G, [(E, 164.55), (185.47, 164.55)], w=0.25, layer='B.Cu')               # pin 2 - C341 - R342 - R338
via(b, V3, (178.2, 162.95))
seg(b, V3, [(178.2, 162.95), (178.2, 163.7), (W, 163.7)], w=0.25, layer='B.Cu')
seg(b, V3, [(178.2, 162.95), (178.2, 162.3)], w=0.5, layer='In2.Cu')
TB = N('VSWB_CMP')
seg(b, TB, [(E, 165.55), (190.87, 165.55), (191.75, 166.43), (191.75, 167.09)], layer='B.Cu')
via(b, TB, (190.0, 165.55))
put('TP302', 190.35, 165.55, {'1': (190.35, 165.55)}, side='F')
seg(b, N('ZVS_B_IN'), [(E, 163.7), (182.6, 163.7), (182.8, 163.5), (183.36, 163.5)], layer='B.Cu')
EEV1 = N('HRTIM1_EEV1')
seg(b, EEV1, [(184.38, 163.5), (185.3, 163.5), (185.3, 157.0)], layer='B.Cu')   # R337 - R338 - north through the gap between the pins
via(b, EEV1, (185.3, 157.0))
seg(b, EEV1, [(185.3, 157.0), (185.3, 156.2), (186.35, 155.15), (189.575, 155.15)], layer='F.Cu')

# ------------------------------------------------------------------ U308, leg A -> HRTIM1_EEV2 (pin 53)
SX, SY = 179.1, 169.6
RN, RS = SY - 1.1375, SY + 1.1375
put('U308', SX, SY, {'1': (SX - 0.95, RN), '3': (SX + 0.95, RN), '5': (SX - 0.95, RS)})
put('C340', 179.575, 166.95, {'1': (180.055, 166.95)})
put('R340', 181.38, 168.97, {'1': (181.38, 168.46)})
put('R335', 178.1, 166.5, {'1': (178.1, 167.01)})
put('C342', 178.63, 172.2, {'1': (178.15, 172.2)})
put('C344', 180.54, 172.2, {'1': (180.06, 172.2)})
via(b, G, (SX, 169.5))
seg(b, G, [(SX, 166.95), (SX, 172.2)], w=0.25, layer='B.Cu')                    # C340 - pin 2 - via - between the south pads - C342
via(b, G, (182.5, 170.35))
seg(b, G, [(181.38, 169.48), (181.63, 169.48), (182.5, 170.35)], w=0.25, layer='B.Cu')   # R340
via(b, G, (182.1, 172.2))
seg(b, G, [(181.02, 172.2), (182.1, 172.2)], w=0.25, layer='B.Cu')              # C344
TA = N('VSWA_CMP')
seg(b, TA, [(SX + 0.95, 166.95), (SX + 0.95, RN)], layer='B.Cu')
seg(b, TA, [(SX + 0.95, 168.46), (184.29, 168.46), (185.15, 167.6), (187.0, 167.6), (187.15, 167.75), (187.15, 172.75), (191.9, 177.5)], layer='B.Cu')
seg(b, N('ZVS_A_IN'), [(SX - 0.95, RN), (SX - 0.95, 167.01)], layer='B.Cu')
via(b, TA, (187.6, 177.2))                                                      # test pad on the front, on a branch of the line
seg(b, TA, [(189.4, 175.0), (187.6, 176.8), (187.6, 177.2)], layer='B.Cu')
put('TP301', 187.6, 177.2, {'1': (187.6, 177.2)}, side='F')
EEV2 = N('HRTIM1_EEV2')
via(b, EEV2, (182.3, 166.45))
seg(b, EEV2, [(178.1, 165.99), (178.38, 166.27), (182.12, 166.27), (182.3, 166.45)], layer='B.Cu')     # between the two comparators
seg(b, EEV2, [(182.3, 166.45), (186.15, 162.6), (187.9, 162.6), (188.6, 161.9), (188.6, 160.8)], layer='In2.Cu')
via(b, EEV2, (188.6, 160.8))
put('R336', 189.4, 161.3, {'1': (189.4, 160.79)})
seg(b, EEV2, [(189.4, 160.8), (188.6, 160.8), (186.0, 158.2), (186.0, 157.5)], layer='B.Cu')
via(b, EEV2, (186.0, 157.5))
seg(b, EEV2, [(186.0, 157.5), (186.0, 156.5), (186.85, 155.65), (189.575, 155.65)], layer='F.Cu')
via(b, G, (190.2, 161.5))
seg(b, G, [(189.4, 161.81), (189.89, 161.81), (190.2, 161.5)], w=0.25, layer='B.Cu')                 # R336
seg(b, V3, [(SX - 0.95, RS), (SX - 0.95, 172.2)], w=0.25, layer='B.Cu')         # pin 5 - C342
via(b, V3, (177.3, 167.75))
seg(b, V3, [(177.3, 167.75), (177.3, 170.74), (SX - 0.95, 170.74)], w=0.25, layer='B.Cu')
seg(b, V3, [(177.3, 162.9), (177.3, 167.75)], w=0.3, layer='In2.Cu')

# ------------------------------------------------------------------ threshold
put('R334', 175.0, 163.55, {'1': (175.51, 163.55)})
put('R345', 176.5, 164.07, {'1': (176.5, 163.56)})
put('C345', 176.5, 166.01, {'1': (176.5, 165.53)})
via(b, DAC, (175.5, 162.9))
seg(b, DAC, [(176.3, 157.3), (177.0, 158.0), (177.0, 160.6), (175.5, 162.1), (175.5, 162.9)], layer='In2.Cu')
seg(b, DAC, [(175.5, 162.9), (175.5, 163.55), (176.5, 163.55)], layer='B.Cu')
seg(b, VTH, [(176.5, 164.58), (176.5, 165.53)], layer='B.Cu')                    # R345 - C345
seg(b, VTH, [(176.5, 165.4), (179.3, 165.4)], layer='B.Cu')                      # east to U309
seg(b, VTH, [(176.5, 165.53), (175.88, 165.53), (175.6, 165.81), (175.6, 167.3), (176.3, 168.0), (176.3, 172.3), (176.85, 172.85), (179.6, 172.85),
             (180.05, 172.4)], layer='B.Cu')                                     # south to U308
seg(b, VTH, [(SX + 0.95, RS), (SX + 0.95, 172.2)], layer='B.Cu')                 # pin 4 - C344
via(b, VTH, (175.6, 166.55))                                                    # test pad on the front, from the line to U308
seg(b, VTH, [(175.6, 166.55), (178.5, 166.55)], layer='F.Cu')
put('TP303', 178.5, 166.55, {'1': (178.5, 166.55)}, side='F')
via(b, G, (176.5, 167.25))
seg(b, G, [(176.5, 166.49), (176.5, 167.25)], w=0.25, layer='B.Cu')              # C345
seg(b, G, [(174.49, 163.55), (174.026, 163.55), (173.701, 163.875)], w=0.25, layer='B.Cu')   # R334 to a via under U203

# ------------------------------------------------------------------ pads of the parts that stay take the nets of the new netlist
k, g = 0, gone()
for fp in b.GetFootprints():
    if uid(fp) in g:
        continue
    c = comps.get(fp.GetReference())
    if c is None or fp.GetReference() == 'J2':
        continue
    for pad in fp.Pads():
        nm = c['pins'].get(pad.GetNumber())
        if nm is not None and pad.GetNetname() != nm:
            pad.SetNet(net(b, nm))
            k += 1
print('pads with a new net:', k)
print('clock input: tracks renamed', newfp.rename_tracks(b, 'Net-(U2-PF0)', 'HSE_EXT'))
seen, once = set(), []
for x in newfp._PENDING:                       # an item marked twice would be removed twice (pcbnew crashes on that)
    if uid(x) not in seen:
        seen.add(uid(x))
        once.append(x)
print('marked twice:', len(newfp._PENDING) - len(once))
newfp._PENDING[:] = once
print('removed', flush(b))
pcbnew.SaveBoard(dst, b)

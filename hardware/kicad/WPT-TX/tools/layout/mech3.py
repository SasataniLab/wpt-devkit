#!/usr/bin/env python3
"""Second part of the mechanical revision (after mech2.py). usage: mech3.py BOARD_IN BOARD_OUT

  * copper made obsolete by mech2.py (stubs of parts that moved, the old SWD / EEV / fault-line pieces) goes out;
    so does the fan-out of the MCU's east pin column, which phys6.py lays out again
  * the two solder-mask lines along the old top edge (y = 135) go out: they would open the mask across the board
  * J3 (SWD) moves to the west edge, vertical, pin 1 at (153.22, 135.20): outside the area a display shield on J2
    would cover
  * R331..R338 (the parts of J301) go to the top side into the strip north of J301, one column per 1.27 mm,
    each with the pad that belongs to a header pin facing that pin
  * the area under the slide switch becomes a ring under the walls of its metal cover, with silkscreen bars under them
  * C16 gets its two connections; the ~{WLAT} track clears the new mounting hole at (155, 200)
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

# ---- what goes out: (net, box, layers) - every track with both ends in the box, every via in the box
KILL = [
    ('SWDIO', (158.0, 135.0, 188.0, 139.0), None),                 # old run along the former top edge
    ('SWCLK', (190.0, 148.5, 191.5, 157.5), ('B.Cu',)),            # old back-side lane under the east pads
    ('SWCLK', (190.3, 157.0, 191.5, 157.3), None),                 # stub to the via and the via
    ('HRTIM1_EEV1', (190.3, 149.0, 192.5, 155.5), None),
    ('HRTIM1_EEV2', (188.0, 155.4, 188.9, 155.9), None),           # inner via and its stub
    ('HRTIM1_EEV2', (174.5, 138.3, 175.5, 139.6), None),
    ('HV_SW_STATE', (190.05, 147.9, 191.5, 153.9), None),          # back-side lane from the outer via; F.Cu stub to it
    ('HV_SW_STATE', (189.7, 153.6, 191.2, 153.7), ('F.Cu',)),
    ('GPIO_VUSB_SENSE', (190.3, 155.9, 191.5, 156.5), None),
    ('HRTIM1_FLT3', (169.6, 139.9, 170.4, 140.7), ('B.Cu',)),      # old entry between the header pins
    ('USB_D_P', (191.2, 137.3, 192.2, 162.4), ('F.Cu',)),          # the pair east of the MCU is laid out again
    ('USB_D_N', (192.3, 137.3, 193.4, 162.8), ('F.Cu',)),
    ('GND', (163.5, 137.5, 187.0, 140.6), None),                   # plane stubs of the parts that left the header gap
    ('+3V3', (163.5, 137.5, 187.0, 140.6), None),
    ('GND', (192.6, 163.3, 193.2, 163.9), None),                   # lone stitching via beside the screw terminal
    ('~{WLAT}', (157.1, 195.5, 158.0, 198.7), ('B.Cu',)),
]
T = lambda net, layer, a, e: ('T', net, layer) + tuple(sorted([a, e]))
keys = set()
for t in b.GetTracks():
    n = short(t.GetNetname())
    for net, (x0, y0, x1, y1), layers in KILL:
        if n != net:
            continue
        inb = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
        if t.Type() == pcbnew.PCB_VIA_T:
            if inb(P(t.GetPosition())):
                keys.add(('V', t.GetNetname(), P(t.GetPosition())))
        else:
            ln = b.GetLayerName(t.GetLayer())
            if (layers is None or ln in layers) and inb(P(t.GetStart())) and inb(P(t.GetEnd())):
                keys.add(T(t.GetNetname(), ln, P(t.GetStart()), P(t.GetEnd())))
# the USB pair keeps its pieces inside U3 (pin to pin) and south of the MCU
keep = {T('/USB_D_P', 'F.Cu', (191.35, 134.86), (191.35, 137.14)), T('/USB_D_N', 'F.Cu', (193.25, 134.86), (193.25, 137.14))}
keys -= keep

# ---- mask lines on the old top edge
drop = [d for d in b.GetDrawings() if d.GetClass() == 'PCB_SHAPE' and b.GetLayerName(d.GetLayer()) in ('F.Mask', 'B.Mask')
        and abs(d.GetStart().y / MM - 135.0) < 1e-3 and abs(d.GetEnd().y / MM - 135.0) < 1e-3]
mask_uuids = [d.m_Uuid.AsString() for d in drop]
print('mask lines to drop:', len(mask_uuids))

# ---- J3 to the west edge
j3 = b.FindFootprintByReference('J3')
j3.SetOrientationDegrees(0)
j3.SetPosition(V(153.22, 135.20))
print('J3', ' '.join('%s:%s(%.2f,%.2f)' % (p.GetNumber(), short(p.GetNetname()), p.GetPosition().x / MM, p.GetPosition().y / MM) for p in j3.Pads()))

# ---- resistors of J301: top side, strip north of the header
COL = [('R333', 169.73, 'HRTIM1_FLT4'), ('R334', 171.00, 'HRTIM1_FLT4'), ('R331', 172.27, 'HRTIM1_FLT3'), ('R332', 173.54, 'HRTIM1_FLT3'),
       ('R338', 174.81, 'HRTIM1_EEV2'), ('R337', 176.08, 'ZVS_B_IN'), ('R336', 177.35, 'HRTIM1_EEV1'), ('R335', 178.62, 'ZVS_A_IN')]
YC = 133.60          # courtyard (1.96 mm long) ends 0.02 mm above the courtyard of J301
for ref, x, south in COL:
    fp = b.FindFootprintByReference(ref)
    if fp.IsFlipped():
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetPosition(V(x, YC))
    for rot in (90, -90):
        fp.SetOrientationDegrees(rot)
        s = [p for p in fp.Pads() if p.GetPosition().y / MM > YC][0]
        if short(s.GetNetname()) == south:
            break
    else:
        raise SystemExit('no orientation for ' + ref)
    print('  ', ref, 'F.Cu' if not fp.IsFlipped() else 'B.Cu', ' '.join('%s:%s(%.2f,%.2f)' % (p.GetNumber(), short(p.GetNetname()), p.GetPosition().x / MM, p.GetPosition().y / MM) for p in fp.Pads()))

# ---- keep-out under the slide switch: vias allowed
# The area becomes a ring that follows the walls of the cover (0.5 mm thick, on the outline 151.25..157.75 x 147.8..161.6):
# from 0.25 mm outside the outline to 0.4 mm inside the inner face of the wall. It carries no restriction of its own;
# the rule "SW2 metal cover: no signal vias" in the .kicad_dru file refers to it by name. Top-side tracks of four slow
# nets still pass under the walls (see docs/stm32-tx/layout_notes.md), so a 0.8 mm silkscreen bar is printed under each
# wall between the frame pads as a second insulating layer on top of the solder mask.
# (KiCad's intersectsArea() does not look at holes in a rule area, so the ring is made of four rectangles of one name.)
WALLS = (((156.85, 147.55), (158.0, 161.85)), ((151.0, 147.55), (152.15, 161.85)), ((152.15, 147.55), (156.85, 148.7)), ((152.15, 160.7), (156.85, 161.85)))
old_area = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName().startswith('SW2 metal cover')]
for k, ((x0, y0), (x1, y1)) in enumerate(WALLS):
    if k == 0:
        z = old_area[0]
        z.Outline().RemoveAllContours()
    else:
        z = pcbnew.ZONE(b)
        z.SetIsRuleArea(True)
        z.SetLayer(pcbnew.F_Cu)
        z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        (z.SetDoNotAllowZoneFills if hasattr(z, 'SetDoNotAllowZoneFills') else z.SetDoNotAllowCopperPour)(False)
        b.Add(z)
    o = z.Outline()
    o.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(int(x * MM), int(y * MM))
    z.SetDoNotAllowTracks(False)
    z.SetDoNotAllowVias(False)
    z.SetZoneName('SW2 metal cover: wall band')
for a, e in (((157.5, 150.3), (157.5, 159.1)), ((151.5, 150.3), (151.5, 159.1)), ((153.1, 148.05), (155.9, 148.05)), ((153.1, 161.35), (155.9, 161.35))):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(pcbnew.F_SilkS)
    s.SetStart(V(*a)); s.SetEnd(V(*e)); s.SetWidth(int(0.8 * MM))
    b.Add(s)

# ---- small pieces of copper
def seg(net, layer, pts, w):
    n = b.FindNet(net)
    assert n is not None, net
    for p, q in zip(pts, pts[1:]):
        s = pcbnew.PCB_TRACK(b)
        s.SetNet(n); s.SetLayer(b.GetLayerID(layer)); s.SetStart(V(*p)); s.SetEnd(V(*q)); s.SetWidth(int(round(w * MM)))
        b.Add(s)


ADC = '/WPT-01-TRANSMITTER-POWER/ADC_VDC'
seg(ADC, 'B.Cu', [(182.50, 151.30), (182.85, 151.65), (182.85, 152.22)], 0.2)          # C16 pad 1 on the line, 1.3 mm from the via of PA0
seg('GND', 'B.Cu', [(182.85, 153.18), (182.85, 153.60), (182.55, 153.90), (182.55, 154.20)], 0.25)   # C16 pad 2 to the GND via
WLAT = '/WPT-01-TRANSMITTER-POWER/~{WLAT}'
seg(WLAT, "B.Cu", [(157.19, 195.55), (157.19, 196.10), (157.59, 196.50), (157.59, 198.30), (157.91, 198.62), (158.82, 198.62)], 0.2)
pcbnew.SaveBoard(dst, b)
del b
n = rip_text(dst, keys)
print('removed', n, 'of', len(keys), 'copper items')
# mask lines out of the file as text
t = open(dst, encoding='utf-8').read()
for u in mask_uuids:
    i = t.index('(uuid "%s")' % u)
    j = t.rfind('\n\t(gr_line', 0, i)
    d = 0
    for k in range(j + 1, len(t)):
        if t[k] == '(':
            d += 1
        elif t[k] == ')':
            d -= 1
            if d == 0:
                break
    t = t[:j] + t[k + 1:]
open(dst, 'w', encoding='utf-8').write(t)
print('written', dst)

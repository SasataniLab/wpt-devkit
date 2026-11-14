#!/usr/bin/env python3
"""Mechanical revision of 2026-11-14: mounting holes on a 5 mm grid, and what follows from it.

usage: mech2.py BOARD_IN BOARD_OUT MCU.kicad_sch

  * outline 70 x 80 mm: 10 mm more at the top, 5 mm more at the bottom (was 70 x 65). The four corners of the old
    outline are occupied by parts; the added strips hold the mounting holes.
  * four M3 mounting holes (plated, GND, same footprint as before) 5 mm from the edges: (155, 130) (215, 130)
    (155, 200) (215, 200), i.e. 60 x 70 mm apart. The three old ones at (153.25, 144.07) (216.75, 138.25)
    (153.25, 196.75) move there, the fourth is new.
  * USB-C receptacle J5 with its protection and CC parts (U3, R9, R10) and its hand-made copper moves 10 mm up to the
    new top edge; the keep-out under its shell moves along.
  * pin headers on one 2.54 mm grid (origin J2 pin 1 at 158.30, 141.50): J2 stays; J301 becomes 1x10 (pin 9 = +3V3,
    pin 10 = GND), two grid rows... one row (5.08 mm) above J2, pin 1 at x = 188.78; J3 (SWD) goes into the new strip,
    four rows (10.16 mm) above J2; the resistors R331..R338 of J301 follow.
  * C16 (ADC_VDC filter) on the back under the MCU, 1.3 mm from the via of pin 12.
  * rule area on F.Cu under the slide switch SW2: its metal cover reaches down to the board along its outline.
  * net Net-(J1-Pin_1) is now /MCU/BOOT0 (label added in the schematic).
"""
import re
import shutil
import sys

import pcbnew

MM = 1e6
src, dst, mcu_sch = sys.argv[1:4]
txt = open(src, encoding='utf-8').read().replace('"Net-(J1-Pin_1)"', '"/MCU/BOOT0"')
open(dst, 'w', encoding='utf-8').write(txt)
b = pcbnew.LoadBoard(dst)
V = lambda x, y: pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
P = lambda v: (round(v.x / MM, 3), round(v.y / MM, 3))
short = lambda n: n.split('/')[-1]
DY = -10.0

# ---- outline and board-wide zones
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts:
        for get, put in ((d.GetStart, d.SetStart), (d.GetEnd, d.SetEnd)):
            x, y = P(get())
            if abs(y - 135.0) < 1e-3:
                put(V(x, 125.0))
            elif abs(y - 200.0) < 1e-3:
                put(V(x, 205.0))
nz = 0
for z in b.Zones():
    if z.GetIsRuleArea():
        if z.GetZoneName().startswith('J5 shell'):
            z.Move(V(0, DY))
        continue
    o = z.Outline()
    for i in range(o.TotalVertices()):
        x, y = P(o.CVertex(i))
        if abs(y - 135.5) < 1e-3:
            o.SetVertex(i, V(x, 125.5)); nz += 1
        elif abs(y - 199.5) < 1e-3:
            o.SetVertex(i, V(x, 204.5)); nz += 1
    z.SetNeedRefill(True)
print('zone corners moved:', nz)

# ---- mounting holes
HOLES = {(153.25, 144.07): (155.0, 130.0), (216.75, 138.25): (215.0, 130.0), (153.25, 196.75): (155.0, 200.0)}
proto = None
for fp in b.GetFootprints():
    if fp.GetReference().startswith('REF') and 'Screw_PTH_3mm' in fp.GetFPIDAsString():
        k = P(fp.GetPosition())
        k = [h for h in HOLES if abs(h[0] - k[0]) < 0.05 and abs(h[1] - k[1]) < 0.05]
        assert len(k) == 1
        fp.SetPosition(V(*HOLES[k[0]]))
        proto = fp
nf = pcbnew.Cast_to_FOOTPRINT(proto.Duplicate(False))
nf.SetPosition(V(215.0, 200.0))
b.Add(nf)

# ---- USB block
for ref in ('J5', 'U3', 'R9', 'R10'):
    fp = b.FindFootprintByReference(ref)
    fp.SetPosition(fp.GetPosition() + V(0, DY))
USBNETS = {'USB_D_P', 'USB_D_N', 'VBUS', 'Net-(J5-CC1)', 'Net-(J5-CC2)'}
GND_T = [((190.45, 142.5), (189.85, 142.5)), ((190.45, 142.5), (189.85, 143.1)), ((197.15, 142.5), (197.3, 142.5)), ((197.15, 142.5), (197.75, 142.5)),
         ((197.3, 142.5), (197.45, 142.65)), ((197.45, 142.65), (197.5, 142.65)), ((197.5, 142.65), (197.95, 143.1)), ((192.3, 147.4), (192.3, 148.9)),
         ((195.15, 145.35), (195.15, 145.95))]
GND_T = {frozenset(k) for k in GND_T}
GND_V = {(189.85, 142.5), (189.85, 143.1), (197.75, 142.5), (197.95, 143.1), (192.3, 148.9), (195.15, 145.95)}
inbox = lambda p: 188.5 <= p[0] <= 199.3 and 134.0 <= p[1] <= 148.0
moved = 0
vbus = gnd = None
for t in b.GetTracks():
    n = short(t.GetNetname())
    if t.Type() == pcbnew.PCB_VIA_T:
        p = P(t.GetPosition())
        if (n in USBNETS and inbox(p)) or (n == 'GND' and p in GND_V):
            t.SetPosition(V(p[0], p[1] + DY)); moved += 1
        continue
    a, e = P(t.GetStart()), P(t.GetEnd())
    if n == 'GND':
        gnd = t.GetNet()
        if frozenset((a, e)) in GND_T:
            t.SetStart(V(a[0], a[1] + DY)); t.SetEnd(V(e[0], e[1] + DY)); moved += 1
        elif frozenset((a, e)) == frozenset(((189.2, 145.7), (189.09, 144.6))):       # R10 ground: was a stub to C11's via
            t.SetStart(V(189.09, 134.6)); t.SetEnd(V(189.09, 133.0)); moved += 1
            r10seg = t
        continue
    if n in USBNETS:
        if n == 'VBUS':
            vbus = t.GetNet()
        if inbox(a):
            t.SetStart(V(a[0], a[1] + DY)); moved += 1
        if inbox(e):
            t.SetEnd(V(e[0], e[1] + DY))
print('USB block: copper items moved', moved)
# R10 0.6 mm further up, clear of the courtyard of J301
r10 = b.FindFootprintByReference('R10')
r10.SetPosition(r10.GetPosition() + V(0, -0.6))
r10seg.SetStart(V(189.09, 134.0))
for t in b.GetTracks():
    if t.Type() != pcbnew.PCB_VIA_T and short(t.GetNetname()) == 'Net-(J5-CC2)' and P(t.GetEnd()) == (190.3, 134.4):
        t.SetEnd(V(190.3, 134.0))


def seg(net, layer, p, q, w):
    s = pcbnew.PCB_TRACK(b)
    s.SetNet(net); s.SetLayer(layer); s.SetStart(V(*p)); s.SetEnd(V(*q)); s.SetWidth(int(w * MM))
    b.Add(s)


seg(gnd, pcbnew.F_Cu, (189.09, 133.0), (189.48, 132.61), 0.25)       # R10 ground into the shell pad of J5
seg(vbus, pcbnew.F_Cu, (197.6, 136.4), (197.6, 146.49), 0.25)        # VBUS on to the sense divider R7, which stays

# ---- headers
# J3 (SWD) goes into the new strip, two rows above J301: beside J301 the two header courtyards would overlap
j3 = b.FindFootprintByReference('J3')
j3.SetPosition(V(160.84, 131.34))
old = b.FindFootprintByReference('J301')
new = pcbnew.FootprintLoad('/usr/share/kicad/footprints/Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x10_P2.54mm_Vertical')
new.SetFPIDAsString('Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical')
new.SetReference('J301A')                                        # renamed to J301 once the old footprint is out of the file
new.SetValue('Conn_01x10_Pin')
new.SetPath(old.GetPath())
new.SetSheetname(old.GetSheetname()); new.SetSheetfile(old.GetSheetfile())
b.Add(new)
new.SetPosition(V(188.78, 136.42))
new.SetOrientationDegrees(old.GetOrientationDegrees())
oldnets = {p.GetNumber(): p.GetNet() for p in old.Pads()}
for p in new.Pads():
    k = p.GetNumber()
    p.SetNet(oldnets[k] if k in oldnets else b.FindNet('+3V3' if k == '9' else 'GND'))
print('J301 pins:', ' '.join('%s@%.2f' % (p.GetNumber(), p.GetPosition().x / MM) for p in new.Pads()), 'y %.2f' % (new.GetPosition().y / MM))
# resistors of the header (back side). FLT pull-ups / pull-downs above the pin row, in the new strip;
# ZVS series / pull-down resistors between the two header rows
PLACE = {'R332': (173.54, 134.3, 90), 'R331': (174.74, 134.3, -90), 'R334': (171.0, 134.3, 90), 'R333': (172.2, 134.3, -90),
         'R335': (179.13, 138.96, 0), 'R336': (181.05, 138.96, 0), 'R337': (175.57, 138.96, 180), 'R338': (173.6, 138.96, 180)}
for ref, (x, y, rot) in PLACE.items():
    fp = b.FindFootprintByReference(ref)
    fp.SetPosition(V(x, y)); fp.SetOrientationDegrees(rot)
    print('  ', ref, ' '.join('%s:%s(%.2f,%.2f)' % (p.GetNumber(), short(p.GetNetname())[:9], p.GetPosition().x / MM, p.GetPosition().y / MM) for p in fp.Pads()))

# ---- C16
t = open(mcu_sch, encoding='utf-8').read()
i = t.index('(property "Reference" "C16"')
uu = re.search(r'\(uuid "([^"]+)"\)', t[t.rfind('\n\t(symbol\n', 0, i):i]).group(1)
c6 = b.FindFootprintByReference('C6')
c16 = pcbnew.FootprintLoad('/usr/share/kicad/footprints/Capacitor_SMD.pretty', 'C_0402_1005Metric')
c16.SetFPIDAsString('Capacitor_SMD:C_0402_1005Metric')
c16.SetReference('C16'); c16.SetValue('10n')
c16.SetPath(pcbnew.KIID_PATH('/82df408d-9aab-4d11-a747-ac2cd4d0c268/' + uu))
c16.SetSheetname(c6.GetSheetname()); c16.SetSheetfile(c6.GetSheetfile())
b.Add(c16)
c16.SetPosition(V(182.85, 152.7))
c16.Flip(V(182.85, 152.7), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
c16.SetOrientationDegrees(-90)
for p in c16.Pads():
    p.SetNet(b.FindNet('/WPT-01-TRANSMITTER-POWER/ADC_VDC' if p.GetNumber() == '1' else 'GND'))
print('C16', ' '.join('%s:%s(%.2f,%.2f)' % (p.GetNumber(), short(p.GetNetname()), p.GetPosition().x / MM, p.GetPosition().y / MM) for p in c16.Pads()))

# ---- keep-out under the slide switch
z = pcbnew.ZONE(b)
z.SetIsRuleArea(True); z.SetLayer(pcbnew.F_Cu); z.SetZoneName('SW2 metal cover: no top copper')
z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
(z.SetDoNotAllowZoneFills if hasattr(z, 'SetDoNotAllowZoneFills') else z.SetDoNotAllowCopperPour)(False)
o = z.Outline(); o.NewOutline()
for x, y in ((150.75, 147.3), (158.25, 147.3), (158.25, 162.1), (150.75, 162.1)):
    o.Append(int(x * MM), int(y * MM))
b.Add(z)
pcbnew.SaveBoard(dst, b)
del b

# ---- the old J301 footprint goes out of the file as text; the new one takes its reference
t = open(dst, encoding='utf-8').read()
i = t.index('(property "Reference" "J301"')
j = t.rfind('\n\t(footprint ', 0, i) + 1
d = 0
for k in range(j, len(t)):
    if t[k] == '(':
        d += 1
    elif t[k] == ')':
        d -= 1
        if d == 0:
            break
assert 'PinHeader_1x08' in t[j:j + 200]
t = t[:j] + t[k + 2:]
assert t.count('"J301A"') >= 1
t = t.replace('"J301A"', '"J301"')
open(dst, 'w', encoding='utf-8').write(t)
print('written', dst)

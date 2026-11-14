#!/usr/bin/env python3
"""Third revision, mechanics and the debug connector. usage: mech4.py BOARD_IN BOARD_OUT ROOT.kicad_sch

  * outline: the four corners become arcs of 5 mm radius around the mounting holes, so the distance from a hole to the
    outline is 5 mm on both edges and all round the corner
  * J3 becomes the ST debug connector STDC14 (2 x 7, 1.27 mm; Samtec FTSH-107-01-L-D-K, through-hole with keying
    shroud). It stays at the west edge where the 1 x 5 header was, long side along the edge: odd pins (pin 1, VCC 3,
    GND 5 / 7 / 11) in the west column at the board edge, even pins (SWDIO 4, SWCLK 6, NRST 12) in the east column,
    pin 1 at the north end. The key of the shroud is on the odd-pin side, so the ribbon cable leaves over the edge.
      - why through-hole: the surface-mount version needs 6.3 mm across its pads and would end 0.7 mm from pin 1 of J2;
        the through-hole one needs 2.3 mm, and a debug connector that is plugged often holds better with pins in holes
      - footprint from the project library (lib/footprints/Connector_Samtec_FTSH.pretty): the stock 2 x 07 header with
        holes of 0.70 mm instead of 0.65 mm (0.40 mm square posts measure 0.57 mm across the corners, and a plated hole
        may come out 0.08 mm small) and pads of 1.05 mm
      - the cable socket (Samtec FFSD-07, 13.1 mm long, 3.05 mm wide) ends 3.8 mm from the centre of the mounting hole
        and 1 mm from the cover of the slide switch
  * SWCLK / SWDIO: the old run came within 3.1 mm of the centre of the mounting hole, i.e. under a 7 mm washer. The new
    one leaves the top strip on a diagonal that stays 4.2 mm away, then goes straight down beside the connector and
    into the pins (no via). NRST keeps its run between the header rows and comes in from the north-east.
  * the supply pins need no tracks: they are through-hole pads in the ground and 3.3 V planes
  * silkscreen: the labels of the old header go
"""
import math
import re
import shutil
import sys

import pcbnew

from nego import rip_text

MM = 1e6
src, dst, root_sch = sys.argv[1:4]
shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)
V = lambda x, y: pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
P = lambda v: (round(v.x / MM, 4), round(v.y / MM, 4))
short = lambda n: n.split('/')[-1]
S2 = math.sqrt(2)

# ---------------------------------------------------------------- outline
R = 5.0
x0, y0, x1, y1 = 150.0, 125.0, 220.0, 205.0
edges = [d for d in b.GetDrawings() if d.GetClass() == 'PCB_SHAPE' and d.GetLayer() == pcbnew.Edge_Cuts]
assert len(edges) == 4, len(edges)
w = edges[0].GetWidth()
for d in edges:
    a, e = P(d.GetStart()), P(d.GetEnd())
    if abs(a[0] - e[0]) < 1e-3:                       # vertical edge: shorten in y
        ya, ye = sorted((a[1], e[1]))
        d.SetStart(V(a[0], ya + R)); d.SetEnd(V(a[0], ye - R))
    else:
        xa, xe = sorted((a[0], e[0]))
        d.SetStart(V(xa + R, a[1])); d.SetEnd(V(xe - R, a[1]))
k = R / S2
for cx, cy, sx, sy in ((x0 + R, y0 + R, -1, -1), (x1 - R, y0 + R, 1, -1), (x1 - R, y1 - R, 1, 1), (x0 + R, y1 - R, -1, 1)):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(w)
    s.SetArcGeometry(V(cx + sx * R, cy), V(cx + sx * k, cy + sy * k), V(cx, cy + sy * R))
    b.Add(s)

# ---------------------------------------------------------------- copper that goes: (net, test on a segment)
kill = set()
ends = {}
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T or b.GetLayerName(t.GetLayer()) != 'F.Cu':
        continue
    n = short(t.GetNetname())
    a, e = P(t.GetStart()), P(t.GetEnd())
    key = ('T', t.GetNetname(), 'F.Cu') + tuple(sorted([(round(a[0], 3), round(a[1], 3)), (round(e[0], 3), round(e[1], 3))]))
    if n in ('SWCLK', 'SWDIO') and min(a[0], e[0]) < 184.0:
        kill.add(key)
        if abs(a[1] - e[1]) < 1e-3 and abs(a[0] - e[0]) > 20:          # the long row along the strip: its east end stays
            ends[n] = max(a, e)
    if n == 'NRST' and max(a[0], e[0]) < 175.0:
        kill.add(key)
assert set(ends) == {'SWCLK', 'SWDIO'}, ends
print('row ends', ends)

# ---------------------------------------------------------------- the new connector
t = open(root_sch, encoding='utf-8').read()
i = t.index('(property "Reference" "J3"')
uu = re.search(r'\(uuid "([^"]+)"\)', t[t.rfind('\n\t(symbol\n', 0, i):i]).group(1)
old = b.FindFootprintByReference('J3')
j4 = b.FindFootprintByReference('J4')
import os
FPLIB = os.path.join(os.path.dirname(os.path.abspath(root_sch)), 'lib', 'footprints', 'Connector_Samtec_FTSH.pretty')
new = pcbnew.FootprintLoad(FPLIB, 'FTSH-107-01-L-D-K_2x07_P1.27mm_Vertical')      # stock 2x07 header with 0.70 mm holes, 1.05 mm pads
new.SetFPIDAsString('Connector_Samtec_FTSH:FTSH-107-01-L-D-K_2x07_P1.27mm_Vertical')
new.SetReference('J3A')                                   # takes the reference J3 once the old footprint is out of the file
new.SetValue('STDC14')
new.SetPath(pcbnew.KIID_PATH('/' + uu))
new.SetSheetname(j4.GetSheetname()); new.SetSheetfile(j4.GetSheetfile())
b.Add(new)
X1, Y1 = 152.40, 136.49                                   # pin 1; the footprint's origin
new.SetPosition(V(X1, Y1))
new.SetOrientationDegrees(0)
NETS = {'1': 'unconnected-(J3-NC-Pad1)', '2': 'unconnected-(J3-NC-Pad2)', '3': '+3V3', '4': '/MCU/SWDIO', '5': 'GND',
        '6': '/MCU/SWCLK', '7': 'GND', '8': 'unconnected-(J3-JTDO{slash}SWO-Pad8)', '9': 'unconnected-(J3-JRCLK{slash}NC-Pad9)',
        '10': 'unconnected-(J3-JTDI{slash}NC-Pad10)', '11': 'GND', '12': '/MCU/NRST', '13': 'unconnected-(J3-VCP_RX-Pad13)',
        '14': 'unconnected-(J3-VCP_TX-Pad14)'}
pad = {}
for p in new.Pads():
    k_ = p.GetNumber()
    pad[k_] = P(p.GetPosition())
    n_ = b.FindNet(NETS[k_])
    if n_ is None:
        n_ = pcbnew.NETINFO_ITEM(b, NETS[k_])
        b.Add(n_)
    p.SetNet(n_)
print('J3 pads:', ' '.join('%s(%.2f,%.2f)' % (k_, *pad[k_]) for k_ in sorted(pad, key=int)))
assert abs(pad['4'][0] - 153.67) < 0.01 and abs(pad['4'][1] - 137.76) < 0.01, pad['4']    # odd pins west, pin 1 north
assert abs(pad['13'][0] - 152.40) < 0.01 and abs(pad['13'][1] - 144.11) < 0.01, pad['13']


def seg(net, pts, w_=0.2, layer='F.Cu'):
    n = b.FindNet(net)
    assert n is not None, net
    for p, q in zip(pts, pts[1:]):
        dx, dy = abs(q[0] - p[0]), abs(q[1] - p[1])
        assert dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-4, ('not on 45 degrees', net, p, q)
        s = pcbnew.PCB_TRACK(b)
        s.SetNet(n); s.SetLayer(b.GetLayerID(layer)); s.SetStart(V(*p)); s.SetEnd(V(*q)); s.SetWidth(int(round(w_ * MM)))
        b.Add(s)


def via(net, c):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(V(*c)); v.SetWidth(int(0.6 * MM)); v.SetDrill(int(0.3 * MM)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(b.FindNet(net))
    b.Add(v)


# The two rows of the top strip (SWDIO north, SWCLK 0.4 mm south of it) turn south-west on parallel diagonals. A washer
# of 7 mm on the M3 hole at (155, 130) reaches 3.5 mm from its centre; the SWDIO diagonal x + y = 291.0 stays 4.24 mm away.
# Then two columns east of the connector (SWDIO inside, because it ends first), each with a short piece into its pin.
r_ = lambda v: round(v, 4)
HOLE = (155.0, 130.0)
ck, io = ends['SWCLK'], ends['SWDIO']
X_IO, X_CK = 155.20, 155.60
S_IO = 291.0
S_CK = S_IO + 0.4 * S2
assert (S_IO - HOLE[0] - HOLE[1]) / S2 > 4.1
seg('/MCU/SWDIO', [io, (r_(S_IO - io[1]), io[1]), (X_IO, r_(S_IO - X_IO)), (X_IO, r_(pad['4'][1] - 0.3)), (X_IO - 0.3, pad['4'][1]), pad['4']])
seg('/MCU/SWCLK', [ck, (r_(S_CK - ck[1]), ck[1]), (X_CK, r_(S_CK - X_CK)), (X_CK, r_(pad['6'][1] - 0.3)), (X_CK - 0.3, pad['6'][1]), pad['6']])
# NRST: along its row between the headers, a step down north of pin 1 of J2, then a diagonal that ends at pin 12
YS = 139.75
xe = r_(pad['12'][0] + 0.54)                              # where the diagonal meets the height of pin 12
xs = r_(xe + (pad['12'][1] - YS))
seg('/MCU/NRST', [(174.95, 138.45), (r_(xs + 1.6 + (YS - 138.45)), 138.45), (xs + 1.6, YS), (xs, YS), (xe, pad['12'][1]), pad['12']])

# ---------------------------------------------------------------- silkscreen texts
drop_txt = {'RST', 'CLK', 'DIO', '3V3', 'GND'}
gone = []
for d in b.GetDrawings():
    if d.GetClass() == 'PCB_TEXT' and d.GetLayer() == pcbnew.F_SilkS:
        x, y = d.GetPosition().x / MM, d.GetPosition().y / MM
        if d.GetText() in drop_txt and abs(x - 154.6) < 0.01 and 134 < y < 147:
            gone.append(d.m_Uuid.AsString())
print('texts to drop:', len(gone))
for txt, x, y, just in (('STDC14', 154.30, 134.75, pcbnew.GR_TEXT_H_ALIGN_LEFT),):
    tx = pcbnew.PCB_TEXT(b)
    tx.SetText(txt); tx.SetLayer(pcbnew.F_SilkS)
    tx.SetTextSize(pcbnew.VECTOR2I(int(0.8 * MM), int(0.8 * MM))); tx.SetTextThickness(int(0.15 * MM))
    tx.SetHorizJustify(just); tx.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    tx.SetPosition(V(x, y))
    b.Add(tx)
pcbnew.SaveBoard(dst, b)
del b
print('removed', rip_text(dst, kill), 'of', len(kill), 'track pieces')

# ---------------------------------------------------------------- old footprint and old texts out of the file
t = open(dst, encoding='utf-8').read()


def cut(t, j):
    d = 0
    for k in range(j, len(t)):
        if t[k] == '(':
            d += 1
        elif t[k] == ')':
            d -= 1
            if d == 0:
                break
    return t[:j] + t[k + 2:]


i = t.index('(property "Reference" "J3"')
j = t.rfind('\n\t(footprint ', 0, i) + 1
assert 'PinHeader_1x05' in t[j:j + 200]
t = cut(t, j)
for u in gone:
    i = t.index('(uuid "%s")' % u)
    t = cut(t, t.rfind('\n\t(gr_text', 0, i) + 1)
assert t.count('"J3A"') >= 1
t = t.replace('"J3A"', '"J3"')
open(dst, 'w', encoding='utf-8').write(t)
print('written', dst)

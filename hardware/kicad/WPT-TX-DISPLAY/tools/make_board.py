#!/usr/bin/env python3
"""Board of the display board from the netlist. usage (inside hardware/kicad/WPT-TX-DISPLAY): make_board.py NETLIST OUT.kicad_pcb

Write OUT into a scratch directory and copy the .kicad_pcb into the project: pcbnew writes a project file next to
the board it saves, and that would replace the rules of this project by the defaults.

The coordinates are those of the transmitter board (WPT-01-TRANSMITTER.kicad_pcb): the display board lies
11 mm above it, so a point (x, y) here is over the same point there. That keeps every check against the
transmitter board (what it covers, what it must leave free) a comparison of numbers.

Shape (see docs/stm32-tx/display_shield_study.md):
  strip   over J2 (pins at y = 141.50, x = 158.30 ... 186.24), 4.6 mm wide. It leaves the three analog test pads
          north of it free (their pads end at y = 137.8).
  block   east of the test pads, over the USB connector: the display, upright (13.5 x 27.95 mm). Its south edge
          lies 1.6 mm beyond the module: a module of the other make sits 0.58 mm further south and its fold stands
          up to 1 mm beyond it (tools/make_footprint.py).
  arm     to the north-east mounting hole (215, 130) of the transmitter board, where an 11 mm spacer carries the board.

Two copper layers. F.Cu is the display side, B.Cu faces the transmitter board and carries J1 and the small parts.
Signals leave J1 northwards and run east along the strip, four rows per layer; a row further north belongs to a pin
further west, so nothing crosses. SCK, DC, RST (front) go round the north end of the lands and enter them from there;
MOSI, CS (back) pass under the lands and come up at their south end; that order needs no crossing either.
The northernmost row of the back is ground, from pin 1 to the ground of the block: it lies under SCK, so the clock
has its return 1.6 mm below it instead of in the transmitter board 11 mm below (the comparators of the ZVS
detection are right under the strip).
"""
import math
import os
import sys

import pcbnew

netlist_path, out_path = sys.argv[1:3]
MM = 1e6
V = lambda x, y: pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
P = lambda v: (round(v.x / MM, 4), round(v.y / MM, 4))
STOCK = '/usr/share/kicad/footprints'
LAYER = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu, 'F.SilkS': pcbnew.F_SilkS, 'B.SilkS': pcbnew.B_SilkS}
LOCAL = 'lib/footprints'


# ------------------------------------------------------------------ netlist (kicad s-expression) -> components
def parse(s):
    """minimal s-expression reader: nested lists of strings"""
    out, stack, i, n = None, [], 0, len(s)
    while i < n:
        c = s[i]
        if c == '(':
            stack.append([])
            i += 1
        elif c == ')':
            top = stack.pop()
            if stack:
                stack[-1].append(top)
            else:
                out = top
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while s[j] != '"':
                if s[j] == '\\':
                    j += 1
                buf.append(s[j])
                j += 1
            stack[-1].append(''.join(buf))
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in '()':
                j += 1
            stack[-1].append(s[i:j])
            i = j
    return out


def kids(n, name):
    return [x for x in n if isinstance(x, list) and x and x[0] == name]


def val(n, name, default=''):
    k = kids(n, name)
    return k[0][1] if k and len(k[0]) > 1 else default


root = parse(open(netlist_path, encoding='utf-8').read())
comps = {}
for c in kids(kids(root, 'components')[0], 'comp'):
    props = {val(p, 'name'): val(p, 'value') for p in kids(c, 'property')}
    fields = {val(f, 'name'): (f[2] if len(f) > 2 else '') for f in (kids(kids(c, 'fields')[0], 'field') if kids(c, 'fields') else [])}
    comps[val(c, 'ref')] = {'value': val(c, 'value'), 'footprint': val(c, 'footprint'), 'path': val(kids(c, 'sheetpath')[0], 'tstamps') + kids(c, 'tstamps')[0][1],
                            'sheetname': props.get('Sheetname', ''), 'sheetfile': props.get('Sheetfile', ''),
                            'description': val(c, 'description') or val(kids(c, 'libsource')[0], 'description'), 'datasheet': val(c, 'datasheet'),
                            'fields': fields, 'pins': {}}
for nn in kids(kids(root, 'nets')[0], 'net'):
    for node in kids(nn, 'node'):
        comps[val(node, 'ref')]['pins'][val(node, 'pin')] = val(nn, 'name')

# ------------------------------------------------------------------ board
b = pcbnew.BOARD()
b.SetCopperLayerCount(2)
ds = b.GetDesignSettings()
ds.SetBoardThickness(int(1.6 * MM))
ds.m_TrackMinWidth = int(0.2 * MM)
ds.m_MinClearance = int(0.2 * MM)
ds.m_ViasMinSize = int(0.6 * MM)
ds.m_MinThroughDrill = int(0.3 * MM)
ds.m_CopperEdgeClearance = int(0.3 * MM)


def net(name):
    n = b.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(b, name)
        b.Add(n)
    return n


def pads(fp):
    return {p.GetNumber(): P(p.GetPosition()) for p in fp.Pads()}


def place(ref, x, y, side, want, ref_pos=None, ref_rot=0.0):
    """footprint of the schematic symbol `ref`, turned until its pads are where `want` says"""
    c = comps[ref]
    nick, name = c['footprint'].split(':')
    lib = os.path.join(LOCAL, nick + '.pretty') if os.path.isdir(os.path.join(LOCAL, nick + '.pretty')) else os.path.join(STOCK, nick + '.pretty')
    fp = pcbnew.FootprintLoad(lib, name)
    assert fp is not None, c['footprint']
    fp.SetFPIDAsString(c['footprint'])
    fp.SetReference(ref)
    fp.SetValue(c['value'])
    fp.SetPath(pcbnew.KIID_PATH(c['path']))
    fp.SetSheetname(c['sheetname'])
    fp.SetSheetfile(c['sheetfile'])
    b.Add(fp)
    fp.SetPosition(V(x, y))
    if side == 'B':
        fp.Flip(V(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    for r in (0, 90, 180, 270):
        fp.SetOrientationDegrees(r)
        got = pads(fp)
        if all(abs(got[k][0] - v[0]) < 0.006 and abs(got[k][1] - v[1]) < 0.006 for k, v in want.items()):
            break
    else:
        raise AssertionError((ref, got, want))
    if c['description']:
        fp.SetField('Description', c['description'])
        fp.GetField('Description').SetVisible(False)
    if c['datasheet'] not in ('', '~'):
        fp.GetField('Datasheet').SetText(c['datasheet'])
    for k, v in c['fields'].items():                      # the fields the parity check compares (manufacturer, part number, notes)
        if k in ('Footprint', 'Datasheet', 'Description'):
            continue
        fp.SetField(k, v)
        fp.GetField(k).SetVisible(False)
    for pad in fp.Pads():
        nm = c['pins'].get(pad.GetNumber())
        if nm is not None:
            pad.SetNet(net(nm))
    t = fp.Reference()
    t.SetTextSize(pcbnew.VECTOR2I(int(0.8 * MM), int(0.8 * MM)))
    t.SetTextThickness(int(0.15 * MM))
    if ref_pos is None:
        t.SetVisible(False)
    else:
        t.SetPosition(V(*ref_pos))
        t.SetTextAngleDegrees(ref_rot)
    fp.Value().SetVisible(False)
    return fp


def seg(netname, pts, layer='F.Cu', w=0.2):
    n = b.FindNet(netname)
    assert n is not None, netname
    for p, q in zip(pts, pts[1:]):
        dx, dy = abs(q[0] - p[0]), abs(q[1] - p[1])
        assert dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-3, ('not on 45 degrees', netname, p, q)
        s = pcbnew.PCB_TRACK(b)
        s.SetNet(n)
        s.SetLayer(LAYER[layer])
        s.SetStart(V(*p))
        s.SetEnd(V(*q))
        s.SetWidth(int(round(w * MM)))
        b.Add(s)


def via(netname, c):
    n = b.FindNet(netname)
    assert n is not None, netname
    v = pcbnew.PCB_VIA(b)
    v.SetNet(n)
    v.SetPosition(V(*c))
    v.SetWidth(pcbnew.F_Cu, int(0.6 * MM))
    v.SetDrill(int(0.3 * MM))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    b.Add(v)


def text(s, x, y, layer='F.SilkS', size=0.8, rot=0.0, justify='center'):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s)
    t.SetLayer(LAYER[layer])
    t.SetTextSize(pcbnew.VECTOR2I(int(size * MM), int(size * MM)))
    t.SetTextThickness(int(0.15 * MM))
    t.SetHorizJustify({'left': pcbnew.GR_TEXT_H_ALIGN_LEFT, 'center': pcbnew.GR_TEXT_H_ALIGN_CENTER, 'right': pcbnew.GR_TEXT_H_ALIGN_RIGHT}[justify])
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    t.SetPosition(V(x, y))
    if rot:
        t.SetTextAngleDegrees(rot)
    if layer.startswith('B.'):
        t.SetMirrored(True)
    b.Add(t)


# ------------------------------------------------------------------ geometry taken from the transmitter board and the parts
J2_X0, J2_Y, PITCH = 158.30, 141.50, 2.54                 # J2 of the transmitter board
HOLE = (215.0, 130.0)                                     # its north-east mounting hole
STRIP_N, STRIP_S, STRIP_W = 138.4, 143.0, 156.3
BLK_W, BLK_E, BLK_N, BLK_S = 189.9, 204.5, 125.3, 155.1
ARM_S, ARM_R = 134.2, 4.7
DS = (197.2, 139.525)                                     # centre of the display module (13.5 x 27.95), tail folded at the south end
LAND_Y0, LAND_Y1 = DS[1] - 0.825, DS[1] + 3.175           # the 13 lands
land = lambda k: round(DS[0] + 4.2 - 0.7 * (k - 1), 3)    # x of land k (1 = east)
pin = lambda k: round(J2_X0 + PITCH * (k - 1), 3)

# ------------------------------------------------------------------ outline with rounded corners
OUT = [(STRIP_W, STRIP_N, 1.0), (BLK_W, STRIP_N, 1.0), (BLK_W, BLK_N, 1.0), (HOLE[0], BLK_N, 0), ('arc', HOLE, ARM_R), (HOLE[0] + ARM_R, HOLE[1], 0),
       (HOLE[0] + ARM_R, ARM_S, 1.5), (BLK_E, ARM_S, 1.0), (BLK_E, BLK_S, 1.0), (BLK_W, BLK_S, 1.0), (BLK_W, STRIP_S, 1.0), (STRIP_W, STRIP_S, 1.0)]


def edge_line(a, e):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(V(*a))
    s.SetEnd(V(*e))
    s.SetWidth(int(0.05 * MM))
    b.Add(s)


def edge_arc(a, m, e):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetArcGeometry(V(*a), V(*m), V(*e))
    s.SetWidth(int(0.05 * MM))
    b.Add(s)


def build_outline(spec):
    """corner points with fillet radius; ('arc', centre, r) joins its neighbours with a quarter circle round the centre"""
    n = len(spec)
    segs = []                                             # per vertex: (entry point, exit point, mid point or None)
    for i, v in enumerate(spec):
        if v[0] == 'arc':
            (cx, cy), r = v[1], v[2]
            a, e = spec[i - 1][:2], spec[(i + 1) % n][:2]
            a0, a1 = math.atan2(a[1] - cy, a[0] - cx), math.atan2(e[1] - cy, e[0] - cx)
            if a1 - a0 > math.pi:
                a1 -= 2 * math.pi
            if a0 - a1 > math.pi:
                a1 += 2 * math.pi
            am = (a0 + a1) / 2
            segs.append((a, e, (cx + r * math.cos(am), cy + r * math.sin(am))))
            continue
        x, y, r = v
        if r == 0:
            segs.append(((x, y), (x, y), None))
            continue
        pv, nx = spec[i - 1], spec[(i + 1) % n]
        pv = pv[1] if pv[0] == 'arc' else pv[:2]
        nx = nx[1] if nx[0] == 'arc' else nx[:2]
        d1 = (pv[0] - x, pv[1] - y)
        d2 = (nx[0] - x, nx[1] - y)
        l1, l2 = math.hypot(*d1), math.hypot(*d2)
        u1, u2 = (d1[0] / l1, d1[1] / l1), (d2[0] / l2, d2[1] / l2)
        a, e = (x + u1[0] * r, y + u1[1] * r), (x + u2[0] * r, y + u2[1] * r)
        c = (x + (u1[0] + u2[0]) * r, y + (u1[1] + u2[1]) * r)             # right angle: the centre is the corner of the square
        k = r / math.hypot(x - c[0], y - c[1])
        segs.append((a, e, (c[0] + (x - c[0]) * k, c[1] + (y - c[1]) * k)))
    for i, (a, e, m) in enumerate(segs):
        if m is not None:
            edge_arc(a, m, e)
        nxt = segs[(i + 1) % n]
        if spec[i][0] == 'arc' or spec[(i + 1) % n][0] == 'arc':
            continue                                      # the arc itself joins these two
        if math.hypot(nxt[0][0] - e[0], nxt[0][1] - e[1]) > 1e-6:
            edge_line(e, nxt[0])


build_outline(OUT)

# ------------------------------------------------------------------ parts
# The small parts are on the back, under the tail of the display. Their positions follow from the lands:
#   land 12 (LEDA) - via - R1 straight below it;  land 10 (VDD) - via - C1 straight below it;  C2 beside C1;
#   land 11 (LEDK) - via - Q1 drain along one diagonal;  R2 below the gate of Q1.
S1, S2 = 143.4, 144.3                                     # the two rows of vias south of the lands
RAIL = 145.81                                             # +3V3 along the lower pad of R1 and the upper pads of C1, C2
QX, QY = 192.5625, 148.6                                  # Q1: gate and source on x = 191.625, drain at (193.5, 148.6)
GX = QX - 0.9375
J1 = place('J1', pin(1), J2_Y, 'B', {'1': (pin(1), J2_Y), '12': (pin(12), J2_Y)}, ref_pos=(pin(1) - 0.2, 139.35))
DS1 = place('DS1', DS[0], DS[1], 'F', {'1': (land(1), DS[1] + 1.175), '13': (land(13), DS[1] + 1.175)})
H1 = place('H1', HOLE[0], HOLE[1], 'F', {'1': HOLE})
R1 = place('R1', land(12), RAIL - 0.51, 'B', {'2': (land(12), RAIL - 1.02), '1': (land(12), RAIL)}, ref_pos=(192.3, 145.0))
C1 = place('C1', land(10), RAIL + 0.48, 'B', {'1': (land(10), RAIL), '2': (land(10), RAIL + 0.96)}, ref_pos=(195.3, 149.0))
C2 = place('C2', 196.3, RAIL + 0.48, 'B', {'1': (196.3, RAIL), '2': (196.3, RAIL + 0.96)}, ref_pos=(197.75, RAIL + 0.48))
Q1 = place('Q1', QX, QY, 'B', {'1': (GX, QY + 0.95), '2': (GX, QY - 0.95), '3': (QX + 0.9375, QY)}, ref_pos=(193.6, 150.85))
R2 = place('R2', GX, QY + 2.8, 'B', {'1': (GX, QY + 2.29), '2': (GX, QY + 3.31)}, ref_pos=(193.3, 152.5))
t = DS1.Reference()                                       # under the module: seen while the board is assembled
t.SetVisible(True)
t.SetPosition(V(DS[0], 134.0))
# The ground pins of J1 are joined by tracks, not by the zone: on the narrow strip the zone would only reach them as
# an island of its own. (The lands of DS1 carry "no zone connection" in the footprint. The pad of the screw hole
# has no net: see gen_sch.py.)
for pad in J1.Pads():
    if pad.GetNumber() in ('1', '12'):
        pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_NONE)

N3, GND = '+3V3', 'GND'
SCK, MOSI, CS, DC, RST, BL = '/SCK', '/MOSI', '/~{CS}', '/DC', '/~{RST}', '/BL_PWM'
LEDA, LEDK = 'Net-(DS1-LEDA)', 'Net-(DS1-LEDK)'
for nm in (N3, GND, SCK, MOSI, CS, DC, RST, BL, LEDA, LEDK):
    assert b.FindNet(nm) is not None, nm

# ------------------------------------------------------------------ the strip: four rows north of the pins on each layer
# front: 0.5 mm apart. back: 0.4 mm apart, because the via of the supply (192.0, 140.3) needs the room south of row C.
ROWF = {'A': 138.8, 'B': 139.3, 'C': 139.8, 'D': 140.3}
ROWB = {'A': 138.8, 'B': 139.2, 'C': 139.6, 'D': 140.0}


def leave(k, y):
    """from pin k straight north, a 45-degree corner, then east along the row at y"""
    return [(pin(k), J2_Y), (pin(k), y + 0.4), (pin(k) + 0.4, y)]


# front: SCK (pin 3), DC (8), RST (9) turn north-east together where the block begins (each one 0.2 mm further east
# than the row north of it: the diagonals stay 0.3 mm apart), run east north of the lands and enter them from there.
seg(SCK, leave(3, ROWF['A']) + [(190.3, 138.8), (191.9, 137.2), (198.2, 137.2), (199.3, 138.3), (199.3, LAND_Y0 + 0.5)])
seg(DC, leave(8, ROWF['B']) + [(190.5, 139.3), (192.1, 137.7), (198.0, 137.7), (198.6, 138.3), (198.6, LAND_Y0 + 0.5)])
seg(RST, leave(9, ROWF['C']) + [(190.7, 139.8), (192.3, 138.2), (197.5, 138.2), (197.9, 138.6), (197.9, LAND_Y0 + 0.5)])
assert (land(4), land(5), land(6)) == (199.3, 198.6, 197.9)
# +3V3 (pin 11): straight east into a via, on the back along one diagonal to the via of the VDD land
VE = (land(10) - (S1 - ROWF['D']), ROWF['D'])
seg(N3, leave(11, ROWF['D']) + [VE])
via(N3, VE)
# ground of pin 12 on the front: to the via of land 13
G13 = (192.4, 143.9)
seg(GND, [(pin(12), J2_Y), (G13[0] - (G13[1] - J2_Y), J2_Y), G13], 'F.Cu', 0.4)
# back: ground (pin 1), MOSI (5), CS (7), backlight switch (10)
seg(GND, leave(1, ROWB['A']) + [(190.0, 138.8), (191.0, 137.8), (191.0, 136.6)], 'B.Cu')
via(GND, (191.0, 136.6))
seg(MOSI, leave(5, ROWB['B']) + [(land(3) - (S1 - ROWB['B']), ROWB['B']), (land(3), S1)], 'B.Cu')
seg(CS, leave(7, ROWB['C']) + [(land(7) - (S1 - ROWB['C']), ROWB['C']), (land(7), S1)], 'B.Cu')
seg(BL, leave(10, ROWB['D']) + [(190.0, 140.0), (190.4, 140.4), (190.4, QY + 0.55), (190.8, QY + 0.95), (GX, QY + 0.95)], 'B.Cu')
seg(BL, [(GX, QY + 0.95), (GX, QY + 2.29)], 'B.Cu')

# ------------------------------------------------------------------ south end of the lands: stubs on the front, vias in two rows
for k, nm in ((12, LEDA), (10, N3), (7, CS), (3, MOSI)):
    seg(nm, [(land(k), LAND_Y1 - 0.5), (land(k), S1)])
    via(nm, (land(k), S1))
seg(GND, [(land(8), LAND_Y1 - 0.5), (land(8), S2)])
via(GND, (land(8), S2))
seg(GND, [(land(13), LAND_Y1 - 0.5), (land(13), G13[1] - (land(13) - G13[0])), G13])
via(GND, G13)
LK = (land(11), QY - 0.9)                                 # via of the cathode: one diagonal from here to the drain of Q1
seg(LEDK, [(land(11), LAND_Y1 - 0.5), LK])
via(LEDK, LK)
seg(LEDK, [LK, (QX + 0.9375, QY)], 'B.Cu')

# supply on the back
seg(N3, [VE, (land(10), S1), (land(10), RAIL)], 'B.Cu', 0.3)
seg(N3, [(land(12), RAIL), (196.3, RAIL)], 'B.Cu', 0.3)
# the anode of the backlight LED through R1
seg(LEDA, [(land(12), S1), (land(12), RAIL - 1.02)], 'B.Cu')
# ground: capacitors, the source of Q1, R2
seg(GND, [(land(10), RAIL + 0.96), (196.3, RAIL + 0.96)], 'B.Cu', 0.3)
seg(GND, [(195.7, RAIL + 0.96), (195.7, 147.8)], 'B.Cu', 0.3)
via(GND, (195.7, 147.8))
seg(GND, [(GX, QY - 0.95), (GX, QY - 2.0)], 'B.Cu', 0.3)
via(GND, (GX, QY - 2.0))
seg(GND, [(GX, QY + 3.31), (GX, QY + 4.3)], 'B.Cu', 0.3)
via(GND, (GX, QY + 4.3))
for c in ((192.0, 127.6), (202.4, 127.6), (197.2, 132.0), (202.9, 150.6), (198.5, 151.6), (208.0, 133.2), (203.4, 139.0)):
    via(GND, c)

# ------------------------------------------------------------------ ground on both layers
poly = [(STRIP_W, STRIP_N), (BLK_W, STRIP_N), (BLK_W, BLK_N), (HOLE[0] + ARM_R, BLK_N), (HOLE[0] + ARM_R, ARM_S), (BLK_E, ARM_S), (BLK_E, BLK_S),
        (BLK_W, BLK_S), (BLK_W, STRIP_S), (STRIP_W, STRIP_S)]
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(net(GND))
    z.SetZoneName('GND')
    z.SetLocalClearance(int(0.25 * MM))
    z.SetMinThickness(int(0.2 * MM))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(int(0.25 * MM))
    z.SetThermalReliefSpokeWidth(int(0.4 * MM))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    for x, y in poly:
        o.Append(int(x * MM), int(y * MM))
    b.Add(z)

# ------------------------------------------------------------------ silkscreen
text('WPT-TX', 208.1, 127.4)
text('DISPLAY', 208.1, 128.9)
text('v0.1', 208.1, 130.4)
text('2026-11', 208.1, 131.9)
text('1', 156.95, 139.4)
text('12', 188.4, 139.4)
text('to J2', 172.3, 139.4, 'B.SilkS')

tb = b.GetTitleBlock()
tb.SetTitle('WPT transmitter: display board (provisional)')
tb.SetRevision('0.1')
tb.SetDate('2026-11-17')
tb.SetComment(0, 'Plugs onto J2 of WPT-01-TRANSMITTER, 11 mm above it. Coordinates are those of that board.')

pcbnew.SaveBoard(out_path, b)
print('saved', out_path)

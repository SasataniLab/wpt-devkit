#!/usr/bin/env python3
"""Board of the display board from the netlist. usage (inside hardware/kicad/WPT-TX-DISPLAY): make_board.py NETLIST OUT.kicad_pcb

Write OUT into a scratch directory and copy the .kicad_pcb into the project: pcbnew writes a project file next to
the board it saves, and that would replace the rules of this project by the defaults.

The coordinates are those of the transmitter board (WPT-01-TRANSMITTER.kicad_pcb): the display board lies
9.9 mm above it, so a point (x, y) here is over the same point there. That keeps every check against the
transmitter board (what it covers, what it must leave free) a comparison of numbers.

Shape (see docs/stm32-tx/display_shield_study.md): a plain rectangle of 30.4 x 14.8 mm, as large as the display
module (13.5 x 27.95 mm, lying, tail folded at the east end) with the room its other makes need. The socket J1 sits
on the back in the middle, over J2 of the transmitter board (2 x 6, odd pins y = 136.42, even pins y = 133.88,
columns x = 171.00 + 2.54 k). It is a surface-mount part, so nothing of it shows on the display side and the module
can lie right over it. No screw: two rows of pins in the middle of a board of this size hold it.

Two copper layers. F.Cu is the display side with the 13 lands of the tail in the middle; B.Cu faces the transmitter
board and carries J1 and the small parts (east of J1).
  MOSI, SCK, RST   leave their lands to the west, go south round the lands and change sides below the inner row
                   of J1, each under its pad.
  DC, CS           leave their lands to the east (under the tail), go north round the lands and change sides above
                   the outer row of J1, each over its pad.
  supply, LED      leave to the east; C1, C2, R1 hang on pin 11, Q1 and R2 on pin 10.
No track crosses another on its layer.
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
TITLE_ROT = 270.0                                            # seen from the back: read from the bottom, as on the transmitter board


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


def text(s, x, y, layer='F.SilkS', size=0.8, rot=0.0, justify='center', knockout=False):
    """(x, y): centre of the text, also for several lines (the lines themselves are aligned by `justify`)."""
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
    t.SetIsKnockout(knockout)
    if '\n' in s or justify != 'center':                      # the anchor is not the centre then: shift by what the box says
        c = t.GetBoundingBox().Centre()
        t.Move(pcbnew.VECTOR2I(int(round(x * MM)) - c.x, int(round(y * MM)) - c.y))
    b.Add(t)
    return t


# ------------------------------------------------------------------ geometry taken from the transmitter board and the parts
J2_X0, J2_YI, J2_YO, PITCH = 171.00, 136.42, 133.88, 2.54     # J2 of the transmitter board: pin 1, inner row (odd pins), outer row (even pins)
JC = (J2_X0 + 2.5 * PITCH, (J2_YI + J2_YO) / 2)              # centre of J2 = centre of the socket = centre of the board
PAD_I, PAD_O = JC[1] + 2.52, JC[1] - 2.52                    # the two rows of lands of the socket (odd / even pins)
DS = (JC[0] - 0.70, JC[1])                                   # centre of the display module; its courtyard reaches 0.7 mm further east than west
W, E, N, S = DS[0] - 14.5, DS[0] + 15.9, DS[1] - 7.4, DS[1] + 7.4
LAND_X0, LAND_X1 = DS[0] - 0.825, DS[0] + 3.175              # the 13 lands, each 4 mm long; the tail covers them from x = DS + 0.675 eastwards
land = lambda k: round(DS[1] - 4.2 + 0.7 * (k - 1), 3)       # y of land k (1 = north)
col = lambda n: round(J2_X0 + PITCH * ((n - 1) // 2), 3)     # x of pin n of J2

# ------------------------------------------------------------------ outline with rounded corners
OUT = [(W, N, 1.0), (E, N, 1.0), (E, S, 1.0), (W, S, 1.0)]


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
J1 = place('J1', JC[0], JC[1], 'B', {'1': (col(1), PAD_I), '2': (col(2), PAD_O), '3': (col(3), PAD_I), '12': (col(12), PAD_O)}, ref_pos=(JC[0], 129.2))
DS1 = place('DS1', DS[0], DS[1], 'F', {'1': (DS[0] + 1.175, land(1)), '13': (DS[0] + 1.175, land(13))})
RAIL = PAD_I                                              # +3V3 leaves pad 11 eastwards along its own row
C1 = place('C1', 186.3, RAIL - 0.48, 'B', {'1': (186.3, RAIL), '2': (186.3, RAIL - 0.96)}, ref_pos=(186.0, 139.0))
C2 = place('C2', 187.35, RAIL - 0.48, 'B', {'1': (187.35, RAIL), '2': (187.35, RAIL - 0.96)}, ref_pos=(187.7, 139.0))
R1 = place('R1', 188.95, RAIL, 'B', {'1': (188.44, RAIL), '2': (189.46, RAIL)}, ref_pos=(191.3, RAIL))
QX, QY = 189.46, 133.0                                    # Q1: source (north) and gate (south) on x = 188.52, drain at (190.40, 133.0)
GX, DX = QX - 0.9375, QX + 0.9375
Q1 = place('Q1', QX, QY, 'B', {'1': (GX, QY + 0.95), '2': (GX, QY - 0.95), '3': (DX, QY)}, ref_pos=(191.4, 134.9))
R2 = place('R2', GX, QY + 2.75, 'B', {'1': (GX, QY + 2.24), '2': (GX, QY + 3.26)}, ref_pos=(186.9, 134.9))
t = DS1.Reference()                                       # under the module: seen while the board is assembled
t.SetVisible(True)
t.SetPosition(V(168.5, DS[1]))
t.SetTextAngleDegrees(90)

N3, GND = '+3V3', 'GND'
SCK, MOSI, CS, DC, RST, BL = '/SCK', '/MOSI', '/~{CS}', '/DC', '/~{RST}', '/BL_PWM'
LEDA, LEDK = 'Net-(DS1-LEDA)', 'Net-(DS1-LEDK)'
for nm in (N3, GND, SCK, MOSI, CS, DC, RST, BL, LEDA, LEDK):
    assert b.FindNet(nm) is not None, nm
assert [J1.FindPadByNumber(str(k)).GetNetname() for k in (3, 5, 6, 7, 8, 10, 11)] == [MOSI, SCK, DC, RST, CS, BL, N3]

# ------------------------------------------------------------------ west of the lands: MOSI (land 3), SCK (4), RST (6) to the inner row
YS1, YS2 = 140.1, 140.9                                    # two rows of vias south of the inner row of J1
seg(MOSI, [(LAND_X0 + 0.5, land(3)), (col(3), land(3)), (col(3), YS1)])
via(MOSI, (col(3), YS1))
seg(MOSI, [(col(3), YS1), (col(3), PAD_I)], 'B.Cu')
seg(SCK, [(LAND_X0 + 0.5, land(4)), (174.9, land(4)), (174.9, YS2 - 0.4), (175.3, YS2), (col(5), YS2)])
via(SCK, (col(5), YS2))
seg(SCK, [(col(5), YS2), (col(5), PAD_I)], 'B.Cu')
seg(RST, [(LAND_X0 + 0.5, land(6)), (175.35, land(6)), (175.35, YS1 - 0.4), (175.75, YS1), (col(7), YS1)])
via(RST, (col(7), YS1))
seg(RST, [(col(7), YS1), (col(7), PAD_I)], 'B.Cu')
# ------------------------------------------------------------------ east of the lands: DC (land 5), CS (7) to the outer row
YN1, YN2 = 130.2, 129.5                                    # DC runs south of CS: CS has the shorter way west
seg(CS, [(LAND_X1 - 0.5, land(7)), (181.0, land(7)), (181.0, YN2 + 0.4), (180.6, YN2), (col(8), YN2)])
via(CS, (col(8), YN2))
seg(CS, [(col(8), YN2), (col(8), PAD_O)], 'B.Cu')
seg(DC, [(LAND_X1 - 0.5, land(5)), (180.5, land(5)), (180.5, YN1 + 0.4), (180.1, YN1), (col(6), YN1)])
via(DC, (col(6), YN1))
seg(DC, [(col(6), YN1), (col(6), PAD_O)], 'B.Cu')
# ------------------------------------------------------------------ supply (land 10) and backlight (11 cathode, 12 anode)
VV = (182.43, land(10))                                    # between the lands of pins 9 and 11 of J1
seg(N3, [(LAND_X1 - 0.5, land(10)), VV])
via(N3, VV)
seg(N3, [VV, (VV[0] + RAIL - VV[1], RAIL), (188.44, RAIL)], 'B.Cu', 0.3)
LK, LA = (DX, land(11)), (189.46, land(12))
seg(LEDK, [(LAND_X1 - 0.5, land(11)), LK])
via(LEDK, LK)
seg(LEDK, [LK, (DX, QY)], 'B.Cu')
seg(LEDA, [(LAND_X1 - 0.5, land(12)), LA])
via(LEDA, LA)
seg(LEDA, [LA, (189.46, RAIL)], 'B.Cu')
# backlight switch: pin 10 of J1 - north - east - round the source of Q1 - gate; R2 below the gate
seg(BL, [(col(10), PAD_O), (col(10), 130.35), (187.0, 130.35), (187.4, 130.75), (187.4, QY + 0.55), (187.8, QY + 0.95), (GX, QY + 0.95)], 'B.Cu')
seg(BL, [(GX, QY + 0.95), (GX, QY + 2.24)], 'B.Cu')
# ------------------------------------------------------------------ ground
GV = (182.43, JC[1])                                       # between the two rows of J1, between the lands of pins 9 / 10 and 11 / 12
seg(GND, [(LAND_X1 - 0.5, land(8)), (GV[0] - (land(8) - GV[1]), land(8)), GV])
via(GND, GV)
seg(GND, [GV, (col(12) - 0.5, GV[1]), (col(12), GV[1] - 0.5), (col(12), PAD_O)], 'B.Cu', 0.3)
seg(GND, [(LAND_X1 - 0.5, land(13)), (180.6, land(13)), (181.2, land(13) + 0.6)])
via(GND, (181.2, land(13) + 0.6))
seg(GND, [(186.3, RAIL - 0.96), (187.35, RAIL - 0.96)], 'B.Cu', 0.3)       # C1, C2
seg(GND, [(186.8, RAIL - 0.96), (186.8, RAIL - 1.9)], 'B.Cu', 0.3)
via(GND, (186.8, RAIL - 1.9))
seg(GND, [(GX, QY - 0.95), (GX, QY - 1.9)], 'B.Cu', 0.3)                   # source of Q1
via(GND, (GX, QY - 1.9))
seg(GND, [(GX, QY + 3.26), (GX + 0.9, QY + 3.26)], 'B.Cu', 0.3)            # R2
via(GND, (GX + 0.9, QY + 3.26))
seg(GND, [(col(1), PAD_I), (169.6, PAD_I)], 'B.Cu', 0.3)                   # pin 1
via(GND, (169.6, PAD_I))
for c in ((164.0, 129.5), (164.0, 140.8), (167.0, 135.15), (172.3, 129.4), (184.6, 141.0), (191.2, 141.0), (191.3, 136.0), (185.9, 129.0)):
    via(GND, c)

# ------------------------------------------------------------------ ground on both layers
poly = [(W, N), (E, N), (E, S), (W, S)]
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

# ------------------------------------------------------------------ silkscreen (back: the side one sees when the board is unplugged)
# The title is that of the transmitter board ("WPT TX v0.2.0 / T. Sasatani / Nov. 18, 2026": inverted, along an edge,
# read from the bottom, lines aligned at their start). The name is longer here and the board is 14.8 mm wide: four
# lines of 0.8 mm instead of three of 1.0 mm, in the strip between the socket and the west edge.
JW = J1.GetCourtyard(pcbnew.B_CrtYd).BBox().GetLeft() / MM
tt = text('WPT TX DISPLAY\nv0.2.0\nT. Sasatani\nNov. 18, 2026', (W + JW) / 2, (N + S) / 2, 'B.SilkS', rot=TITLE_ROT, justify='left', knockout=True)
bb = tt.GetBoundingBox()
box = (bb.GetLeft() / MM, bb.GetTop() / MM, bb.GetRight() / MM, bb.GetBottom() / MM)
assert box[0] > W + 0.5 and box[2] < JW - 0.5 and box[1] > N + 0.5 and box[3] < S - 0.5, (box, W, JW, N, S)
print('title: x %.2f .. %.2f, y %.2f .. %.2f (strip x %.2f .. %.2f)' % (box[0], box[2], box[1], box[3], W, JW))
text('to J2', JC[0], 141.3, 'B.SilkS')

tb = b.GetTitleBlock()
tb.SetTitle('WPT transmitter: display board (provisional)')
tb.SetRevision('0.2.0')
tb.SetDate('2026-11-18')
tb.SetComment(0, 'Plugs onto J2 of WPT-01-TRANSMITTER, 9.9 mm above it. Coordinates are those of that board.')

pcbnew.SaveBoard(out_path, b)
print('saved', out_path)

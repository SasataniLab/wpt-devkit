#!/usr/bin/env python3
"""Revision 8 on the board: 36 V input block, I2C without the level shifter, legacy extras removed.
usage: mech19.py BOARD_IN BOARD_OUT NETLIST      (schematic with tools/schematic/edit_sch12.py; NETLIST = its export)

Input (south-west corner)
  CN207, TP211, TP216, TP217 and the inner-layer track from J202 to CN203 go.
  J202 moves 8.6 mm north to where J4 stood (J4 goes), 2.4 mm from the west edge.
  C224 (100 uF / 50 V, 8 x 10 mm can) takes the place of CN207 and the old J202: + pad on the copper that fed the 7 V
  converter, - pad with two vias to the ground plane. Both converters hang on one net now (DC_IN).
  D204 (S210FA) between J202 and C224.
I2C
  U202, R214, C210, R217, R218 and their copper go; R221 / R222 (already on the board, now fitted) join the bus sections.
  The logic supply of U204 (VL, SHDN, C209) becomes +3V3. It comes down the board on the back-side track that was
  ~{WLAT}: cut west of J1, where a new via ties it to the +3V3 plane (In2), and joined to U204's two supply vias on In2
  at the south end.
  The rest of ~{WLAT} (MCU to J1) goes with R223.
Others
  R226: removed, its pads bridged by a 1 mm track (LDO output = +5V); both sense lines of U203 channel 1 stay.
  CN209, CN210: removed; CN208 moves onto CN209's holes, where the inner-layer feed arrives.
  J4: removed with its two stubs.
Every pad gets the net the netlist gives it; the silkscreen labels of J4 are replaced by those of J202.
"""
import sys
import pcbnew
import newfp
from newfp import P, V

src, dst, netfile = sys.argv[1:4]
b = pcbnew.LoadBoard(src)
comps = newfp.load_netlist(netfile)
MM = 1e6
short = lambda n: n.split('/')[-1]
DC_IN, J202_NET = comps['J201']['pins']['1'], comps['J202']['pins']['1']
assert short(DC_IN) == 'DC_IN' and short(J202_NET) == 'Net-(D204-A)', (DC_IN, J202_NET)
gone = []                                                    # copper to remove, carried out at the very end


def near(p, q, tol=0.0015):
    return abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) < tol


def is_gone(t):
    return any(t is x for x in gone)


def pieces(net_short, layer=None):
    for t in b.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T and short(t.GetNetname()) == net_short and not is_gone(t) and (layer is None or b.GetLayerName(t.GetLayer()) == layer):
            yield t


def piece(net_short, layer, a, e):
    hit = [t for t in pieces(net_short, layer) if (near(P(t.GetStart()), a) and near(P(t.GetEnd()), e)) or (near(P(t.GetStart()), e) and near(P(t.GetEnd()), a))]
    assert len(hit) == 1, (net_short, layer, a, e, len(hit))
    return hit[0]


def via_at(net_short, c):
    hit = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and short(t.GetNetname()) == net_short and near(P(t.GetPosition()), c) and not is_gone(t)]
    assert len(hit) == 1, (net_short, c, len(hit))
    return hit[0]


def drop(net_short, layer, *polys):
    """remove the pieces along the polylines (corner by corner)"""
    for poly in polys:
        for a, e in zip(poly, poly[1:]):
            gone.append(piece(net_short, layer, a, e))


def drop_via(net_short, c):
    gone.append(via_at(net_short, c))


def drop_net(net_short):
    n = 0
    for t in b.GetTracks():
        if short(t.GetNetname()) == net_short and not is_gone(t):
            gone.append(t)
            n += 1
    return n


def renet(old_short, new_full):
    """all copper and zones of a net go to another net"""
    new, n = newfp.net(b, new_full), 0
    for t in b.GetTracks():
        if short(t.GetNetname()) == old_short and not is_gone(t):
            t.SetNet(new)
            n += 1
    for z in b.Zones():
        if short(z.GetNetname()) == old_short:
            z.SetNet(new)
            n += 1
    return n


def seg(net_full, layer, pts, w):
    newfp.seg(b, net_full, pts, w=w, layer=layer)


def remove_fp(*refs):
    for r in refs:
        fp = b.FindFootprintByReference(r)
        assert fp is not None, r
        gone.append(fp)


def pad(ref, num):
    return [P(p.GetPosition()) for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]


# ================================================================= nets that merge
print('copper renamed to DC_IN:', renet('Net-(CN207-P1)', DC_IN) + renet('Net-(CN207-P2)', DC_IN))
print('copper renamed to +5V:', renet('Net-(U203-SENSE1+)', '+5V'))

# ================================================================= input block
remove_fp('CN207', 'TP211', 'TP216', 'TP217')
print('J202 net, old copper removed:', drop_net('Net-(CN203-P3)'))             # front-side track to CN207 and the wide inner-layer track to CN203
drop('DC_IN', 'F.Cu', [(158.55, 177.1), (160.325, 177.1), (161.35, 176.075)], [(161.79, 182.88), (158.55, 179.64)])
j202 = b.FindFootprintByReference('J202')
j202.SetPosition(V(152.4, 169.87))
assert near(pad('J202', '1'), (152.4, 171.14)) and near(pad('J202', '2'), (152.4, 168.6)), (pad('J202', '1'), pad('J202', '2'))
j202.Reference().SetPosition(V(152.4, 166.3))
newfp.place(b, comps, 'C224', 156.0, 177.145, rot=180, ref_at=(0, 0))        # reference between the pads (under the can)
newfp.place(b, comps, 'D204', 158.6, 171.14, rot=180, ref_at=(4.0, 0.3))
c224 = b.FindFootprintByReference('C224')                                       # the symbol carries a field "Size", as the other capacitors do
f = pcbnew.PCB_FIELD(c224, pcbnew.FIELD_T_USER, 'Size')
f.SetText('8x10.2')
f.SetVisible(False)
f.SetLayer(pcbnew.F_Fab)
f.SetPosition(c224.GetPosition())
c224.Add(f)
c224.GetField('Description').SetText('Aluminium electrolytic capacitor, 100 uF, 50 V, 8 x 10.2 mm, surface mount')   # as in the schematic
PLUS, MINUS, DK, DA = pad('C224', '1'), pad('C224', '2'), pad('D204', '1'), pad('D204', '2')
assert near(PLUS, (159.25, 177.145)) and near(MINUS, (152.75, 177.145)) and near(DK, (160.15, 171.14)) and near(DA, (157.05, 171.14)), (PLUS, MINUS, DK, DA)
seg(DC_IN, 'F.Cu', [PLUS, (159.25, 180.34), (161.79, 182.88)], 2.0)             # to the jack: the old diagonal, started under the can
seg(DC_IN, 'F.Cu', [PLUS, (160.28, 177.145), (161.35, 176.075)], 1.0)           # to C202 / U207
seg(DC_IN, 'F.Cu', [DK, (160.15, 176.245), PLUS], 1.0)                           # from D204
newfp.net(b, J202_NET)
seg(J202_NET, 'F.Cu', [(152.4, 171.14), DA], 1.0)
for y in (175.3, 179.0):                                                         # the can's ground
    newfp.via(b, 'GND', (152.75, y))
seg('GND', 'F.Cu', [(152.75, 175.3), MINUS, (152.75, 179.0)], 0.5)

# ================================================================= J4 and its two stubs
remove_fp('J4')
drop('USART1_RX_EXTERNAL', 'B.Cu', [(155.25, 157.45), (154.5, 158.2), (154.5, 161.5), (153.8, 162.2)])
drop_via('USART1_RX_EXTERNAL', (153.8, 162.2))
drop('USART1_RX_EXTERNAL', 'F.Cu', [(153.8, 162.2), (153.8, 162.6), (152.4, 164.0)])
drop('USART1_TX_EXTERNAL', 'F.Cu', [(154.5, 156.75), (154.5, 164.44), (152.4, 166.54)])

# ================================================================= I2C cluster
remove_fp('U202', 'R214', 'C210', 'R217', 'R218')
print('enable net of U202 removed:', drop_net('Net-(U202-EN)'))
drop('+5V', 'F.Cu', [(159.7, 158.644), (159.7, 159.644), (159.7, 160.644)], [(159.7, 159.644), (159.094, 160.25), (159.0, 160.25)])
drop_via('+5V', (159.0, 160.25))
drop('+5V', 'B.Cu', [(159.0, 160.25), (159.0, 160.5), (159.7, 161.2), (159.7, 163.0), (159.95, 163.25), (160.0, 163.25), (160.05, 163.3), (160.15, 163.3),
                     (160.7, 163.85), (160.75, 163.85), (160.8, 163.9), (161.9, 163.9), (162.2, 164.2)])
drop_via('+5V', (162.2, 164.2))
drop('GND', 'F.Cu', [(159.7, 161.644), (158.8, 161.644), (158.8, 161.95), (158.85, 162.0)], [(164.95, 160.894), (165.75, 160.894), (166.0, 161.144)])
drop_via('GND', (158.85, 162.0))
drop_via('GND', (166.0, 161.144))
drop('+3V3', 'F.Cu', [(164.95, 160.394), (166.75, 160.394), (167.1, 160.044), (167.1, 159.644)])
drop('SCL_5V', 'F.Cu', [(160.7, 159.644), (160.95, 159.894), (161.85, 159.894), (162.549, 159.894), (162.7, 160.045), (162.7, 161.344), (161.9, 162.144)])
drop('SDA_5V', 'F.Cu', [(160.7, 158.644), (160.75, 158.644), (161.5, 159.394), (161.85, 159.394), (162.615, 159.394), (163.035, 159.815)])

# ================================================================= +3V3 for the logic side of U204, on the old ~{WLAT} track
WLAT = '~{WLAT}'
keep = [(153.6, 166.55), (155.4, 168.35), (155.4, 182.134), (153.0, 184.534), (153.0, 189.731), (157.188, 193.919), (157.188, 196.088), (158.825, 197.725), (158.825, 198.625)]
p3 = newfp.net(b, '+3V3')
for a, e in zip(keep, keep[1:]):
    piece(WLAT, 'B.Cu', a, e).SetNet(p3)
via_at(WLAT, (158.825, 198.625)).SetNet(p3)
t = piece(WLAT, 'B.Cu', (153.6, 162.95), (153.6, 166.55))                       # its north end becomes a via into the +3V3 plane (In2, west of J1)
if near(P(t.GetStart()), (153.6, 162.95)):
    t.SetStart(V(153.6, 165.5))
else:
    t.SetEnd(V(153.6, 165.5))
t.SetNet(p3)
print('rest of ~{WLAT} removed:', drop_net(WLAT))
newfp.via(b, '+3V3', (153.6, 165.5))
drop('Net-(U204-~{WLAT})', 'F.Cu', [(161.35, 198.65), (162.35, 198.65)])        # the link to R223
remove_fp('R223')
drop('+5V', 'In2.Cu', [(165.6, 197.3), (166.9, 197.3), (167.8, 198.2), (170.4, 198.2)])     # U204 no longer hangs on the 5 V feed of R212
for a, e in (((158.7, 193.7), (160.5, 193.7)), ((160.5, 193.7), (164.1, 197.3)), ((164.1, 197.3), (165.6, 197.3))):
    piece('+5V', 'In2.Cu', a, e).SetNet(p3)
for a, e in (((159.5, 193.7), (158.7, 193.7)), ((159.5, 193.7), (159.8, 193.4)), ((159.8, 193.4), (161.0, 193.4)), ((166.9, 197.3), (165.6, 197.3))):
    piece('+5V', 'F.Cu', a, e).SetNet(p3)
for c in ((158.7, 193.7), (165.6, 197.3)):
    via_at('+5V', c).SetNet(p3)
seg('+3V3', 'In2.Cu', [(158.825, 198.625), (164.275, 198.625), (165.6, 197.3)], 0.2)

# ================================================================= R226
remove_fp('R226')
drop('+5V', 'F.Cu', [(181.65, 169.1), (180.55, 169.1)], [(183.75, 169.1), (182.65, 169.1)])
seg('+5V', 'F.Cu', [(180.55, 169.1), (181.65, 169.1), (182.65, 169.1), (183.75, 169.1)], 1.0)

# ================================================================= 5 V header: one of three
remove_fp('CN209', 'CN210')
b.FindFootprintByReference('CN208').SetPosition(V(209.285, 137.769))
assert near(pad('CN208', '1'), (209.285, 139.039)), pad('CN208', '1')
drop('+5V', 'B.Cu', [(211.825, 139.039), (209.285, 139.039), (206.745, 139.039)])
drop('GND', 'B.Cu', [(206.745, 136.499), (209.285, 136.499), (211.825, 136.499)])

# ================================================================= pad nets as in the netlist
changed = []
for fp in b.GetFootprints():
    if any(fp is x for x in gone):
        continue
    c = comps.get(fp.GetReference())
    if c is None:
        continue
    for p in fp.Pads():
        want = c['pins'].get(p.GetNumber())
        if want is not None and p.GetNetname() != want:
            changed.append('%s.%s %s -> %s' % (fp.GetReference(), p.GetNumber(), short(p.GetNetname()), short(want)))
            p.SetNet(newfp.net(b, want))
print('pad nets changed: %d\n   %s' % (len(changed), '\n   '.join(changed)))

# ================================================================= silkscreen: the labels of J4 become those of J202
texts = {(154.4, 164.0): None, (154.4, 166.54): None, (160.2, 166.2): None, (154.4, 169.08): ('36V', (154.75, 169.3)), (154.4, 171.62): ('+', (154.75, 171.3))}
n = 0
for d in list(b.GetDrawings()):
    if isinstance(d, pcbnew.PCB_TEXT) and b.GetLayerName(d.GetLayer()) == 'F.Silkscreen':
        for at, new in texts.items():
            if near(P(d.GetPosition()), at):
                n += 1
                if new is None:
                    gone.append(d)
                else:
                    d.SetText(new[0])
                    d.SetPosition(V(*new[1]))
                    if new[0] == '+':
                        d.SetTextAngleDegrees(0)
assert n == 5, n

for item in gone:
    b.Remove(item)
pcbnew.SaveBoard(dst, b)
print('removed items:', len(gone))

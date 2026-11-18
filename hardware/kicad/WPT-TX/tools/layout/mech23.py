#!/usr/bin/env python3
"""Silkscreen that the DRC warned about (44 items), corrected in the drawings themselves.
usage: mech23.py BOARD_IN BOARD_OUT LIB_DIR        (LIB_DIR = lib/footprints of the project; its footprints are rewritten)

  TestPoint:PTH_1mm (11)      the ring (radius 0.75) lay on the pad's own mask opening (radius 0.80): radius 1.00.
  SOD-523F_Diodes (8)         the side lines lay on the mask openings of the pads: 0.15 mm further out.
  LED_D3.0mm (D201)           the flat ran across pad 1: now two short pieces; the two arcs end before pad 2.
  NR5040 (L201, L202)         outline 5.6 x 5.6 mm -> 5.6 x 5.2 mm (the part is 4.9 mm): its long side crossed a line of
                              C207 / C208.
  ULO-PH409-1x3SX1 (CN203)    the bracket at pin 1 crossed a line of C218: now a bar beside pin 1.
  54-00129 (J201)             outline outside the board (the jack overhangs the edge): cut at the edge.
  SW2                         its thin outline lay on the mask openings of its mounting pads and inside the wide
                              insulating band drawn under the cover: the four lines are removed (the band shows the
                              outline). The footprint moves from KiCad's library to the project library
                              Button_Switch_BoardEdge (the schematic names it there too).
  TP215, U307                 references 0.35 / 0.32 mm lower, clear of the larger ring and of the outline of D312.
Every changed footprint is written back to the project library, so that board and library agree.
"""
import math
import os
import sys
import pcbnew
from newfp import P, V

src, dst, libdir = sys.argv[1:4]
b = pcbnew.LoadBoard(src)
MM = 1e6
gone = []
changed = {}                                   # footprint id -> one instance


def silk(fp):
    return [g for g in fp.GraphicalItems() if g.GetClass() == 'PCB_SHAPE' and 'Silk' in b.GetLayerName(g.GetLayer())]


def seg(fp, a, e, tol=0.002):
    near = lambda p, q: abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) < tol
    hit = [g for g in silk(fp) if g.GetShape() == pcbnew.SHAPE_T_SEGMENT and ((near(P(g.GetStart()), a) and near(P(g.GetEnd()), e)) or (near(P(g.GetStart()), e) and near(P(g.GetEnd()), a)))]
    assert len(hit) == 1, (fp.GetReference(), a, e, len(hit))
    return hit[0]


for fp in b.GetFootprints():
    fid = fp.GetFPIDAsString()
    c = P(fp.GetPosition())
    if fid == 'TestPoint:PTH_1mm':
        for g in silk(fp):
            assert g.GetShape() == pcbnew.SHAPE_T_CIRCLE and abs(g.GetRadius() / MM - 0.75) < 1e-3
            e = P(g.GetEnd())                                   # same direction as before: rotated instances stay equal to the library
            g.SetEnd(V(c[0] + (e[0] - c[0]) / 0.75, c[1] + (e[1] - c[1]) / 0.75))
        changed[fid] = fp
    elif fid == 'Diodes_SMD:SOD-523F_Diodes':
        p1, p2 = [P(p.GetPosition()) for p in sorted(fp.Pads(), key=lambda p: p.GetNumber())]
        L = math.dist(p1, p2)
        u = ((p1[0] - p2[0]) / L, (p1[1] - p2[1]) / L)
        nrm = (-u[1], u[0])
        for g in silk(fp):
            for get, put in ((g.GetStart, g.SetStart), (g.GetEnd, g.SetEnd)):
                q = P(get())
                lat = (q[0] - c[0]) * nrm[0] + (q[1] - c[1]) * nrm[1]
                assert abs(abs(lat) - 0.45) < 0.01, (fp.GetReference(), q, lat)
                d = math.copysign(0.15, lat)
                put(V(q[0] + d * nrm[0], q[1] + d * nrm[1]))
        changed[fid] = fp
    elif fid == 'taiyo-yuden:NR5040':
        assert fp.GetOrientationDegrees() == 0
        for g in silk(fp):
            for get, put in ((g.GetStart, g.SetStart), (g.GetEnd, g.SetEnd)):
                q = P(get())
                assert abs(abs(q[0] - c[0]) - 2.8) < 0.01 and abs(abs(q[1] - c[1]) - 2.8) < 0.01, q
                put(V(q[0], c[1] + math.copysign(2.6, q[1] - c[1])))
        changed[fid] = fp

# ---- D201
fp = b.FindFootprintByReference('D201')
c = P(fp.GetPosition())
assert c == (185.8, 196.15) and fp.GetOrientationDegrees() == 180
flat = seg(fp, (187.3, 197.695), (187.3, 194.605))
flat.SetStart(V(187.3, 194.605)); flat.SetEnd(V(187.3, 194.95))
g2 = pcbnew.PCB_SHAPE(fp, pcbnew.SHAPE_T_SEGMENT)
g2.SetLayer(flat.GetLayer()); g2.SetWidth(flat.GetWidth()); g2.SetStart(V(187.3, 197.35)); g2.SetEnd(V(187.3, 197.695))
fp.Add(g2)
R = math.dist(c, (187.3, 194.605))
pad2 = (184.53, 196.15)
phi = next(a for a in (math.radians(k * 0.5) for k in range(1, 180)) if math.dist((c[0] - R * math.cos(a), c[1] + R * math.sin(a)), pad2) >= 1.2)
k = 0
for g in silk(fp):
    if g.GetShape() == pcbnew.SHAPE_T_ARC and abs(g.GetWidth() / MM - 0.12) < 1e-3:
        s, e = P(g.GetStart()), P(g.GetEnd())
        east = s if abs(s[0] - 187.3) < 0.01 else e
        assert abs(east[0] - 187.3) < 0.01
        sgn = 1 if east[1] > c[1] else -1                      # the arc now stays on the side of its east end
        ae = math.pi - math.atan2(abs(east[1] - c[1]), east[0] - c[0])
        pt = lambda a: (c[0] - R * math.cos(a), c[1] + sgn * R * math.sin(a))
        if east == s:
            g.SetArcGeometry(V(*east), V(*pt((phi + ae) / 2)), V(*pt(phi)))
        else:
            g.SetArcGeometry(V(*pt(phi)), V(*pt((phi + ae) / 2)), V(*east))
        k += 1
assert k == 2
changed[fp.GetFPIDAsString()] = fp

# ---- CN203: a bar beside pin 1 instead of the bracket
fp = b.FindFootprintByReference('CN203')
assert fp.GetOrientationDegrees() == -90
gone.append((fp, seg(fp, (176.815, 183.475), (178.365, 183.475))))
gone.append((fp, seg(fp, (178.365, 186.575), (176.815, 186.575))))
g = seg(fp, (178.365, 183.475), (178.365, 186.575)); g.SetStart(V(178.365, 183.8)); g.SetEnd(V(178.365, 186.25))
changed[fp.GetFPIDAsString()] = fp

# ---- SW2: the band replaces the thin outline; project-local footprint
fp = b.FindFootprintByReference('SW2')
for a, e in (((151.15, 159.65), (151.15, 149.75)), ((151.9, 147.7), (157.1, 147.7)), ((157.1, 161.7), (151.9, 161.7)), ((157.85, 149.75), (157.85, 159.65))):
    gone.append((fp, seg(fp, a, e)))
fp.SetFPIDAsString('Button_Switch_BoardEdge:SW_E-Switch_EG2219_DPDT_Angled')
changed[fp.GetFPIDAsString()] = fp

# ---- J201: nothing outside the board (edge at x = 150)
fp = b.FindFootprintByReference('J201')
X = 150.45
gone.append((fp, seg(fp, (148.19, 191.3), (148.19, 182.2))))
g = seg(fp, (148.19, 182.2), (162.59, 182.2)); g.SetStart(V(X, 182.2)); g.SetEnd(V(162.59, 182.2))
g = seg(fp, (156.94, 191.3), (148.19, 191.3)); g.SetStart(V(156.94, 191.3)); g.SetEnd(V(X, 191.3))
changed[fp.GetFPIDAsString()] = fp

r = b.FindFootprintByReference('U307').Reference()               # the wider outline of D312 reached this text
assert P(r.GetPosition()) == (192.91, 177.425), P(r.GetPosition())
r.SetPosition(V(192.91, 177.75))
r = b.FindFootprintByReference('TP215').Reference()
assert P(r.GetPosition()) == (195.05, 148.5), P(r.GetPosition())
r.SetPosition(V(195.05, 148.85))

for fp, g in gone:
    fp.Remove(g)
pcbnew.SaveBoard(dst, b)
print('footprint types changed:', sorted(changed), '; lines removed:', len(gone))

# ---- the same footprints into the project library (a copy of one instance, brought back to the library's frame)
b2 = pcbnew.LoadBoard(dst)
for fid in sorted(changed):
    nick, name = fid.split(':')
    fp = next(f for f in b2.GetFootprints() if f.GetFPIDAsString() == fid)
    if fp.IsFlipped():
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(0)
    fp.SetPosition(V(0, 0))
    fp.SetReference('REF**')
    fp.SetPath(pcbnew.KIID_PATH(''))
    fp.SetSheetname(''); fp.SetSheetfile('')
    for pd in fp.Pads():
        pd.SetNetCode(0)
    pcbnew.FootprintSave(os.path.join(libdir, nick + '.pretty'), fp)
    print('library:', nick, name)

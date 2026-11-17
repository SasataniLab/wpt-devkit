#!/usr/bin/env python3
"""Drawings of the display board on the transmitter board.
usage: drawings.py TRANSMITTER.kicad_pcb DISPLAY.kicad_pcb OUT_PLAN.png OUT_SIDE.png OUT_BOARD.png

OUT_PLAN   the top of the transmitter board (kicad-cli render) with the outline of the display board over it:
           what it covers and what stays free
OUT_SIDE   heights above the transmitter board, seen from the south (parts at different y drawn in one view)
OUT_BOARD  both sides of the display board (kicad-cli render) with the display drawn in

Both boards use the coordinates of the transmitter board, so positions are read from the two board files.
What cannot be read from them (heights, mating parts) is in the table below with its source.
"""
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
import pcbnew
from PIL import Image, ImageDraw, ImageFont

main_path, disp_path, out_plan, out_side, out_board = sys.argv[1:6]
MM = 1e6
main = pcbnew.LoadBoard(main_path)
disp = pcbnew.LoadBoard(disp_path)


def fp(board, ref):
    f = board.FindFootprintByReference(ref)
    assert f is not None, ref
    return f


def pos(board, ref):
    p = fp(board, ref).GetPosition()
    return p.x / MM, p.y / MM


def pad_xy(board, ref, num):
    for p in fp(board, ref).Pads():
        if p.GetNumber() == num:
            return p.GetPosition().x / MM, p.GetPosition().y / MM
    raise AssertionError((ref, num))


def court(board, ref):
    f = fp(board, ref)
    r = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd).BBox()
    return r.GetLeft() / MM, r.GetTop() / MM, r.GetRight() / MM, r.GetBottom() / MM


# ---- from the two boards
EDGE = (150.0, 125.0, 220.0, 205.0)
poly = pcbnew.SHAPE_POLY_SET()
assert disp.GetBoardPolygonOutlines(poly, False)
o = poly.Outline(0)
OUTLINE = [(o.CPoint(i).x / MM, o.CPoint(i).y / MM) for i in range(o.PointCount())]
OX0, OX1 = min(p[0] for p in OUTLINE), max(p[0] for p in OUTLINE)
OY0, OY1 = min(p[1] for p in OUTLINE), max(p[1] for p in OUTLINE)
DS = pos(disp, 'DS1')
H1 = pos(disp, 'H1')
J1_1, J1_12 = pad_xy(disp, 'J1', '1'), pad_xy(disp, 'J1', '12')
J2_1, J2_12 = pad_xy(main, 'J2', '1'), pad_xy(main, 'J2', '12')
assert J1_1 == J2_1 and J1_12 == J2_12, 'the socket is not over the header'
J3_1, J3_14 = pad_xy(main, 'J3', '1'), pad_xy(main, 'J3', '14')
SW3 = pos(main, 'SW3')
ENC = (pos(main, 'SW1')[0] + 7.5, pos(main, 'SW1')[1] + 2.5)       # shaft axis of the EC11E footprint
J5 = court(main, 'J5')
CN = (court(main, 'CN210')[0], court(main, 'CN210')[1], court(main, 'CN208')[2], court(main, 'CN208')[3])
TP = {r: pos(main, r) for r in ('TP301', 'TP302', 'TP303', 'TP304', 'TP214', 'TP215', 'TP224', 'TP225')}
STRIP_S = max(p[1] for p in OUTLINE if p[0] < 180.0)                # south edge of the strip
STRIP_N = min(p[1] for p in OUTLINE if p[0] < 180.0)
BLK_W = min(p[0] for p in OUTLINE if p[1] > 150.0)                  # west edge of the block
assert (ENC, SW3) == ((167.9, 150.6), (162.0, 126.25)), (ENC, SW3)
inside = lambda p: poly.Contains(pcbnew.VECTOR2I(int(p[0] * MM), int(p[1] * MM)))
for r in ('TP301', 'TP302', 'TP303', 'TP304', 'TP224', 'TP225'):
    assert not inside(TP[r]), r + ' is under the display board'
for r in ('TP214', 'TP215'):
    assert inside(TP[r]), r

# ---- not in the board files (mm). Sources: Samtec FFSD catalogue page F-226 and print FTSH-1XX-XX-XXX-D-XXX-XX sheet 3;
# Alps EC11E catalogue (update 2510), drawing No. 3; GCT USB4105 drawing (3.31 high) and the USB Type-C plug overmould
# limit (12.35 x 6.5); Wuerth WR-PHD 61301211121 (insulator 2.54) and 61301211821 (socket 8.5); Harwin R30-1001102
# (M3 x 11, 5 mm across flats); panel drawings N096-1608TBBIG11-H13 / MDT0096A2IS-SPI (13.5 x 27.95 x 1.5)
H_INS, H_SOCKET, T_PCB = 2.54, 8.5, 1.6
H_DISP = H_INS + H_SOCKET                 # underside of the display board: 11.04
MOD_W, MOD_L, MOD_T, TAPE = 13.5, 27.95, 1.5, 0.3
AA = (10.8, 21.7, 1.7)                    # active area and its distance from the end opposite to the tail
H_STDC = 7.59
STDC_SOCKET = (J3_1[0] + 0.635 - 1.525 - 1.02, (J3_1[1] + J3_14[1]) / 2 - 13.08 / 2, J3_1[0] + 0.635 + 1.525, (J3_1[1] + J3_14[1]) / 2 + 13.08 / 2)
H_ENC_BODY, H_BUSH, H_SHAFT = 4.5, 11.5, 24.5
KNOB_MAX = 14.0
KNOB = ('ø10.8 × 13.5', 10.8, 13.5, H_SHAFT - 9.6)
H_USB, PLUG_W, PLUG_T, PLUG_Z = 3.31, 12.35, 6.5, 1.65
H_HDR = 2.54 + 6.1                        # the 5 V headers: insulator and pins
H_SOT23 = 1.1
MODULE = (DS[0] - MOD_W / 2, DS[1] - MOD_L / 2, DS[0] + MOD_W / 2, DS[1] + MOD_L / 2)
ACTIVE = (DS[0] - AA[0] / 2, MODULE[1] + AA[2], DS[0] + AA[0] / 2, MODULE[1] + AA[2] + AA[1])

JP = None
for i in range(8):
    try:
        f = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 20, index=i)
    except OSError:
        break
    if f.getname()[0].endswith('JP'):
        JP = i
        break
assert JP is not None, 'Noto Sans CJK JP not found'
font = lambda size: ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', size, index=JP)
BLUE, ORANGE, GREEN, RED, INK, GREY, LIGHT = (25, 95, 200), (205, 110, 0), (15, 130, 80), (200, 30, 40), (25, 25, 30), (95, 95, 100), (205, 205, 210)


def label(d, xy, text, size=22, fill=INK, anchor='la', box=True):
    f = font(size)
    l, t, r, btm = d.textbbox(xy, text, font=f, anchor=anchor)
    if box:
        d.rectangle((l - 5, t - 3, r + 5, btm + 3), fill=(255, 255, 255, 228))
    d.text(xy, text, font=f, fill=fill, anchor=anchor)


def dashed(d, pts, fill, width=3, dash=14, gap=9):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L // (dash + gap)))
        for k in range(n + 1):
            a = k * (dash + gap)
            e = min(a + dash, L)
            if a >= L:
                break
            d.line((x0 + (x1 - x0) * a / L, y0 + (y1 - y0) * a / L, x0 + (x1 - x0) * e / L, y0 + (y1 - y0) * e / L), fill=fill, width=width)


def arrow(d, a, e, fill, width=4, head=14):
    d.line((a, e), fill=fill, width=width)
    ang = math.atan2(e[1] - a[1], e[0] - a[0])
    for s in (-0.45, 0.45):
        d.line((e, (e[0] - head * math.cos(ang + s), e[1] - head * math.sin(ang + s))), fill=fill, width=width)


def render(path, side, w, h):
    """kicad-cli render with a transparent background -> (RGB image on white, bounding box of the board in pixels)"""
    tmp = os.path.join(tempfile.mkdtemp(), 'r.png')
    subprocess.run(['kicad-cli', 'pcb', 'render', '--side', side, '--quality', 'basic', '--background', 'transparent', '-w', str(w), '-h', str(h),
                    '-o', tmp, path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rgba = Image.open(tmp).convert('RGBA')
    return rgba, np.asarray(rgba)[:, :, 3] > 128


# ================================================================== plan view
rgba, mask = render(main_path, 'top', 2944, 3416)
cols, rows = mask.sum(axis=0), mask.sum(axis=1)
cx, ry = np.where(cols > 0.5 * cols.max())[0], np.where(rows > 0.5 * rows.max())[0]   # the board without what stands over its edge
px0, px1, py0, py1 = cx.min(), cx.max() + 1, ry.min(), ry.max() + 1
sx, sy = (px1 - px0) / (EDGE[2] - EDGE[0]), (py1 - py0) / (EDGE[3] - EDGE[1])
assert abs(sx - sy) / sx < 0.005, (sx, sy)
im = Image.alpha_composite(Image.new('RGBA', rgba.size, (255, 255, 255, 255)), rgba).convert('RGB')

WIN = (134.0, 112.5, 228.0, 170.0)       # window in board mm; the margins take the labels
S = 19.0                                 # px per mm
W, H = int((WIN[2] - WIN[0]) * S), int((WIN[3] - WIN[1]) * S)
canvas = Image.new('RGB', (W, H), (255, 255, 255))
crop = (EDGE[0], EDGE[1], EDGE[2], min(EDGE[3], WIN[3]))
src = im.crop((int(px0 + (crop[0] - EDGE[0]) * sx), int(py0 + (crop[1] - EDGE[1]) * sy) - int(1.2 * sy),
               int(px0 + (crop[2] - EDGE[0]) * sx), int(py0 + (crop[3] - EDGE[1]) * sy)))
src = src.resize((int((crop[2] - crop[0]) * S), int((crop[3] - crop[1] + 1.2) * S)), Image.LANCZOS)
src = Image.blend(src, Image.new('RGB', src.size, (255, 255, 255)), 0.40)              # paler, so that the overlay reads
src.paste((255, 255, 255), (0, 0, src.size[0], 3))                                      # the renderer leaves a grey line at the cut
canvas.paste(src, (int((crop[0] - WIN[0]) * S), int((crop[1] - 1.2 - WIN[1]) * S)))
X = lambda x: (x - WIN[0]) * S
Y = lambda y: (y - WIN[1]) * S
box = lambda r: (X(r[0]), Y(r[1]), X(r[2]), Y(r[3]))
P = lambda p: (X(p[0]), Y(p[1]))

ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(ov)
d.polygon([P(p) for p in OUTLINE], fill=BLUE + (58,))
d.line([P(p) for p in OUTLINE + OUTLINE[:1]], fill=BLUE + (255,), width=5)
d.rectangle(box(MODULE), fill=(30, 34, 48, 150), outline=(20, 24, 40, 255), width=3)
d.rectangle(box(ACTIVE), fill=(150, 190, 240, 215), outline=(240, 240, 250, 255), width=2)
d.ellipse((X(H1[0] - 2.9), Y(H1[1] - 2.9), X(H1[0] + 2.9), Y(H1[1] + 2.9)), outline=BLUE + (255,), width=4)
d.line((X(J1_1[0] - 1.27), Y(J1_1[1]), X(J1_12[0] + 1.27), Y(J1_1[1])), fill=BLUE + (255,), width=3)
# what stays free (green) and what is covered (orange)
for r in ('TP301', 'TP302', 'TP303', 'TP304', 'TP224', 'TP225'):
    d.ellipse((X(TP[r][0] - 1.0), Y(TP[r][1] - 1.0), X(TP[r][0] + 1.0), Y(TP[r][1] + 1.0)), outline=GREEN + (255,), width=5)
for r in ('TP214', 'TP215'):
    d.ellipse((X(TP[r][0] - 1.0), Y(TP[r][1] - 1.0), X(TP[r][0] + 1.0), Y(TP[r][1] + 1.0)), outline=ORANGE + (255,), width=5)
d.rectangle(box(STDC_SOCKET), outline=GREEN + (255,), width=4, fill=GREEN + (28,))
arrow(d, (X(STDC_SOCKET[0]), Y(139.6)), (X(STDC_SOCKET[0] - 5.5), Y(139.6)), GREEN + (255,))
d.rectangle(box(CN), outline=GREEN + (255,), width=4, fill=GREEN + (28,))
rk = KNOB_MAX / 2
dashed(d, [(X(ENC[0] + rk * math.cos(t / 30 * math.pi)), Y(ENC[1] + rk * math.sin(t / 30 * math.pi))) for t in range(61)], RED + (255,), width=4, dash=9, gap=6)
arrow(d, (X(SW3[0]), Y(EDGE[1] - 4.4)), (X(SW3[0]), Y(EDGE[1] - 0.9)), GREEN + (255,))
ux = (J5[0] + J5[2]) / 2
arrow(d, (X(ux), Y(EDGE[1] - 4.4)), (X(ux), Y(EDGE[1] - 0.3)), GREEN + (255,))
# the dimension from the strip to the shaft axis
d.line((X(ENC[0]), Y(STRIP_S), X(ENC[0]), Y(ENC[1])), fill=INK + (255,), width=3)
for yy in (STRIP_S, ENC[1]):
    d.line((X(ENC[0] - 0.9), Y(yy), X(ENC[0] + 0.9), Y(yy)), fill=INK + (255,), width=3)
# leaders
lead = lambda a, e, col: d.line((P(a), P(e)), fill=col + (255,), width=3)
for r in ('TP303', 'TP302', 'TP301'):
    a = math.atan2(TP[r][1] - 116.4, TP[r][0] - 176.0)
    lead((176.0, 116.4), (TP[r][0] - 1.1 * math.cos(a), TP[r][1] - 1.1 * math.sin(a)), GREEN)
lead((206.6, 158.3), (TP['TP215'][0] + 0.9, TP['TP215'][1] + 0.5), ORANGE)
lead((206.6, 158.3), (TP['TP214'][0] + 0.9, TP['TP214'][1] + 0.5), ORANGE)
lead((214.0, 151.2), (TP['TP224'][0] + 0.3, TP['TP224'][1] + 1.0), GREEN)
lead((214.0, 151.2), (TP['TP225'][0], TP['TP225'][1] + 1.0), GREEN)
lead((221.4, 122.2), (H1[0] + 2.2, H1[1] - 2.0), BLUE)
out = Image.alpha_composite(canvas.convert('RGBA'), ov)
d = ImageDraw.Draw(out)
label(d, (X(208.2), Y(127.6)), '表示基板', 24, BLUE, 'mm', box=False)
label(d, (X(208.2), Y(130.0)), '11 mm 上', 21, BLUE, 'mm', box=False)
label(d, (X(DS[0]), Y(ACTIVE[1] + 4.6)), '表示', 26, (20, 40, 110), 'mm', box=False)
label(d, (X(DS[0]), Y(ACTIVE[1] + 7.4)), '0.96 型', 22, (20, 40, 110), 'mm', box=False)
label(d, (X(DS[0]), Y(ACTIVE[1] + 9.9)), '80×160', 22, (20, 40, 110), 'mm', box=False)
label(d, (X(176.0), Y(115.6)), 'アナログの確認点 VTH・B・A：隠れない', 22, GREEN, 'mb')
label(d, (X(SW3[0]), Y(EDGE[1] - 5.8)), 'リセット', 22, GREEN, 'mm')
label(d, (X(ux), Y(EDGE[1] - 5.8)), 'USB（付けたまま挿せる）', 22, GREEN, 'mm')
label(d, (X(221.6), Y(120.6)), 'M3 スペーサ', 22, BLUE, 'mm')
label(d, (X(221.6), Y(122.6)), '11 mm', 22, BLUE, 'mm')
label(d, (X(WIN[0] + 0.5), Y(135.0)), 'STDC14 のソケット', 22, GREEN, 'la')
label(d, (X(WIN[0] + 0.5), Y(140.6)), 'ケーブルは西へ', 20, GREEN, 'la')
label(d, (X(CN[2] + 0.6), Y((CN[1] + CN[3]) / 2 - 1.1)), '5 V の', 22, GREEN, 'lm')
label(d, (X(CN[2] + 0.6), Y((CN[1] + CN[3]) / 2 + 1.1)), 'ヘッダ：使える', 22, GREEN, 'lm')
label(d, (X(214.2), Y(152.6)), '+3V3・GND の確認点', 20, GREEN, 'mm')
label(d, (X(214.2), Y(154.6)), '（こちらは見える）', 20, GREEN, 'mm')
label(d, (X(206.8), Y(159.6)), '隠れる確認点：+3V3・GND', 20, ORANGE, 'la')
label(d, (X(ENC[0] - rk - 0.5), Y(ENC[1] + 5.0)), 'つまみ ø14 以下', 22, RED, 'ra')
label(d, (X(ENC[0] + 1.1), Y((STRIP_S + ENC[1]) / 2)), '%.1f' % (ENC[1] - STRIP_S), 22, INK, 'lm')
out.convert('RGB').save(out_plan)
print('plan view', out.size, out_plan)

# ================================================================== side view (seen from the south: west is on the left, as in the plan)
S2 = 21.0
X0, X1, Z0, Z1 = 146.0, 224.0, -6.5, 31.0
ML, MR = 150, 60
W2, H2 = int((X1 - X0) * S2) + ML + MR, int((Z1 - Z0) * S2) + 40
im2 = Image.new('RGB', (W2, H2), (255, 255, 255))
d = ImageDraw.Draw(im2)
U = lambda x: ML + (x - X0) * S2
V = lambda z: 20 + (Z1 - z) * S2
rect = lambda x0, x1, z0, z1: (U(x0), V(z1), U(x1), V(z0))


def part(x0, x1, z0, z1, fill, outline=INK, far=False, width=2):
    if far:                                           # a part that stands in front of or behind the others: outline only, dashed
        dashed(d, [(U(x0), V(z0)), (U(x0), V(z1)), (U(x1), V(z1)), (U(x1), V(z0)), (U(x0), V(z0))], outline, width=2, dash=8, gap=6)
    else:
        d.rectangle(rect(x0, x1, z0, z1), fill=fill, outline=outline, width=width)


d.line((70, V(0), 70, V(30)), fill=GREY, width=2)
for z in range(0, 31, 5):
    d.line((62, V(z), 70, V(z)), fill=GREY, width=2)
    label(d, (56, V(z)), '%d' % z, 20, GREY, 'rm', box=False)
label(d, (56, V(31.0) - 2), 'mm（送電基板の上面から）', 18, GREY, 'la', box=False)
part(EDGE[0], EDGE[2], -T_PCB, 0, (60, 110, 70))                                    # transmitter board
part(J5[0] + 0.9, J5[2] - 0.9, 0, H_USB, LIGHT)                                     # USB receptacle (at the north edge, under the block)
part(ux - PLUG_W / 2, ux + PLUG_W / 2, PLUG_Z - PLUG_T / 2, PLUG_Z + PLUG_T / 2, None, outline=RED, far=True)   # overmould of a plug
part(J2_1[0] - 1.27, J2_12[0] + 1.27, 0, H_INS, (45, 45, 48))                       # J2 and the socket J1
part(J2_1[0] - 1.27, J2_12[0] + 1.27, H_INS, H_DISP, (70, 70, 75))
part(OX0, OX1, H_DISP, H_DISP + T_PCB, BLUE)                                        # display board
q1 = court(disp, 'Q1')
part(q1[0] + 0.6, q1[2] + 2.2, H_DISP - H_SOT23, H_DISP, LIGHT)                     # the small parts on its back
part(MODULE[0], MODULE[2], H_DISP + T_PCB + TAPE, H_DISP + T_PCB + TAPE + MOD_T, (150, 185, 235), outline=BLUE)
part(H1[0] - 2.5, H1[0] + 2.5, 0, H_INS + H_SOCKET - 0.04, (190, 170, 110))         # spacer
part(H1[0] - 2.8, H1[0] + 2.8, H_DISP + T_PCB, H_DISP + T_PCB + 2.0, (150, 150, 155))   # screw head
part(CN[0], CN[2], 0, H_HDR, None, outline=GREEN, far=True)                         # the 5 V headers (south of the arm)
part(STDC_SOCKET[0], STDC_SOCKET[2], 0, H_STDC, None, outline=GREEN, far=True)      # STDC14 with its cable socket
part(ENC[0] - 6.25, ENC[0] + 6.25, 0, H_ENC_BODY, LIGHT)                            # encoder (in front of the strip)
part(ENC[0] - 3.5, ENC[0] + 3.5, H_ENC_BODY, H_BUSH, LIGHT)
part(ENC[0] - 3.0, ENC[0] + 3.0, H_BUSH, H_SHAFT, (235, 235, 238))
name, od, hk, zk = KNOB
part(ENC[0] - od / 2, ENC[0] + od / 2, zk, zk + hk, (120, 120, 126))
z_top = H_DISP + T_PCB + TAPE + MOD_T
for z, text, col, x in ((z_top, '表示器の上面 %.1f' % z_top, BLUE, MODULE[2] + 0.4), (H_DISP + T_PCB, '基板の上面 %.1f' % (H_DISP + T_PCB), BLUE, None),
                        (H_DISP, '下面 %.1f' % H_DISP, BLUE, None)):
    if x is None:
        d.line((U(OX0) - 44, V(z), U(OX0), V(z)), fill=col, width=2)
        label(d, (U(OX0) - 50, V(z)), text, 19, col, 'rm', box=False)
    else:
        label(d, (U(x), V(z) - 4), text, 19, col, 'lb', box=False)
label(d, (U(181.0), V(H_DISP + T_PCB / 2)), '表示基板', 20, (255, 255, 255), 'mm', box=False)
label(d, (U(DS[0]), V(z_top) - 16), '表示器', 20, BLUE, 'mm', box=False)
label(d, (U(180.5), V(7.4)), 'ソケット 8.5', 19, (235, 235, 238), 'mm', box=False)
label(d, (U(180.5), V(1.3)), 'ピンヘッダ 2.54', 19, (235, 235, 238), 'mm', box=False)
label(d, (U(H1[0]), V(6.6)), 'M3', 19, INK, 'mm', box=False)
label(d, (U(H1[0]), V(5.4)), '11.0', 19, INK, 'mm', box=False)
label(d, (U(ENC[0]), V(zk + hk) - 16), 'つまみ ' + name, 20, INK, 'mm', box=False)
label(d, (U(ENC[0]), V(2.2)), 'エンコーダ', 19, GREY, 'mm', box=False)
label(d, (U(ENC[0] + od / 2) + 8, V(zk + hk)), '上端 %.1f' % (zk + hk), 19, INK, 'lm', box=False)
label(d, (U(ENC[0] + od / 2) + 8, V(zk)), '下端 %.1f' % zk, 19, INK, 'lm', box=False)
label(d, (U(ux), V(PLUG_Z + PLUG_T / 2) - 14), 'USB のプラグ（上端 %.1f）' % (PLUG_Z + PLUG_T / 2), 19, RED, 'mm', box=False)
label(d, (U(q1[2] + 2.6), V(H_DISP - H_SOT23 / 2) + 14), '裏面の部品（下端 %.1f）' % (H_DISP - H_SOT23), 19, GREY, 'lm', box=False)
label(d, (U((CN[0] + CN[2]) / 2), V(H_HDR) + 22), '5 V の', 19, GREEN, 'mm', box=False)
label(d, (U((CN[0] + CN[2]) / 2), V(H_HDR) + 46), 'ヘッダ', 19, GREEN, 'mm', box=False)
label(d, (U((STDC_SOCKET[0] + STDC_SOCKET[2]) / 2), V(H_STDC) - 38), 'STDC14', 19, GREEN, 'mm', box=False)
label(d, (U((STDC_SOCKET[0] + STDC_SOCKET[2]) / 2), V(H_STDC) - 14), '上端 7.6', 19, GREEN, 'mm', box=False)
label(d, (U(165.0), V(-3.4)), '送電基板', 20, GREY, 'mm', box=False)
label(d, (U(EDGE[0]), V(-3.4)), '西', 22, GREY, 'lm', box=False)
label(d, (U(EDGE[2]), V(-3.4)), '東', 22, GREY, 'rm', box=False)
im2.save(out_side)
print('side view', im2.size, out_side)

# ================================================================== the display board itself, both sides
PX = 34.0                                 # px per mm asked of the renderer (it fits the board into the picture)
panels = []
for side in ('top', 'bottom'):
    rgba, mask = render(disp_path, side, 2600, 1500)
    ys, xs = np.where(mask)
    bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    s = (bx1 - bx0) / (OX1 - OX0)
    assert abs(s - (by1 - by0) / (OY1 - OY0)) / s < 0.02, (s, (by1 - by0) / (OY1 - OY0))
    img = Image.alpha_composite(Image.new('RGBA', rgba.size, (255, 255, 255, 255)), rgba)
    over = Image.new('RGBA', rgba.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(over)
    if side == 'top':
        px = lambda x: bx0 + (x - OX0) * s
    else:                                 # seen from below: mirrored left to right
        px = lambda x: bx0 + (OX1 - x) * s
    py = lambda y: by0 + (y - OY0) * s
    if side == 'top':
        dd.rectangle((px(MODULE[0]), py(MODULE[1]), px(MODULE[2]), py(MODULE[3])), fill=(150, 190, 240, 70), outline=(235, 240, 255, 255), width=4)
        dd.rectangle((px(ACTIVE[0]), py(ACTIVE[1]), px(ACTIVE[2]), py(ACTIVE[3])), outline=(235, 240, 255, 255), width=2)
    m = int(1.5 * s)
    img = Image.alpha_composite(img, over).crop((bx0 - m, by0 - m, bx1 + m, by1 + m)).convert('RGB')
    panels.append((img, side))
gap, cap = 40, 64
Wb, Hb = max(p[0].size[0] for p in panels), sum(p[0].size[1] for p in panels) + cap * 2 + gap
board_im = Image.new('RGB', (Wb, Hb), (255, 255, 255))
d = ImageDraw.Draw(board_im)
y = 0
for img, side in panels:
    label(d, (12, y + 14), '表面（表示器の側）。外側の枠が表示器、内側の枠が表示される範囲' if side == 'top' else '裏面（送電基板の側、左右が反転）。ソケットと小さな部品はすべてこちら', 26, INK, 'la', box=False)
    board_im.paste(img, (0, y + cap))
    y += cap + img.size[1] + gap
board_im.save(out_board)
print('board', board_im.size, out_board)

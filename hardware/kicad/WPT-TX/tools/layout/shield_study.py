#!/usr/bin/env python3
"""Drawings for the first study of a display board on J2. usage: shield_study.py BOARD OUT_PLAN.png OUT_SIDE.png

OUT_PLAN  the top of the main board (kicad-cli render) with the area a display board can use and what limits it
OUT_SIDE  heights above the main board, seen from the east (parts at different x drawn in one view)

Positions are read from the board file; what cannot be read from it (heights, mating parts) is in the tables below
with its source. docs/stm32-tx/display_shield_study.md explains the drawings.
"""
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
import pcbnew
from PIL import Image, ImageDraw, ImageFont

board_path, out_plan, out_side = sys.argv[1:4]
MM = 1e6
b = pcbnew.LoadBoard(board_path)


def fp(ref):
    f = b.FindFootprintByReference(ref)
    assert f is not None, ref
    return f


def pad_xy(ref, num):
    for p in fp(ref).Pads():
        if p.GetNumber() == num:
            return p.GetPosition().x / MM, p.GetPosition().y / MM
    raise AssertionError((ref, num))


def court(ref):
    r = fp(ref).GetCourtyard(pcbnew.F_CrtYd).BBox()
    return r.GetLeft() / MM, r.GetTop() / MM, r.GetRight() / MM, r.GetBottom() / MM


# ---- from the board
EDGE = (150.0, 125.0, 220.0, 205.0)
J2_1, J2_12 = pad_xy('J2', '1'), pad_xy('J2', '12')
J3_1, J3_14 = pad_xy('J3', '1'), pad_xy('J3', '14')
SW3 = (fp('SW3').GetPosition().x / MM, fp('SW3').GetPosition().y / MM)
ENC = (fp('SW1').GetPosition().x / MM + 7.5, fp('SW1').GetPosition().y / MM + 2.5)     # shaft axis of the EC11E footprint
J5 = court('J5')
CN = (court('CN210')[0], court('CN210')[1], court('CN208')[2], court('CN208')[3])
HOLES = sorted((f.GetPosition().x / MM, f.GetPosition().y / MM) for f in b.GetFootprints() if f.GetValue() == 'Screw_PTH_3mm')
assert J2_1 == (158.3, 141.5) and J2_12 == (186.24, 141.5), (J2_1, J2_12)
assert J3_1 == (152.4, 136.49) and J3_14 == (153.67, 144.11), (J3_1, J3_14)
assert ENC == (167.9, 150.6) and SW3 == (162.0, 126.25), (ENC, SW3)
assert HOLES[0] == (155.0, 130.0), HOLES

# ---- not in the board file (mm). Sources: Samtec FFSD catalogue page F-226 and print FTSH-1XX-XX-XXX-D-XXX-XX sheet 3;
# Alps EC11E catalogue (update 2510), drawing No. 3; Omron B3U data sheet A162-E1-07; GCT USB4105 drawing (3.31 high);
# 2.54 mm header pair: insulator 2.54 + socket 8.5 (Wuerth WR-PHD 6130xx11121 / 6130xx21821)
STDC_SOCKET = (J3_1[0] + 0.635 - 1.525 - 1.02, (J3_1[1] + J3_14[1]) / 2 - 13.08 / 2,
               J3_1[0] + 0.635 + 1.525, (J3_1[1] + J3_14[1]) / 2 + 13.08 / 2)       # FFSD-07: 13.08 x 3.05 plus a 1.02 key on the odd-row side
H_STDC_HDR, H_STDC = 5.71, 7.59          # top of the shroud; top of the mated cable socket
H_INS, H_SOCKET, T_PCB = 2.54, 8.5, 1.6  # header insulator, female socket, board thickness
H_SHIELD = H_INS + H_SOCKET              # underside of the display board: 11.04
H_ENC_BODY, H_BUSH, H_SHAFT, FLAT = 4.5, 11.5, 24.5, 10.0
PUSH = 2.0                               # push travel 1.5 +/- 0.5
KNOB_MAX = 14.0
KNOBS = (('ø10.8 × 13.5（押し込み式の例）', 10.8, 13.5, H_SHAFT - 9.6), ('ø13.7 × 13.5（ねじ止め式の例）', 13.7, 13.5, 14.0))

# ---- the proposal (main-board coordinates)
Y_S = 143.0                              # south edge: 0.23 mm beyond the socket body, 7.6 mm from the shaft axis
N = (156.5, EDGE[1], 188.0, Y_S)         # basic outline
NE = (188.0, EDGE[1], 204.5, Y_S)        # optional: over the USB-C receptacle
SE = (178.0, Y_S, 204.5, 160.0)          # optional: over the crystal and the MCU
EAR_R = 3.2                              # land for the spacer on the north-west mounting hole
assert abs(ENC[1] - Y_S - 7.6) < 1e-6

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

BLUE, ORANGE, GREEN, RED, INK = (25, 95, 200), (215, 120, 0), (20, 140, 90), (200, 30, 40), (25, 25, 30)


def label(d, xy, text, size=24, fill=INK, anchor='la', box=True):
    f = font(size)
    l, t, r, btm = d.textbbox(xy, text, font=f, anchor=anchor)
    if box:
        d.rectangle((l - 5, t - 3, r + 5, btm + 3), fill=(255, 255, 255, 225))
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


# ================================================================== plan view
tmp = tempfile.mkdtemp()
big = os.path.join(tmp, 'top.png')
subprocess.run(['kicad-cli', 'pcb', 'render', '--side', 'top', '--quality', 'basic', '--background', 'transparent', '-w', '2944', '-h', '3416',
                '-o', big, board_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
rgba = Image.open(big).convert('RGBA')
mask = np.asarray(rgba)[:, :, 3] > 128
cols, rows = mask.sum(axis=0), mask.sum(axis=1)
cx, ry = np.where(cols > 0.5 * cols.max())[0], np.where(rows > 0.5 * rows.max())[0]   # the board without what stands over its edge
px0, px1, py0, py1 = cx.min(), cx.max() + 1, ry.min(), ry.max() + 1
sx, sy = (px1 - px0) / (EDGE[2] - EDGE[0]), (py1 - py0) / (EDGE[3] - EDGE[1])
assert abs(sx - sy) / sx < 0.005, (sx, sy)
im = Image.alpha_composite(Image.new('RGBA', rgba.size, (255, 255, 255, 255)), rgba).convert('RGB')

WIN = (137.0, 117.0, 224.0, 166.0)       # window in board mm; the margins take the labels
S = 19.0                                 # px per mm in the drawing
W, H = int((WIN[2] - WIN[0]) * S), int((WIN[3] - WIN[1]) * S)
canvas = Image.new('RGB', (W, H), (255, 255, 255))
crop = (EDGE[0], EDGE[1], EDGE[2], min(EDGE[3], WIN[3]))
src = im.crop((int(px0 + (crop[0] - EDGE[0]) * sx), int(py0 + (crop[1] - EDGE[1]) * sy) - int(1.2 * sy),
               int(px0 + (crop[2] - EDGE[0]) * sx), int(py0 + (crop[3] - EDGE[1]) * sy)))
src = src.resize((int((crop[2] - crop[0]) * S), int((crop[3] - crop[1] + 1.2) * S)), Image.LANCZOS)
src = Image.blend(src, Image.new('RGB', src.size, (255, 255, 255)), 0.38)              # paler, so that the overlay reads
canvas.paste(src, (int((crop[0] - WIN[0]) * S), int((crop[1] - 1.2 - WIN[1]) * S)))
X = lambda x: (x - WIN[0]) * S
Y = lambda y: (y - WIN[1]) * S
box = lambda r: (X(r[0]), Y(r[1]), X(r[2]), Y(r[3]))

ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(ov)
# optional areas first (below the basic outline)
for r, col in ((NE, ORANGE), (SE, GREEN)):
    d.rectangle(box(r), fill=col + (38,))
    x0, y0, x1, y1 = box(r)
    dashed(d, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], col + (255,), width=4)
# basic outline with the ear around the mounting hole
hx, hy = HOLES[0]
d.rectangle(box(N), fill=BLUE + (60,))
d.ellipse((X(hx - EAR_R), Y(hy - EAR_R), X(hx + EAR_R), Y(hy + EAR_R)), fill=BLUE + (60,))
d.rectangle((X(hx), Y(hy - EAR_R), X(N[0]), Y(hy + EAR_R)), fill=BLUE + (60,))
th0 = math.degrees(math.acos(0))                       # the ear meets the body with two straight pieces
pts = [(X(N[0]), Y(Y_S)), (X(N[2]), Y(Y_S)), (X(N[2]), Y(N[1])), (X(N[0]), Y(N[1])), (X(N[0]), Y(hy - EAR_R)), (X(hx), Y(hy - EAR_R))]
d.line(pts, fill=BLUE + (255,), width=5)
d.arc((X(hx - EAR_R), Y(hy - EAR_R), X(hx + EAR_R), Y(hy + EAR_R)), 90, 270, fill=BLUE + (255,), width=5)
d.line([(X(hx), Y(hy + EAR_R)), (X(N[0]), Y(hy + EAR_R)), (X(N[0]), Y(Y_S))], fill=BLUE + (255,), width=5)
d.ellipse((X(hx - 1.6), Y(hy - 1.6), X(hx + 1.6), Y(hy + 1.6)), outline=BLUE + (255,), width=4)
# what limits it
d.rectangle(box(STDC_SOCKET), outline=RED + (255,), width=4, fill=RED + (30,))
arrow(d, (X(STDC_SOCKET[0]), Y(139.6)), (X(STDC_SOCKET[0] - 5.5), Y(139.6)), RED + (255,))
r = KNOB_MAX / 2
dashed(d, [(X(ENC[0] + r * math.cos(t / 30 * math.pi)), Y(ENC[1] + r * math.sin(t / 30 * math.pi))) for t in range(61)], RED + (255,), width=4, dash=9, gap=6)
d.rectangle(box(CN), outline=RED + (255,), width=4, fill=RED + (30,))
arrow(d, (X(SW3[0]), Y(EDGE[1] - 4.2)), (X(SW3[0]), Y(EDGE[1] - 0.9)), RED + (255,))
arrow(d, (X((J5[0] + J5[2]) / 2), Y(EDGE[1] - 4.2)), (X((J5[0] + J5[2]) / 2), Y(EDGE[1] - 0.3)), RED + (255,))
# J2 row and the dimension from the south edge to the shaft axis
d.line((X(J2_1[0] - 1.27), Y(J2_1[1]), X(J2_12[0] + 1.27), Y(J2_1[1])), fill=BLUE + (255,), width=3)
d.line((X(ENC[0]), Y(Y_S), X(ENC[0]), Y(ENC[1])), fill=INK + (255,), width=3)
for yy in (Y_S, ENC[1]):
    d.line((X(ENC[0] - 0.9), Y(yy), X(ENC[0] + 0.9), Y(yy)), fill=INK + (255,), width=3)
out = Image.alpha_composite(canvas.convert('RGBA'), ov)
d = ImageDraw.Draw(out)
label(d, (X((N[0] + N[2]) / 2), Y(133.2)), 'N  基本形  31.5 × 18.0 mm', 30, BLUE, 'mm')
label(d, (X((N[0] + N[2]) / 2), Y(135.6)), 'J2 のソケットは下面の南辺', 22, BLUE, 'mm')
label(d, (X((NE[0] + NE[2]) / 2), Y(137.6)), 'NE  東へ（USB-C の上）', 24, ORANGE, 'mm')
label(d, (X((SE[0] + SE[2]) / 2 + 2.0), Y(157.4)), 'SE  南東へ（MCU の上）', 24, GREEN, 'mm')
d.line((X(WIN[0] + 10.6), Y(127.0), X(hx - EAR_R * 0.72), Y(hy - EAR_R * 0.72)), fill=BLUE, width=3)
label(d, (X(WIN[0] + 0.4), Y(126.2)), 'M3 スペーサ 11 mm', 22, BLUE, 'la')
label(d, (X(WIN[0] + 0.4), Y(128.0)), '（左上の取付穴）', 20, BLUE, 'la')
label(d, (X(WIN[0] + 0.4), Y(136.6)), 'STDC14 のソケット', 22, RED, 'la')
label(d, (X(WIN[0] + 0.4), Y(141.6)), 'ケーブルは西へ', 20, RED, 'la')
label(d, (X(ENC[0] + r + 0.6), Y(ENC[1] + 4.6)), 'つまみ ø14 以下', 22, RED, 'la')
label(d, (X(ENC[0] + 1.1), Y((Y_S + ENC[1]) / 2)), '7.6', 22, INK, 'lm')
label(d, (X(SW3[0]), Y(EDGE[1] - 5.6)), 'リセット（横から押す）', 22, RED, 'mm')
label(d, (X((J5[0] + J5[2]) / 2), Y(EDGE[1] - 5.6)), 'USB ケーブル', 22, RED, 'mm')
label(d, (X((CN[0] + CN[2]) / 2), Y(CN[1] - 1.4)), '電源の切替ジャンパ', 22, RED, 'mm')
out.convert('RGB').save(out_plan)
print('plan view', out.size, out_plan)

# ================================================================== side view (seen from the east: north is on the right)
S2 = 26.0
Y0, Y1, Z0, Z1 = 120.0, 160.5, -6.0, 31.0
ML, MR = 470, 250                                    # margins for the height scale and the labels
W2, H2 = int((Y1 - Y0) * S2) + ML + MR, int((Z1 - Z0) * S2) + 40
im2 = Image.new('RGB', (W2, H2), (255, 255, 255))
d = ImageDraw.Draw(im2)
U = lambda y: ML + (Y1 - y) * S2                     # north on the right
V = lambda z: 20 + (Z1 - z) * S2
rect = lambda y0, y1, z0, z1: (U(y1), V(z1), U(y0), V(z0))
GREY, LIGHT = (95, 95, 100), (205, 205, 210)


def part(y0, y1, z0, z1, fill, outline=INK, far=False, width=2):
    if far:                                           # a part that stands at another x: outline only, dashed
        dashed(d, [(U(y0), V(z0)), (U(y0), V(z1)), (U(y1), V(z1)), (U(y1), V(z0)), (U(y0), V(z0))], outline, width=2, dash=8, gap=6)
    else:
        d.rectangle(rect(y0, y1, z0, z1), fill=fill, outline=outline, width=width)


# height scale at the far left
d.line((70, V(0), 70, V(30)), fill=GREY, width=2)
for z in range(0, 31, 5):
    d.line((62, V(z), 70, V(z)), fill=GREY, width=2)
    label(d, (56, V(z)), '%d' % z, 20, GREY, 'rm', box=False)
label(d, (78, V(30.0)), 'mm（主基板の上面から）', 18, GREY, 'lm', box=False)
part(EDGE[1], Y1, -T_PCB, 0, (60, 110, 70))                                         # main board
part(SW3[1] - 1.25, SW3[1] + 1.25, 0, 1.2, LIGHT)                                   # reset switch, plunger over the edge
part(SW3[1] - 1.95, SW3[1] - 1.25, 0.2, 1.0, (60, 60, 60))
part(135.1, 139.3, 0, 1.45, LIGHT)                                                  # comparators
part(J2_1[1] - 1.27, J2_1[1] + 1.27, 0, H_INS, (45, 45, 48))                        # J2 header and its socket
part(J2_1[1] - 1.27, J2_1[1] + 1.27, H_INS, H_SHIELD, (70, 70, 75))
part(EDGE[1], Y_S, H_SHIELD, H_SHIELD + T_PCB, BLUE)                                # display board
part(EDGE[1] + 0.5, 139.6, H_SHIELD + T_PCB, H_SHIELD + T_PCB + 1.6, (150, 185, 235), outline=BLUE)   # a display 1.6 mm thick
part(144.74, 156.46, 0, H_ENC_BODY, LIGHT)                                          # encoder
part(ENC[1] - 3.5, ENC[1] + 3.5, H_ENC_BODY, H_BUSH, LIGHT)
part(ENC[1] - 3.0, ENC[1] + 3.0, H_BUSH, H_SHAFT, (235, 235, 238))
name, od, hk, zk = KNOBS[0]
part(ENC[1] - od / 2, ENC[1] + od / 2, zk, zk + hk, (120, 120, 126))
dashed(d, [(U(ENC[1] - KNOB_MAX / 2), V(H_SHIELD - 0.6)), (U(ENC[1] - KNOB_MAX / 2), V(zk + hk + 1.0))], RED, width=3, dash=9, gap=6)
part(hy - 2.75, hy + 2.75, 0, H_SHIELD, None, outline=BLUE, far=True)               # spacer on the mounting hole
part(STDC_SOCKET[1], STDC_SOCKET[3], H_INS, H_STDC, None, outline=RED, far=True)    # STDC14 cable socket
part(EDGE[1] - 4.0, EDGE[1] - 0.2, 1.65 - 3.25, 1.65 + 3.25, None, outline=RED, far=True)   # overmould of a USB-C plug
# labels on the left: the encoder and the knob
xl = U(ENC[1] + od / 2) - 14
for z, text in ((H_SHAFT, '軸の先端 24.5'), (zk, 'つまみの下端 14.9'), (H_BUSH, '軸受けの上端 11.5'), (H_ENC_BODY, '本体の上面 4.5')):
    d.line((xl - 40, V(z), xl + 8, V(z)), fill=INK, width=2)
    label(d, (xl - 46, V(z)), text, 20, INK, 'rm', box=False)
label(d, (xl - 46, V(zk) + 26), '（押すと 12.9〜13.9）', 18, INK, 'rm', box=False)
label(d, (U(ENC[1]), V(zk + hk) - 16), 'つまみ ' + name, 20, INK, 'mm', box=False)
label(d, (U(ENC[1]), V(2.2)), 'エンコーダ', 20, GREY, 'mm', box=False)
# labels on the right: the display board
xr = U(EDGE[1]) + 8
for z, text in ((H_SHIELD + T_PCB, '上面 12.6'), (H_SHIELD, '下面 11.0')):
    d.line((xr, V(z), xr + 34, V(z)), fill=BLUE, width=2)
    label(d, (xr + 40, V(z)), text, 20, BLUE, 'lm', box=False)
label(d, (U(132.8), V(H_SHIELD + T_PCB + 1.6) - 16), '表示器（例: 厚さ 1.6）', 20, BLUE, 'mm', box=False)
label(d, (U(134.0), V(H_SHIELD + 0.8)), '表示シールド', 20, (255, 255, 255), 'mm', box=False)
label(d, (U(hy), V(6.6)), 'M3', 20, BLUE, 'mm', box=False)
label(d, (U(hy), V(5.4)), 'スペーサ', 20, BLUE, 'mm', box=False)
label(d, (U(137.0), V(6.3)), 'STDC14 の', 19, RED, 'mm', box=False)
label(d, (U(137.0), V(5.2)), 'ソケット', 19, RED, 'mm', box=False)
label(d, (U(137.0), V(4.1)), '上端 7.6', 19, RED, 'mm', box=False)
label(d, (U(EDGE[1] - 2.1), V(1.65 + 3.25) - 42), 'USB の', 19, RED, 'mm', box=False)
label(d, (U(EDGE[1] - 2.1), V(1.65 + 3.25) - 18), 'プラグ', 19, RED, 'mm', box=False)
arrow(d, (U(EDGE[1] - 3.6), V(0.6)), (U(SW3[1] - 2.2), V(0.6)), RED, width=3, head=10)
label(d, (U(ENC[1] - KNOB_MAX / 2) + 10, V(22.5)), 'つまみの限界 ø14', 20, RED, 'la', box=False)
label(d, (U(ENC[1] - KNOB_MAX / 2) + 10, V(21.3)), 'シールドの南辺まで 0.6', 18, RED, 'la', box=False)
# labels under the board
label(d, (U(155.5), V(-3.0)), '主基板', 20, GREY, 'mm', box=False)
label(d, (U(J2_1[1]), V(-3.0)), 'J2 とソケット', 20, GREY, 'mm', box=False)
label(d, (U(137.2), V(-4.5)), 'コンパレータ 1.45', 20, GREY, 'mm', box=False)
label(d, (U(SW3[1] + 1.0), V(-3.0)), 'リセット 1.2', 20, GREY, 'mm', box=False)
label(d, (U(Y1), V(Z1) + 2), '南', 22, GREY, 'la', box=False)
label(d, (U(EDGE[1]), V(Z1) + 2), '北（上辺）', 22, GREY, 'ra', box=False)
im2.save(out_side)
print('side view', im2.size, out_side)

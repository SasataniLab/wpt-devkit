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
J2P = {str(n): pad_xy(main, 'J2', str(n)) for n in range(1, 13)}
JC = (sum(p[0] for p in J2P.values()) / 12, sum(p[1] for p in J2P.values()) / 12)
# the socket is a surface-mount part: its lands lie 1.25 mm outside the pins, at the same place along the row
for n in range(1, 13):
    a, e = pad_xy(disp, 'J1', str(n)), J2P[str(n)]
    assert abs(a[0] - e[0]) < 0.01 and abs(abs(a[1] - JC[1]) - abs(e[1] - JC[1]) - 1.25) < 0.01 and (a[1] - JC[1]) * (e[1] - JC[1]) > 0, (n, a, e)
J3_1, J3_14 = pad_xy(main, 'J3', '1'), pad_xy(main, 'J3', '14')
SW3 = pos(main, 'SW3')
SW4 = pos(main, 'SW4')                                               # BOOT0, the same switch 5.75 mm east of the reset switch
ENC = (pos(main, 'SW1')[0] + 7.5, pos(main, 'SW1')[1] + 2.5)       # shaft axis of the EC11E footprint
J5 = court(main, 'J5')
CN = court(main, 'CN208')                                            # CN209 / CN210 went with revision 8 of the transmitter board
TP = {r: pos(main, r) for r in ('TP301', 'TP302', 'TP303', 'TP304', 'TP214', 'TP215', 'TP224', 'TP225')}
assert (ENC, SW3) == ((167.9, 150.6), (162.0, 126.25)), (ENC, SW3)
inside = lambda p: poly.Contains(pcbnew.VECTOR2I(int(p[0] * MM), int(p[1] * MM)))
FREE = ('TP301', 'TP302', 'TP303', 'TP214', 'TP215', 'TP224', 'TP225')
for r in FREE:
    assert not inside(TP[r]), r + ' is under the display board'
assert inside(TP['TP304'])                                            # the fault input: a digital check point
assert not inside(SW3) and OY0 > SW3[1] + 1.25, 'the reset button is under the display board'
assert not inside(SW4) and OY0 > SW4[1] + 1.25, 'the BOOT0 button is under the display board'

# ---- not in the board files (mm). Sources: Samtec catalogue pages F-226 (SSM, socket 7.37 high) and FFSD / print
# FTSH-1XX-XX-XXX-D-XXX-XX sheet 3; Alps EC11E catalogue (update 2510), drawing No. 3; GCT USB4105 drawing (3.31 high) and
# the USB Type-C plug overmould limit (12.35 x 6.5); Wuerth WR-PHD 61301221121 (insulator 2.54);
# panel drawings N096-1608TBBIG11-H13 / MDT0096A2IS-SPI (13.5 x 27.95 x 1.5)
H_INS, H_SOCKET, T_PCB = 2.54, 7.37, 1.6
H_DISP = H_INS + H_SOCKET                 # underside of the display board: 9.91
MOD_W, MOD_L, MOD_T, TAPE = 13.5, 27.95, 1.5, 0.3
AA = (10.8, 21.7, 1.7)                    # active area and its distance from the end opposite to the tail
H_STDC = 7.59
STDC_SOCKET = (J3_1[0] + 0.635 - 1.525 - 1.02, (J3_1[1] + J3_14[1]) / 2 - 13.08 / 2, J3_1[0] + 0.635 + 1.525, (J3_1[1] + J3_14[1]) / 2 + 13.08 / 2)
H_ENC_BODY, H_BUSH, H_SHAFT = 4.5, 11.5, 24.5
KNOB_MAX = 14.0
KNOB = ('ø10.8 × 13.5', 10.8, 13.5, H_SHAFT - 9.6)
H_USB = 3.31
H_HDR = 2.54 + 6.1                        # the 5 V headers: insulator and pins
H_SOT23 = 1.1
MODULE = (DS[0] - MOD_L / 2, DS[1] - MOD_W / 2, DS[0] + MOD_L / 2, DS[1] + MOD_W / 2)          # lying: long side along x, tail at the east end
ACTIVE = (MODULE[0] + AA[2], DS[1] - AA[0] / 2, MODULE[0] + AA[2] + AA[1], DS[1] + AA[0] / 2)

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

WIN = (134.0, 112.5, 228.0, 184.0)       # window in board mm; the margins take the labels
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
for p in J2P.values():                                                                  # the twelve pins of J2 under the board
    d.rectangle((X(p[0] - 0.45), Y(p[1] - 0.45), X(p[0] + 0.45), Y(p[1] + 0.45)), outline=BLUE + (255,), width=3)
for r in FREE:
    d.ellipse((X(TP[r][0] - 1.0), Y(TP[r][1] - 1.0), X(TP[r][0] + 1.0), Y(TP[r][1] + 1.0)), outline=GREEN + (255,), width=5)
d.ellipse((X(TP['TP304'][0] - 1.0), Y(TP['TP304'][1] - 1.0), X(TP['TP304'][0] + 1.0), Y(TP['TP304'][1] + 1.0)), outline=ORANGE + (255,), width=5)
d.rectangle(box(STDC_SOCKET), outline=GREEN + (255,), width=4, fill=GREEN + (28,))
arrow(d, (X(STDC_SOCKET[0]), Y(139.6)), (X(STDC_SOCKET[0] - 5.5), Y(139.6)), GREEN + (255,))
d.rectangle(box(CN), outline=GREEN + (255,), width=4, fill=GREEN + (28,))
rk = KNOB_MAX / 2
dashed(d, [(X(ENC[0] + rk * math.cos(t / 30 * math.pi)), Y(ENC[1] + rk * math.sin(t / 30 * math.pi))) for t in range(61)], RED + (255,), width=4, dash=9, gap=6)
arrow(d, (X(SW3[0]), Y(EDGE[1] - 4.4)), (X(SW3[0]), Y(EDGE[1] - 0.9)), GREEN + (255,))
arrow(d, (X(SW4[0]), Y(EDGE[1] - 4.4)), (X(SW4[0]), Y(EDGE[1] - 0.9)), GREEN + (255,))
ux = (J5[0] + J5[2]) / 2
arrow(d, (X(ux), Y(EDGE[1] - 4.4)), (X(ux), Y(EDGE[1] - 0.3)), GREEN + (255,))
# the dimension from the board to the shaft axis
d.line((X(ENC[0]), Y(OY1), X(ENC[0]), Y(ENC[1])), fill=INK + (255,), width=3)
for yy in (OY1, ENC[1]):
    d.line((X(ENC[0] - 0.9), Y(yy), X(ENC[0] + 0.9), Y(yy)), fill=INK + (255,), width=3)
lead = lambda a, e, col: d.line((P(a), P(e)), fill=col + (255,), width=3)
for r in ('TP303', 'TP302', 'TP301'):
    a = math.atan2(TP[r][1] - 172.0, TP[r][0] - 142.5)
    lead((146.2, 172.0), (TP[r][0] - 1.1 * math.cos(a), TP[r][1] - 1.1 * math.sin(a)), GREEN)
lead((157.0, 118.6), (TP['TP304'][0] - 0.6, TP['TP304'][1] - 0.9), ORANGE)
lead((214.0, 151.2), (TP['TP224'][0] + 0.3, TP['TP224'][1] + 1.0), GREEN)
lead((214.0, 151.2), (TP['TP225'][0], TP['TP225'][1] + 1.0), GREEN)
lead((214.0, 157.0), (TP['TP215'][0] + 1.0, TP['TP215'][1] + 0.4), GREEN)
lead((214.0, 157.0), (TP['TP214'][0] + 1.0, TP['TP214'][1] + 0.2), GREEN)
out = Image.alpha_composite(canvas.convert('RGBA'), ov)
d = ImageDraw.Draw(out)
label(d, (X(OX1 + 0.8), Y(OY0 - 1.4)), '表示基板（%.1f × %.1f mm、%.1f mm 上）' % (OX1 - OX0, OY1 - OY0, H_DISP), 22, BLUE, 'lb')
label(d, (X((ACTIVE[0] + ACTIVE[2]) / 2), Y(DS[1] - 3.9)), '表示 0.96 型', 24, (20, 40, 110), 'mm', box=False)
label(d, (X((ACTIVE[0] + ACTIVE[2]) / 2), Y(DS[1] + 3.9)), '160 × 80', 22, (20, 40, 110), 'mm', box=False)
label(d, (X(WIN[0] + 0.5), Y(172.0)), 'アナログの確認点 VTH・B・A：', 22, GREEN, 'lb')
label(d, (X(WIN[0] + 0.5), Y(174.4)), '隠れない', 22, GREEN, 'lb')
label(d, (X(157.0), Y(117.4)), '隠れる確認点：FLT3（ディジタル）', 20, ORANGE, 'mb')
label(d, (X(SW3[0] - 4.0), Y(EDGE[1] - 5.8)), 'リセット', 22, GREEN, 'mm')
label(d, (X(SW4[0] + 3.5), Y(EDGE[1] - 5.8)), 'BOOT0', 22, GREEN, 'mm')
label(d, (X(ux), Y(EDGE[1] - 5.8)), 'USB（付けたまま挿せる）', 22, GREEN, 'mm')
label(d, (X(WIN[0] + 0.5), Y(135.0)), 'STDC14 のソケット', 22, GREEN, 'la')
label(d, (X(WIN[0] + 0.5), Y(140.6)), 'ケーブルは西へ', 20, GREEN, 'la')
label(d, (X((CN[0] + CN[2]) / 2 - 1.0), Y(CN[1] - 0.4)), '5 V のヘッダ：使える', 22, GREEN, 'mb')    # above it: the board's name stands to the east
label(d, (X(214.2), Y(152.6)), '+3V3・GND の確認点', 20, GREEN, 'mm')
label(d, (X(214.2), Y(158.4)), '（4 つとも見える）', 20, GREEN, 'mm')
label(d, (X(ENC[0] - rk - 0.5), Y(ENC[1] + 5.0)), 'つまみ ø14 以下', 22, RED, 'ra')
label(d, (X(ENC[0] + 1.1), Y((OY1 + ENC[1]) / 2)), '%.1f' % (ENC[1] - OY1), 22, INK, 'lm')
label(d, (X(JC[0]), Y(OY1 + 1.5)), 'J2（2 × 6）の真上にソケット', 20, BLUE, 'mm')
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


def part(x0, x1, z0, z1, fill, outline=INK, width=2):
    d.rectangle(rect(x0, x1, z0, z1), fill=fill, outline=outline, width=width)


part(EDGE[0], EDGE[2], -T_PCB, 0, (60, 110, 70))                                        # transmitter board
part(STDC_SOCKET[0], STDC_SOCKET[2], 0, H_STDC, LIGHT)                                  # STDC14 with its cable socket
part(J5[0], J5[2], 0, H_USB, LIGHT)                                                     # USB-C receptacle (at the north edge)
part(CN[0], CN[2], 0, H_HDR, LIGHT)                                                     # 5 V headers
jx0, jx1 = min(p[0] for p in J2P.values()) - 1.27, max(p[0] for p in J2P.values()) + 1.27
part(jx0, jx1, 0, H_INS, (40, 40, 44))                                                  # J2: insulator of the header
part(jx0, jx1, H_INS, H_DISP, (70, 70, 78))                                             # the socket of the display board
part(OX0, OX1, H_DISP, H_DISP + T_PCB, (50, 90, 170))                                   # display board
part(MODULE[0], MODULE[2], H_DISP + T_PCB + TAPE, H_DISP + T_PCB + TAPE + MOD_T, (30, 34, 48))
part(186.0, 191.0, H_DISP - H_SOT23, H_DISP, LIGHT)                                     # small parts under the display board
part(ENC[0] - 6.0, ENC[0] + 6.0, 0, H_ENC_BODY, LIGHT)                                  # encoder (nearer to the viewer than the display board): body, bushing, shaft, knob
part(ENC[0] - 3.5, ENC[0] + 3.5, H_ENC_BODY, H_BUSH, LIGHT)
part(ENC[0] - 3.0, ENC[0] + 3.0, H_BUSH, H_SHAFT, (235, 235, 238))
part(ENC[0] - KNOB[1] / 2, ENC[0] + KNOB[1] / 2, KNOB[3], KNOB[3] + KNOB[2], (250, 225, 225), outline=RED, width=3)
top = H_DISP + T_PCB + TAPE + MOD_T
for z, txt in ((H_DISP, '%.1f' % H_DISP), (top, '%.1f' % top)):
    d.line((U(OX1 + 1.0), V(z), U(203.5), V(z)), fill=GREY, width=2)
    label(d, (U(204.0), V(z)), txt + ' mm', 22, INK, 'lm', box=False)
d.line((U(EDGE[0] - 3.0), V(0), U(EDGE[2] + 2.0), V(0)), fill=GREY, width=1)
label(d, (U((OX0 + OX1) / 2), V(top + 1.6)), '表示基板と表示器', 24, BLUE, 'mb', box=False)
label(d, (U(ENC[0]), V(KNOB[3] + KNOB[2] + 1.2)), 'つまみ %s（例）' % KNOB[0], 22, RED, 'mb', box=False)
label(d, (U(STDC_SOCKET[0] - 0.5), V(H_STDC + 1.0)), 'STDC14 %.1f' % H_STDC, 20, INK, 'mb', box=False)
label(d, (U((J5[0] + J5[2]) / 2), V(H_USB + 0.8)), 'USB %.1f（北の縁、表示基板の外）' % H_USB, 20, INK, 'mb', box=False)
label(d, (U(CN[2] + 0.6), V(H_HDR / 2)), '5 V ヘッダ %.1f' % H_HDR, 20, INK, 'lm', box=False)
label(d, (U((jx0 + jx1) / 2), V(H_DISP / 2)), 'J2 + ソケット', 20, (255, 255, 255), 'mm', box=False)
label(d, (10, V(0)), '基板面 0', 20, GREY, 'lm', box=False)
label(d, (10, V(Z0) - 30), '南から見た高さ（mm）。奥行きの違う部品を重ねて描いてある（つまみは表示基板より手前）', 20, GREY, 'lb', box=False)
im2.save(out_side)
print('side view', im2.size, out_side)

# ================================================================== the display board itself, both sides
tiles = []
for side, title in (('top', '表（表示器の側）'), ('bottom', '裏（送電基板の側）')):
    rg, mk = render(disp_path, side, 1900, 1000)
    ys, xs = np.where(mk)
    t = Image.alpha_composite(Image.new('RGBA', rg.size, (255, 255, 255, 255)), rg).convert('RGB').crop((xs.min() - 30, ys.min() - 70, xs.max() + 30, ys.max() + 30))
    dd = ImageDraw.Draw(t, 'RGBA')
    s = (xs.max() - xs.min()) / (OX1 - OX0)
    if side == 'top':                                                                   # the module, drawn in
        bx = lambda r: (30 + (r[0] - OX0) * s, 70 + (r[1] - OY0) * s, 30 + (r[2] - OX0) * s, 70 + (r[3] - OY0) * s)
        dd.rectangle(bx(MODULE), fill=(30, 34, 48, 110), outline=(20, 24, 40, 255), width=3)
        dd.rectangle(bx(ACTIVE), outline=(240, 240, 250, 255), width=2)
    label(dd, (30, 14), title, 30, INK, 'lt', box=False)
    tiles.append(t)
Wb = max(t.size[0] for t in tiles)
board = Image.new('RGB', (Wb, sum(t.size[1] for t in tiles) + 20), (255, 255, 255))
y = 0
for t in tiles:
    board.paste(t, (0, y))
    y += t.size[1] + 20
board.save(out_board)
print('board', board.size, out_board)

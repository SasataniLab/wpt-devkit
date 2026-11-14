#!/usr/bin/env python3
"""Pin functions of the pin headers on the top silkscreen. usage: silklabel.py BOARD_IN BOARD_OUT

Without these one needs the schematic open to plug anything onto J2 / J3 / J4 / J301. Text is 0.8 mm high with
a 0.15 mm stroke. The script refuses to run on a board that already carries these texts.
  J301 (experiment header, pin 1 at the east end): two lines in the strip north of it
  J2   (display / add-on, pin 1 at the west end): two lines between the header rows
  J3   (SWD): one word beside every pin
  J4   (UART): one word beside every pin, turned by 90 degrees (between J4 and J1);  J1 (BOOT0 jumper): its name beside it
"""
import sys

import pcbnew

MM = 1e6
src, dst = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
V = lambda x, y: pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
# (text, x, y, justify) - x, y is the left end / centre / right end of the line, on its middle height
L, C, Rr = pcbnew.GR_TEXT_H_ALIGN_LEFT, pcbnew.GR_TEXT_H_ALIGN_CENTER, pcbnew.GR_TEXT_H_ALIGN_RIGHT
TEXTS = [
    ('J301  1:VSW_A  2:GND  3:VSW_B  4:GND  5:ZVS_A', 188.9, 127.3, Rr),
    ('6:ZVS_B  7:FLT3  8:FLT4  9:+3V3  10:GND', 188.9, 128.6, Rr),
    ('J2  1:GND 2:+3V3 3:SCK 4:MISO 5:MOSI 6:ADC', 157.6, 138.50, L),
    ('7:CS 8:DC 9:RST 10:IO 11:+3V3 12:GND', 157.6, 139.55, L),
    ('RST', 154.6, 135.20, L), ('CLK', 154.6, 137.74, L), ('DIO', 154.6, 140.28, L), ('3V3', 154.6, 142.82, L), ('GND', 154.6, 145.36, L),
    ('RX', 154.4, 164.00, C, 90), ('TX', 154.4, 166.54, C, 90), ('3V3', 154.4, 169.08, C, 90), ('GND', 154.4, 171.62, C, 90),
    ('BOOT0', 158.1, 164.65, L),
]
mine = {(t[0], round(t[1], 2), round(t[2], 2)) for t in TEXTS}
old = [d for d in b.GetDrawings() if d.GetClass() == 'PCB_TEXT' and d.GetLayer() == pcbnew.F_SilkS
       and (d.GetText(), round(d.GetPosition().x / MM, 2), round(d.GetPosition().y / MM, 2)) in mine]
if old:
    raise SystemExit('labels are already on the board: start from a board without them')
for txt, x, y, just, *rot in TEXTS:
    t = pcbnew.PCB_TEXT(b)
    t.SetText(txt)
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(int(0.8 * MM), int(0.8 * MM)))
    t.SetTextThickness(int(0.15 * MM))
    t.SetHorizJustify(just)
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    t.SetPosition(V(x, y))
    if rot:
        t.SetTextAngleDegrees(rot[0])
    b.Add(t)
    bb = t.GetBoundingBox()
    print('%-48s x %.2f..%.2f  y %.2f..%.2f' % (txt, bb.GetLeft() / MM, bb.GetRight() / MM, bb.GetTop() / MM, bb.GetBottom() / MM))
pcbnew.SaveBoard(dst, b)
print('written', dst)

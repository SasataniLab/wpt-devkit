#!/usr/bin/env python3
"""Third revision: silkscreen notes that the header signals are 3.3 V only. usage: silknote.py BOARD_IN BOARD_OUT

The MCU pins behind J4 pin 1 (PC5), J301 pins 7 / 8 (PB10 / PB11) and the SPI / DC / RST pins of J2 are "TT_a" inputs:
3.6 V at most, not 5 V tolerant, and without a clamp diode to the supply. A 5 V USB-UART adapter on J4 would exceed the
rating. Two texts say so: one under the J301 legend for the two headers at the top, one beside the UART header.
"""
import shutil
import sys

import pcbnew

MM = 1e6
src, dst = sys.argv[1:3]
if src != dst:
    shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)
have = {d.GetText() for d in b.GetDrawings() if d.GetClass() == 'PCB_TEXT'}
n = 0
for txt, x, y in (('J2 / J301: 3.3 V MAX', 158.30, 129.95), ('J4: 3.3 V MAX', 160.20, 166.20)):
    if txt in have:
        continue
    t = pcbnew.PCB_TEXT(b)
    t.SetText(txt)
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(int(0.8 * MM), int(0.8 * MM)))
    t.SetTextThickness(int(0.15 * MM))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    t.SetPosition(pcbnew.VECTOR2I(int(x * MM), int(y * MM)))
    b.Add(t)
    bb = t.GetBoundingBox()
    print('%-30s box (%.1f, %.1f)-(%.1f, %.1f)' % (txt, bb.GetLeft() / MM, bb.GetTop() / MM, bb.GetRight() / MM, bb.GetBottom() / MM))
    n += 1
pcbnew.SaveBoard(dst, b)
print('texts added:', n)

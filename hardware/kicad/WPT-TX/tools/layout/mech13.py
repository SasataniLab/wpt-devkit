#!/usr/bin/env python3
"""Revision 7, part 3: the silkscreen follows. usage: mech13.py BOARD_IN BOARD_OUT

  J2            the four lines of the old pin table go; every pin gets its signal name beside it (outer row above,
                inner row below), and the note "J2: 3.3 V MAX" moves to the header. The reference "J2" is part of that
                note and is hidden.
  test pads     the names of TP301 / TP302 / TP303 ("A", "B", "VTH") move with the pads; "FLT3" moves with TP304.
                Their references stay hidden, as before.
  comparators   the two lines that explained the top strip go; two lines on the back side beside the comparators say
                which leg reports to which event input (it changed with this revision).
"""
import shutil
import sys

import pcbnew

import newfp

src, dst = sys.argv[1:3]
shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)

GONE = ('J2 1:GND 2:+3V3 3:SCK', '4:MISO 5:MOSI 6:ADC', '7:CS 8:DC 9:RST 10:IO', '11:+3V3 12:GND', 'J2: 3.3 V MAX', 'FLT3', 'VTH', 'B', 'A',
        'TP301-304: VSW_A VSW_B VTH FLT3', 'U308: leg A > EEV1  U309: leg B > EEV2')
old = [d for d in b.GetDrawings() if d.GetClass() == 'PCB_TEXT' and d.GetText() in GONE and 'Silk' in b.GetLayerName(d.GetLayer())]
assert sorted(d.GetText() for d in old) == sorted(GONE), sorted(set(GONE) - {d.GetText() for d in old})

X0, YN, YS, P = 171.0, 133.88, 136.42, 2.54
for k, (outer, inner) in enumerate((('3V3', 'GND'), ('MISO', 'MOSI'), ('DC', 'SCK'), ('CS', 'RST'), ('IO', 'ADC'), ('GND', '3V3'))):
    for name, y in ((outer, YN - 2.23), (inner, YS + 2.23)):                           # clear of the outline of the header
        t = newfp.text(b, name, X0 + k * P, y, thick=0.13, justify='center')
        t.SetTextSize(pcbnew.VECTOR2I(int(0.55e6), int(0.8e6)))                         # full height (board rule), narrow: four letters per 2.54 mm
newfp.text(b, 'J2: 3.3 V MAX', X0 + 2.5 * P, YN - 3.5, justify='center')
newfp.text(b, 'FLT3', 168.24, 137.75, justify='center')
newfp.text(b, 'A', 187.6, 178.65, justify='center')
newfp.text(b, 'B', 191.5, 165.55, justify='center')
newfp.text(b, 'VTH', 178.5, 168.0, justify='center')
newfp.text(b, 'U308: leg A > EEV2', 179.5, 175.0, layer='B.SilkS', justify='center')
newfp.text(b, 'U309: leg B > EEV1', 179.5, 176.1, layer='B.SilkS', justify='center')
for ref in ('J2', 'TP301', 'TP302', 'TP303', 'TP304'):
    b.FindFootprintByReference(ref).Reference().SetVisible(False)
for d in old:                                     # removals last: after a Remove() pcbnew hands out footprints it cannot use
    b.Remove(d)
pcbnew.SaveBoard(dst, b)

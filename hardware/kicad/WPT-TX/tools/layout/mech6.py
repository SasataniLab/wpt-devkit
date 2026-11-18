#!/usr/bin/env python3
"""Third revision: the frame lugs of the encoder SW1 to ground. usage: mech6.py BOARD_IN BOARD_OUT

The two slotted pads "MP" of SW1 (the lugs of the metal frame that carries the shaft) had no net. The schematic now
ties them to GND (edit_sch6.py); here the pads get the net. They sit in the ground pours of both outer layers and in
the ground plane, so no track is needed: the zones connect them when they are refilled.
"""
import shutil
import sys

import pcbnew

src, dst = sys.argv[1:3]
if src != dst:
    shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)
gnd = b.FindNet('GND')
n = 0
for p in b.FindFootprintByReference('SW1').Pads():
    if p.GetNumber() == 'MP':
        assert p.GetNetname() in ('', 'GND'), p.GetNetname()
        p.SetNet(gnd)
        n += 1
assert n == 2, n
pcbnew.SaveBoard(dst, b)
print('SW1 MP pads on GND:', n)

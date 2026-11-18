#!/usr/bin/env python3
"""Schematic edit of 2026-11-14, fourth revision, part 3: one duplicated power-symbol reference
(run inside the project directory hardware/kicad/WPT-TX).

The ground symbol added to the encoder frame in edit_sch6.py took its number from the root sheet alone and got
#PWR0370, which MCU.kicad_sch already uses. ERC does not complain, but `kicad-cli sch export netlist` prints
"schematic has annotation errors". The one on the root sheet gets the next free number. Nothing electrical changes.
"""
import glob
import re
import sys

FN = 'WPT-01-TRANSMITTER.kicad_sch'
t = open(FN, encoding='utf-8').read()
if t.count('"#PWR0370"') == 0:
    sys.exit('already applied')
assert t.count('(property "Reference" "#PWR0370"') == 1 and t.count('(reference "#PWR0370")') == 1
nums = []
for fn in glob.glob('*.kicad_sch'):
    nums += [int(n) for n in re.findall(r'"#PWR0*(\d+)"', open(fn, encoding='utf-8').read())]
new = '#PWR0%d' % (max(nums) + 1)
t = t.replace('(property "Reference" "#PWR0370"', '(property "Reference" "%s"' % new).replace('(reference "#PWR0370")', '(reference "%s")' % new)
open(FN, 'w', encoding='utf-8').write(t)
print('root sheet: #PWR0370 ->', new)

#!/usr/bin/env python3
"""Schematic edit of 2026-11-14, third revision, part 2 (run inside the project directory hardware/kicad/WPT-TX).

The switch-node sense path to the MCU comparators is fitted in the HRTIM variant:
    R343, R344   series resistors between the divider taps (VSWA_SENSE / VSWB_SENSE) and the comparator pins
                 PA1 / PC1 (nets VSWA_CMP / VSWB_CMP): 1 k not fitted  ->  100 ohm, fitted in variant HRTIM.
                 Without them the comparator pins are not connected to anything.
    C338, C339   1 pF across the 15 k upper divider resistors: not fitted -> fitted in variant HRTIM.
                 The tap carries about 15 pF (MCU pin, 45 mm of track, header pin); 15 k x 1 pF = 1 k x 15 pF makes
                 the divider flat instead of a 14 ns low-pass.
The Legacy variant keeps all four unfitted (base state), as before.
"""
import re
import sys

FN = 'WPT-01-TRANSMITTER-TX.kicad_sch'
t = open(FN, encoding='utf-8').read()


def block(t, ref):
    i = t.index('(property "Reference" "%s"' % ref)
    j = t.rfind('\n\t(symbol\n', 0, i) + 1
    d = 0
    for k in range(j, len(t)):
        if t[k] == '(':
            d += 1
        elif t[k] == ')':
            d -= 1
            if d == 0:
                return j, k + 1
    raise ValueError(ref)


VARIANT = '\t\t\t\t\t(variant\n\t\t\t\t\t\t(name "HRTIM")\n\t\t\t\t\t\t(dnp no)\n\t\t\t\t\t)\n'
for ref, value, mpn in (('R343', '100R', 'RC0402FR-07100RL'), ('R344', '100R', 'RC0402FR-07100RL'), ('C338', None, None), ('C339', None, None)):
    j, k = block(t, ref)
    b = t[j:k]
    if '(name "HRTIM")' in b:
        sys.exit('already applied (%s)' % ref)
    assert '(dnp yes)' in b, ref
    if value:
        b, n = re.subn(r'\(property "Value" "1k"', '(property "Value" "%s"' % value, b)
        assert n == 1, ref
        b, n = re.subn(r'\(property "Manufacturer Part Number" "RC0402FR-071KL"', '(property "Manufacturer Part Number" "%s"' % mpn, b)
        assert n == 1, ref
    m = re.search(r'\(reference "%s"\)\n\t\t\t\t\t\(unit 1\)\n' % ref, b)
    assert m, ref
    b = b[:m.end()] + VARIANT + b[m.end():]
    t = t[:j] + b + t[k:]
assert t.count('(') == t.count(')')
open(FN, 'w', encoding='utf-8').write(t)
print('applied')

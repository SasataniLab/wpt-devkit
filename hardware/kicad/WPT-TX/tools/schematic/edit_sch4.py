#!/usr/bin/env python3
"""Schematic edit of 2026-11-14, third revision, part 2 (run inside the project directory hardware/kicad/WPT-TX).

The switch-node sense path to the MCU comparators is fitted in the HRTIM variant:
    R343, R344   series resistors between the divider taps (VSWA_SENSE / VSWB_SENSE) and the comparator pins
                 PA1 / PC1 (nets VSWA_CMP / VSWB_CMP): 1 k not fitted  ->  100 ohm, fitted in variant HRTIM.
                 Without them the comparator pins are not connected to anything.
    C338, C339   across the 15 k upper divider resistors: 1 pF not fitted -> 0.5 pF (+/-0.1 pF), fitted in variant HRTIM.
                 The tap carries 12 to 14 pF with the comparator connected (MCU pin 5 pF, 40 to 60 mm of track, header
                 pin), so exact compensation needs 0.8 to 0.9 pF in total. 0.5 pF plus the stray capacitance of the
                 resistor gives 55 to 75 % of the step at once and never overshoots; 1 pF +/-0.25 pF could overshoot by
                 up to 70 %, which at 36 V on the bus is 3.8 V on a pin that must stay below 3.6 V. The value is a
                 starting point: trim on the bench (0.5 to 1 pF) until the tap follows the switch node without
                 overshoot (docs/stm32-tx/hrtim_timing_control.md, sections 3.2 and 7.5).
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
JOBS = (('R343', '1k', '100R', 'RC0402FR-071KL', 'RC0402FR-07100RL'), ('R344', '1k', '100R', 'RC0402FR-071KL', 'RC0402FR-07100RL'),
        ('C338', '1p', '0.5p', 'GRM1555C1H1R0CA01D', 'GRM1555C1HR50BA01D'), ('C339', '1p', '0.5p', 'GRM1555C1H1R0CA01D', 'GRM1555C1HR50BA01D'))
changed = 0
for ref, old_value, value, old_mpn, mpn in JOBS:
    j, k = block(t, ref)
    b = t[j:k]
    assert '(dnp yes)' in b, ref
    if '(property "Value" "%s"' % old_value in b:
        b = b.replace('(property "Value" "%s"' % old_value, '(property "Value" "%s"' % value, 1)
        b, n = re.subn(re.escape('(property "Manufacturer Part Number" "%s"' % old_mpn), '(property "Manufacturer Part Number" "%s"' % mpn, b)
        assert n == 1, ref
        changed += 1
    assert '(property "Value" "%s"' % value in b, ref
    if '(name "HRTIM")' not in b:
        m = re.search(r'\(reference "%s"\)\n\t\t\t\t\t\(unit 1\)\n' % ref, b)
        assert m, ref
        b = b[:m.end()] + VARIANT + b[m.end():]
        changed += 1
    t = t[:j] + b + t[k:]
if not changed:
    sys.exit('already applied')
assert t.count('(') == t.count(')')
open(FN, 'w', encoding='utf-8').write(t)
print('applied')

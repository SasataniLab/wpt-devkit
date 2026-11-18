#!/usr/bin/env python3
"""Schematic edit of 2026-11-18 (run inside the project directory hardware/kicad/WPT-TX): the default population becomes
the one that is ordered.

Until now the base state of the schematic and of the board was the Legacy build (the 2020 drive from the Si5351) and
the HRTIM build - the one that is ordered - was a variant on top of it. Whatever reads a file without choosing a
variant (the default view in KiCad, a drawing printed from the GUI, PCBWay's plug-in, any third-party BOM tool) saw
the Legacy build: comparators and the links from the MCU to the gate drivers crossed out, the delay networks fitted.

Now:  base state        = HRTIM build
      variant "HRTIM"   = the same (no overrides; the name stays for the export scripts)
      variant "Legacy"  = the fall-back: R305, R307, R315, R318, D305, D306, D311, D312 fitted;
                          R320, R323, R326, R329, R343 - R345, C338 - C345, U308, U309 not fitted
For each of the 25 symbols the base DNP flag takes the value the HRTIM variant had and a Legacy override keeps the old
base value. The project file gets the matching descriptions; a note on the transmitter sheet lists the parts.
The board follows through tools/schematic/pcb_side.py (run by tools/layout/finalize.py).

A second run stops with "already applied".
"""
import re
import sys
import uuid

sys.path.insert(0, __file__.rsplit('/', 1)[0])
import sx

TX, PRO = 'WPT-01-TRANSMITTER-TX.kicad_sch', 'WPT-01-TRANSMITTER.kicad_pro'
s = open(TX, encoding='utf-8').read()
if '(name "HRTIM")' not in s:
    sys.exit('already applied')


def block_at(t, j):
    d = 0
    for k in range(j, len(t)):
        if t[k] == '(':
            d += 1
        elif t[k] == ')':
            d -= 1
            if d == 0:
                return t[j:k + 1]
    raise ValueError('unbalanced')


VAR = re.compile(r'\(variant\n(\t+)\(name "HRTIM"\)\n\t+\(dnp (yes|no)\)\n\t+\)')
out, pos, done = [], 0, {'yes': [], 'no': []}
for m in re.finditer(r'\n\t\(symbol\n', s):
    j = m.start() + 2
    if j < pos:
        continue
    b = block_at(s, j)
    v = VAR.search(b)
    if v:
        base = re.search(r'\n\t\t\(dnp (yes|no)\)', b)                  # the flag of the symbol itself
        assert base and base.start() < v.start() and base.group(1) != v.group(2), b[:200]
        ref = re.search(r'\(property "Reference" "([^"]+)"', b).group(1)
        nb = b[:base.start()] + '\n\t\t(dnp %s)' % v.group(2) + b[base.end():v.start()] \
            + v.group(0).replace('(name "HRTIM")', '(name "Legacy")').replace('(dnp %s)' % v.group(2), '(dnp %s)' % base.group(1)) + b[v.end():]
        assert len(nb) == len(b) + len('Legacy') - len('HRTIM') and nb.count('(variant') == 1
        done[v.group(2)].append(ref)
        b = nb
    out.append(s[pos:j] + b)
    pos = j + len(block_at(s, j))
s = ''.join(out) + s[pos:]
assert '(name "HRTIM")' not in s and s.count('(name "Legacy")') == 25, s.count('(name "Legacy")')
key = lambda r: (re.match(r'[A-Z]+', r).group(0), int(re.search(r'\d+', r).group(0)))
fitted, left_out = sorted(done['no'], key=key), sorted(done['yes'], key=key)
assert len(fitted) == 17 and len(left_out) == 8, (fitted, left_out)

NOTE = ('Populations\nDefault (drawn here, ordered): HRTIM build. The MCU drives the gate drivers through\nR320, R323, R326, R329; '
        'U308 / U309 with C338 .. C345, R343 .. R345 report the switch nodes.\n'
        'Variant "Legacy" (fall-back, the 2020 drive from the Si5351): fit D305, D306, D311, D312,\nR305, R307, R315, R318 and take out '
        'R320, R323, R326, R329 (the 74LVC outputs are 5 V, the MCU\npins take 3.6 V); U308 / U309 and their parts are not needed then.\n'
        'Never fit both sets.')
text = ('(text %s\n\t\t(exclude_from_sim no)\n\t\t(at 25.4 262.89 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)'
        % (sx.quote(NOTE), uuid.uuid4()))                       # quote() escapes the quotation marks and the line breaks
k = s.rindex('\n\t(embedded_fonts') if '\n\t(embedded_fonts' in s else s.rindex('\n)')
for mark in ('\n\t(sheet_instances', '\n\t(symbol_instances'):
    if mark in s:
        k = min(k, s.rindex(mark))
s = s[:k] + '\n\t' + text + s[k:]
assert s.count('(') == s.count(')')
sx.parse(s)
assert [t.a(0) for t in sx.parse(s).kids('text')].count(NOTE) == 1          # the note reads back as written
open(TX, 'w', encoding='utf-8').write(s)

p = open(PRO, encoding='utf-8').read()
OLD_H = '"description": "HRTIM build: R320, R323, R326, R329 fitted; R305, R307, R315, R318, D305, D306, D311, D312 not fitted"'
OLD_L = '"description": "Legacy build (same as the base schematic): R305, R307, R315, R318, D305, D306, D311, D312 fitted; R320, R323, R326, R329 not fitted"'
assert p.count(OLD_H) == 1 and p.count(OLD_L) == 1
p = p.replace(OLD_H, '"description": "HRTIM build (same as the base schematic and board; the population that is ordered): R320, R323, R326, R329, U308, U309 and the sense parts fitted; R305, R307, R315, R318, D305, D306, D311, D312 not fitted"')
p = p.replace(OLD_L, '"description": "Legacy build (fall-back, the 2020 drive from the Si5351): R305, R307, R315, R318, D305, D306, D311, D312 fitted; R320, R323, R326, R329, R343 - R345, C338 - C345, U308, U309 not fitted"')
open(PRO, 'w', encoding='utf-8').write(p)
print('default population is now the HRTIM build')
print('  fitted by default, left out in "Legacy":', ' '.join(fitted))
print('  left out by default, fitted in "Legacy":', ' '.join(left_out))

#!/usr/bin/env python3
"""Schematic edit of 2026-11-18 after the review of revision 8 (run inside the project directory hardware/kicad/WPT-TX):
the BOOT0 jumper becomes a push button.

J1 (1 x 2 pin header between BOOT0 and +3V3) stood on the west edge, 4 mm beside J202, the 36 V input on a header of
the same shape. The free place in the north-west of the board lies under the display board (9.9 mm above), where a
jumper cannot be handled. A side-actuated switch on the board edge can: the same part as the reset switch SW3.

  J1    removed
  SW4   Switch:SW_Push, Omron B3U-3000P-B (as SW3), between BOOT0 and +3V3. R2 (10 k to GND) stays.
        Hold SW4, tap SW3: the MCU starts its system boot loader (USB DFU on J5).
        Drawn mirrored so that pad 2 (the east pad on the board) is BOOT0.
  SW3   the assembly note now names both switches (one BOM line).

A second run stops with "already applied".
"""
import re
import sys
import uuid

sys.path.insert(0, __file__.rsplit('/', 1)[0])
import sx

MCU = 'MCU.kicad_sch'
R = lambda v: round(float(v), 3)
fmt = lambda v: ('%.4f' % v).rstrip('0').rstrip('.')
uid = lambda: str(uuid.uuid4())
PROP = r'\(property "%s" "(?:[^"\\]|\\.)*"'

s = open(MCU, encoding='utf-8').read()
if '(property "Reference" "SW4"' in s:
    sys.exit('already applied')


def symbol(text, ref):
    hit = [n for n in sx.parse(text).kids('symbol') if [p.a(1) for p in n.kids('property') if p.a(0) == 'Reference'] == [ref]]
    assert len(hit) == 1, (ref, len(hit))
    return hit[0]


def cut(text, n):
    lead = '\n\t'
    assert text[n.start - len(lead):n.start] == lead
    return text[:n.start - len(lead)] + text[n.end:]


def prop_block(block, name):
    m = re.search(r'\n\t\t' + PROP % re.escape(name), block)
    assert m, name
    j = m.start() + 3
    d = 0
    for k in range(j, len(block)):
        if block[k] == '(':
            d += 1
        elif block[k] == ')':
            d -= 1
            if d == 0:
                return j, k + 1
    raise ValueError(name)


def setp(block, name, value):
    new, k = re.subn(PROP % re.escape(name), lambda _: '(property "%s" %s' % (name, sx.quote(value)), block, count=1)
    assert k == 1, name
    return new


NOTE = ('SW3, SW4: front of the body on the board edge, plunger towards the outside (it stands 0.7 mm over the edge: no V-cut along the top edge). '
        'Not washable: no-clean process, or fit after washing. B3U-3000P (same switch without the locating boss) is an accepted substitute')
X, Y = 209.55, 134.62                         # pins at (X -/+ 5.08, Y): the left one ends the BOOT0 wire where pin 1 of J1 was

# ---- SW3: the note names both switches
n = symbol(s, 'SW3')
sw3 = n.text(s)
assert '(at 85.09 68.58 270)' in sw3 and sw3.count('(justify right)') == 2
sw3_new = setp(sw3, 'Assembly Note', NOTE)
s = s[:n.start] + sw3_new + s[n.end:]

# ---- SW4: a copy of SW3, horizontal, mirrored (pin 2 on the left), texts below the symbol
b = sw3_new.replace('(at 85.09 68.58 270)', '(at %s %s 0)\n\t\t(mirror y)' % (fmt(X), fmt(Y)), 1)
b = b.replace('(at 85.09 68.58 0)', '(at %s %s 0)' % (fmt(X), fmt(Y)))                    # the hidden fields
for name, y in (('Reference', Y + 2.54), ('Value', Y + 5.08)):
    j, k = prop_block(b, name)
    blk = re.sub(r'\(at [^)]*\)', '(at %s %s 0)' % (fmt(X), fmt(y)), b[j:k], count=1)
    blk, c = re.subn(r'\n\t\t\t\t\(justify right\)', '', blk)
    assert c == 1, name
    b = b[:j] + blk + b[k:]
b = setp(b, 'Value', 'BOOT0')
b = re.sub(r'\(uuid "[^"]+"\)', lambda _: '(uuid "%s")' % uid(), b)
b = b.replace('(property "Reference" "SW3"', '(property "Reference" "SW4"', 1).replace('(reference "SW3")', '(reference "SW4")')
assert b.count('"SW4"') == 2 and '"SW3"' not in b and '(at 85.09' not in b, b.count('"SW4"')

# ---- J1 out, SW4 in, the +3V3 symbol moves from pin 2 of J1 to the right pin of SW4
n = symbol(s, 'J1')
assert '(at 204.47 139.7 90)' in n.text(s)
s = cut(s, n)
pw = [q for q in sx.parse(s).kids('symbol') if q.val('lib_id', '').startswith('power:') and (R(q.kid('at').a(0)), R(q.kid('at').a(1))) == (207.01, 134.62)]
assert len(pw) == 1 and [p.a(1) for p in pw[0].kids('property') if p.a(0) == 'Value'] == ['+3V3'], len(pw)
blk = pw[0].text(s)
blk = re.sub(r'\(at (-?[\d.]+) (-?[\d.]+) (\d+)\)', lambda q: '(at %s %s %s)' % (fmt(float(q.group(1)) + (X + 5.08 - 207.01)), q.group(2), q.group(3)), blk)
s = s[:pw[0].start] + blk + s[pw[0].end:]
k = s.rindex('\n\t(embedded_fonts') if '\n\t(embedded_fonts' in s else s.rindex('\n)')
for mark in ('\n\t(sheet_instances', '\n\t(symbol_instances'):
    if mark in s:
        k = min(k, s.rindex(mark))
s = s[:k] + '\n\t' + b + s[k:]

assert s.count('(') == s.count(')')
sx.parse(s)
open(MCU, 'w', encoding='utf-8').write(s)
print('J1 removed; SW4 (B3U-3000P-B) between BOOT0 and +3V3 at (%s, %s); assembly note of SW3 names both switches' % (fmt(X), fmt(Y)))

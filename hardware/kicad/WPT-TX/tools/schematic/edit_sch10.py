#!/usr/bin/env python3
"""Schematic edit of 2026-11-17, sixth revision (run inside the project directory hardware/kicad/WPT-TX).

  SW3   reset button between NRST and GND, beside C10 (MCU sheet). Omron B3U-3000P-B: side-actuated, 3 x 2.5 mm,
        with a locating boss. On the board it sits at the top edge with the plunger over the edge, so that it can
        still be reached when a display board is plugged onto J2 (footprint: the project-local copy without the
        silkscreen beyond the edge). NRST already has C10 (100 nF) and the pull-up inside the MCU; pressed, the
        switch carries 3.3 V / 40 kohm = 0.08 mA (its minimum load is 10 uA).
  R13   1 kohm between the slide switch SW2 (net HV_SW_STATE) and PB4 (root sheet, at the sheet pin GPIO_SW_MISC2).
        The switch ties the line hard to +3V3 or GND; the resistor limits the current to 3.3 mA should firmware ever
        drive PB4 as an output. The piece between R13 and the pin gets the name of the sheet pin (/MCU/GPIO_SW_MISC2).
  U2    a note for the buyer (field "Assembly Note", it goes into the BOM): STM32G474RET6 was out of stock at the
        franchised distributors on 2026-11-17. Accepted without asking: the same chip in other packing or temperature
        grade (RET6TR, RET3, RET3TR) and STM32G484RET6 (the same device with an AES unit: same LQFP64 pinout and
        alternate functions, same device ID 0x469, same bootloader; docs/stm32-tx/preorder_review.md, section 7).

Each of the three edits is skipped if the schematic already has it.
"""
import glob
import re
import sys
import uuid

uid = lambda: str(uuid.uuid4())
ROOT = 'WPT-01-TRANSMITTER.kicad_sch'
MCU = 'MCU.kicad_sch'
STOCK = '/usr/share/kicad/symbols/Switch.kicad_sym'
t = open(ROOT, encoding='utf-8').read()
m = open(MCU, encoding='utf-8').read()
U2_NOTE = ('U2: STM32G474RET6 was out of stock at the franchised distributors on 2026-11-17. Accepted substitutes, same package '
           'and pinout, no change to the board: STM32G474RET6TR, STM32G474RET3, STM32G474RET3TR, STM32G484RET6. '
           'Ask before using any other part number (STM32G474RBT6 and RCT6 have less flash memory)')
todo = {'R13': '(property "Reference" "R13"' not in t, 'SW3': '(property "Reference" "SW3"' not in m, 'U2 note': U2_NOTE not in m}
if not any(todo.values()):
    sys.exit('already applied')


def block_at(s, j):
    d = 0
    for k in range(j, len(s)):
        if s[k] == '(':
            d += 1
        elif s[k] == ')':
            d -= 1
            if d == 0:
                return s[j:k + 1]
    raise ValueError('unbalanced')


def inst(s, ref):
    i = s.index('(property "Reference" "%s"' % ref)
    j = s.rfind('\n\t(symbol\n', 0, i) + 1
    return j, block_at(s, j)


def fmt(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def prop(b, name, value=None, at=None, just=None):
    """set value, position (x, y, angle) and justification of one property of a placed symbol"""
    mm = re.search(r'\t\t\(property "%s" "(?:[^"\\]|\\.)*"\n.*?\n\t\t\)\n' % re.escape(name), b, re.S)
    assert mm, name
    p = p0 = mm.group(0)
    if value is not None:
        p = re.sub(r'\(property "%s" "(?:[^"\\]|\\.)*"' % re.escape(name), lambda _: '(property "%s" "%s"' % (name, value), p, count=1)
    if at is not None:
        p = re.sub(r'\(at [-\d. ]+\)', '(at %s %s %d)' % (fmt(at[0]), fmt(at[1]), at[2]), p, count=1)
    if just is not None:
        p = re.sub(r'\n\t\t\t\t\(justify [^)]*\)', '', p)
        tail = '\t\t\t\t)\n\t\t\t)\n\t\t)\n'
        assert p.endswith(tail), name
        p = p[:-len(tail)] + '\t\t\t\t)\n\t\t\t\t(justify %s)\n\t\t\t)\n\t\t)\n' % just
    return b.replace(p0, p, 1)


def add_prop(b, after, name, value):
    """a hidden property copied from the property `after`"""
    mm = re.search(r'\t\t\(property "%s" "(?:[^"\\]|\\.)*"\n.*?\n\t\t\)\n' % re.escape(after), b, re.S)
    new = re.sub(r'\(property "%s" "(?:[^"\\]|\\.)*"' % re.escape(after), lambda _: '(property "%s" "%s"' % (name, value), mm.group(0), count=1)
    return b[:mm.end()] + new + b[mm.end():]


def drop_prop(b, name):
    b2, n = re.subn(r'\t\t\(property "%s" "(?:[^"\\]|\\.)*"\n.*?\n\t\t\)\n' % re.escape(name), '', b, count=1, flags=re.S)
    assert n == 1, name
    return b2


def fresh(b, ref):
    old = re.search(r'\(property "Reference" "([^"]+)"', b).group(1)
    b = re.sub(r'\(uuid "[^"]+"\)', lambda _: '(uuid "%s")' % uid(), b)
    b = b.replace('(property "Reference" "%s"' % old, '(property "Reference" "%s"' % ref, 1).replace('(reference "%s")' % old, '(reference "%s")' % ref)
    assert b.count('"%s"' % ref) == 2, ref
    return b


def move_all(b, x, y, angle=None):
    """every position in the block shifted so that the symbol lands on (x, y); angle: new angle for all of them"""
    mm = re.search(r'\(at (-?[\d.]+) (-?[\d.]+) (\d+)\)', b)
    dx, dy = x - float(mm.group(1)), y - float(mm.group(2))
    return re.sub(r'\(at (-?[\d.]+) (-?[\d.]+) (\d+)\)',
                  lambda q: '(at %s %s %s)' % (fmt(float(q.group(1)) + dx), fmt(float(q.group(2)) + dy), q.group(3) if angle is None else angle), b)


def wire(*pts):
    out = ''
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        out += ('\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)\n'
                % (fmt(x0), fmt(y0), fmt(x1), fmt(y1), uid()))
    return out


def junction(x, y):
    return '\t(junction\n\t\t(at %s %s)\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "%s")\n\t)\n' % (fmt(x), fmt(y), uid())


def cut_wire(s, a, b):
    for p, q in ((a, b), (b, a)):
        pat = (r'\t\(wire\n\t\t\(pts\n\t\t\t\(xy %s %s\) \(xy %s %s\)\n\t\t\)\n\t\t\(stroke\n\t\t\t\(width 0\)\n\t\t\t\(type default\)\n\t\t\)\n\t\t\(uuid "[^"]+"\)\n\t\)\n'
               % tuple(re.escape(fmt(v)) for v in p + q))
        s2, n = re.subn(pat, '', s)
        if n == 1:
            return s2
    raise AssertionError(('wire', a, b))


def append(s, text):
    """new items go before the parenthesis that closes the sheet (a sub-sheet has no trailer to insert before)"""
    k = s.rindex('\n)')
    return s[:k] + '\n' + text.rstrip('\n') + s[k:]


# ------------------------------------------------------------------ root sheet: R13 at the sheet pin of PB4
if todo['R13']:
    PIN, MID, END = (93.98, 203.2), (93.98, 207.01), (93.98, 210.82)
    assert '(pin "GPIO_SW_MISC2" input\n\t\t\t(at 93.98 203.2 270)' in t
    t = cut_wire(t, PIN, MID)
    old = '\t(label "HV_SW_STATE"\n\t\t(at 93.98 207.01 180)'
    assert t.count(old) == 1
    t = t.replace(old, '\t(label "HV_SW_STATE"\n\t\t(at %s %s 180)' % (fmt(END[0]), fmt(END[1])))       # the label moves down by the length of the resistor
    j, r12 = inst(t, 'R12')
    assert '(lib_id "Device:R")' in r12 and '(at 74.93 129.54 90)' in r12
    r13 = fresh(move_all(r12, MID[0], MID[1], angle=0), 'R13')          # upright: pin 1 on the sheet pin, pin 2 on the label
    r13 = drop_prop(r13, 'Assembly Note')
    r13 = prop(r13, 'Reference', at=(95.25, 205.74, 0), just='left')
    r13 = prop(r13, 'Value', '1k', at=(95.25, 208.28, 0), just='left')
    r13 = prop(r13, 'Manufacturer Part Number', 'RC0402FR-071KL')
    t = t[:j + len(r12)] + '\n\t' + r13.lstrip('\t') + t[j + len(r12):]
    assert t.count('(') == t.count(')')

# ------------------------------------------------------------------ MCU sheet: SW3 across C10
if todo['SW3']:
    stock = open(STOCK, encoding='utf-8').read()
    sym = block_at(stock, stock.index('\n\t(symbol "SW_Push"\n') + 2)
    emb = '\n'.join('\t' + l for l in ('\t' + sym).split('\n')).replace('(symbol "SW_Push"\n', '(symbol "Switch:SW_Push"\n', 1)
    i = m.index('\n\t(lib_symbols\n') + 2
    k = i + len(block_at(m, i)) - 3                                      # before the line that closes (lib_symbols ...)
    assert m[k:k + 3] == '\n\t)' and '(symbol "Switch:SW_Push"' not in m
    m = m[:k] + '\n' + emb.rstrip('\n') + m[k:]

    A, B, C = (80.01, 63.5), (85.09, 63.5), (91.44, 63.5)               # NRST wire: sheet label, the new tap, C10
    m = cut_wire(m, A, C)
    _, c10 = inst(m, 'C10')
    assert '(lib_id "Device:C")' in c10 and '(at 91.44 67.31 0)' in c10
    sw = fresh(move_all(c10, 85.09, 68.58), 'SW3').replace('(lib_id "Device:C")', '(lib_id "Switch:SW_Push")', 1)
    sw = sw.replace('\t\t(fields_autoplaced yes)\n', '', 1)
    sw = sw.replace('(at 85.09 68.58 0)', '(at 85.09 68.58 270)', 1)      # upright: pin 1 on NRST (y = 63.5), pin 2 on GND (y = 73.66)
    sw = prop(sw, 'Reference', at=(83.82, 67.31, 90), just='right')       # a field turns with its symbol: 90 here reads level on the sheet
    sw = prop(sw, 'Value', 'RESET', at=(83.82, 69.85, 90), just='right')
    sw = prop(sw, 'Footprint', 'Button_Switch_BoardEdge:SW_SPST_B3U-3000P-B_BoardEdge', at=(85.09, 68.58, 0))
    sw = prop(sw, 'Datasheet', 'https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3u.pdf')
    sw = prop(sw, 'Description', 'Tactile switch, SPST-NO, side-actuated, with locating boss, 3 x 2.5 mm')
    sw = prop(sw, 'Manufacturer', 'Omron')
    sw = prop(sw, 'Manufacturer Part Number', 'B3U-3000P-B')
    sw = add_prop(sw, 'Manufacturer Part Number', 'Assembly Note',
                  'SW3: front of the body on the board edge, plunger towards the outside (it stands 0.7 mm over the edge: '
                  'no V-cut along the top edge). Not washable: no-clean process, or fit after washing. '
                  'B3U-3000P (same switch without the locating boss) is an accepted substitute')
    nums = []
    for fn in glob.glob('*.kicad_sch'):
        nums += [int(n) for n in re.findall(r'"#PWR0*(\d+)"', open(fn, encoding='utf-8').read())]
    _, gnd = inst(m, '#PWR0257')
    assert '(lib_id "power:GND")' in gnd and '(at 91.44 71.12 0)' in gnd
    g = fresh(move_all(gnd, 85.09, 73.66), '#PWR0%d' % (max(nums) + 1))
    m = append(m, wire(A, B) + wire(B, C) + junction(*B) + '\t' + sw.lstrip('\t') + '\n\t' + g.lstrip('\t') + '\n')
    assert m.count('(') == m.count(')')

# ------------------------------------------------------------------ MCU sheet: note for the buyer on U2
if todo['U2 note']:
    j, u2 = inst(m, 'U2')
    assert '(property "Manufacturer Part Number" "STM32G474RET6"' in u2 and '(property "Assembly Note"' not in u2
    m = m[:j] + add_prop(u2, 'Manufacturer Part Number', 'Assembly Note', U2_NOTE) + m[j + len(u2):]
    assert m.count('(') == m.count(')')

open(ROOT, 'w', encoding='utf-8').write(t)
open(MCU, 'w', encoding='utf-8').write(m)
print('applied:', ', '.join(k for k, v in todo.items() if v))

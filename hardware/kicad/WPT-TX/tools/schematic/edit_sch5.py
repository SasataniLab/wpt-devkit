#!/usr/bin/env python3
"""Schematic edit of 2026-11-14, third revision, part 3: the BOM (run inside the project directory hardware/kicad/WPT-TX).

Nothing electrical changes. The aim is a BOM an assembler can buy from without asking:

  * test points (TP...) are bare pads / plated holes, not parts: out of the BOM and out of the placement files
  * one spelling per manufacturer (the same maker appeared as "Murata Electronics " with a trailing blank, "microchip",
    "ULO Electronic", "EPSON")
  * part numbers written the way the manufacturer writes them (MPN_FIX)
  * part numbers for the parts that had none (ADD: the 2.54 mm pin headers)
  * an "Assembly Note" field on the parts that need an instruction (NOTE); fab/bom_pcbway.py prints it

Run it again after changing the tables: every step only touches what still differs.
"""
import re
import sys

FILES = ('WPT-01-TRANSMITTER.kicad_sch', 'WPT-01-TRANSMITTER-POWER.kicad_sch', 'WPT-01-TRANSMITTER-TX.kicad_sch', 'MCU.kicad_sch')

MAKER = {'Murata Electronics ': 'Murata Electronics', 'microchip': 'Microchip Technology', 'ULO Electronic': 'ULO Electronics', 'EPSON': 'Epson'}
# part number as it was -> as the manufacturer writes it
MPN_FIX = {}
# reference -> (manufacturer, part number) for parts that had no part number
ADD = {}
# reference -> instruction for the assembler
NOTE = {'J3': 'Keying slot of the shroud faces the board edge; pin 1 is the square pad at the north-west corner'}


def blocks(t):
    """(start, end) of every placed symbol on a sheet"""
    out = []
    for m in re.finditer(r'\n\t\(symbol\n', t):
        j = m.start() + 1
        d = 0
        for k in range(j, len(t)):
            if t[k] == '(':
                d += 1
            elif t[k] == ')':
                d -= 1
                if d == 0:
                    out.append((j, k + 1))
                    break
    return out


def prop(b, name):
    m = re.search(r'\(property "%s" "((?:[^"\\]|\\.)*)"' % re.escape(name), b)
    return m.group(1) if m else None


def set_prop(b, name, value):
    return re.sub(r'(\(property "%s" ")((?:[^"\\]|\\.)*)(")' % re.escape(name), lambda m: m.group(1) + value + m.group(3), b, count=1)


def add_prop(b, name, value):
    """a hidden field, placed like the part number field of the same symbol"""
    m = re.search(r'\t\t\(property "Manufacturer Part Number" .*?\n\t\t\)\n', b, re.S) or re.search(r'\t\t\(property "Footprint" .*?\n\t\t\)\n', b, re.S)
    new = set_prop(m.group(0).replace(m.group(0).split('"')[1], name, 1), name, value)
    if '(hide yes)' not in new:
        new = new.replace('\t\t\t(effects', '\t\t\t(hide yes)\n\t\t\t(effects', 1)
    return b[:m.end()] + new + b[m.end():]


total = 0
for fn in FILES:
    t = open(fn, encoding='utf-8').read()
    n = 0
    for old, new in MAKER.items():                       # also in the embedded library symbols, so that new parts get it right
        c = t.count('(property "Manufacturer" "%s"' % old)
        t = t.replace('(property "Manufacturer" "%s"' % old, '(property "Manufacturer" "%s"' % new)
        n += c
    for old, new in MPN_FIX.items():
        c = t.count('(property "Manufacturer Part Number" "%s"' % old)
        t = t.replace('(property "Manufacturer Part Number" "%s"' % old, '(property "Manufacturer Part Number" "%s"' % new)
        n += c
    for j, k in reversed(blocks(t)):
        b = t[j:k]
        ref = prop(b, 'Reference')
        if ref is None:
            continue
        nb = b
        if re.fullmatch(r'TP\d+', ref):
            nb = nb.replace('(in_bom yes)', '(in_bom no)', 1).replace('(in_pos_files yes)', '(in_pos_files no)', 1)
        if ref in ADD:
            maker, mpn = ADD[ref]
            for name, value in (('Manufacturer', maker), ('Manufacturer Part Number', mpn)):
                nb = set_prop(nb, name, value) if prop(nb, name) is not None else add_prop(nb, name, value)
        if ref in NOTE:
            nb = set_prop(nb, 'Assembly Note', NOTE[ref]) if prop(nb, 'Assembly Note') is not None else add_prop(nb, 'Assembly Note', NOTE[ref])
        if nb != b:
            t = t[:j] + nb + t[k:]
            n += 1
    assert t.count('(') == t.count(')'), fn
    if n:
        open(fn, 'w', encoding='utf-8').write(t)
    print('%-38s %d changes' % (fn, n))
    total += n
# the project symbol libraries carry the same fields; keep them equal to the copies embedded in the sheets (ERC compares them)
import glob
for fn in sorted(glob.glob('lib/symbols/*.kicad_sym')):
    t = open(fn, encoding='utf-8').read()
    n = 0
    for name, table in (('Manufacturer', MAKER), ('Manufacturer Part Number', MPN_FIX)):
        for old, new in table.items():
            c = t.count('(property "%s" "%s"' % (name, old))
            t = t.replace('(property "%s" "%s"' % (name, old), '(property "%s" "%s"' % (name, new))
            n += c
    if n:
        open(fn, 'w', encoding='utf-8').write(t)
        print('%-38s %d changes' % (fn, n))
    total += n
if not total:
    sys.exit('nothing to change')

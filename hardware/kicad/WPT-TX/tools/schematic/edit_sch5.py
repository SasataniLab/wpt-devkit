#!/usr/bin/env python3
"""Schematic edit of 2026-11-14, third revision, part 3: the BOM (run inside the project directory hardware/kicad/WPT-TX).

Nothing electrical changes. The aim is a BOM an assembler can buy from without asking:

  * test points (TP...) are bare pads / plated holes, not parts: out of the BOM and out of the placement files
  * one spelling per manufacturer (the same maker appeared as "Murata Electronics " with a trailing blank, "microchip",
    "ULO Electronic", "EPSON")
  * part numbers written the way the manufacturer writes them (MPN_FIX)
  * part numbers for the parts that had none, and parts that are no longer made replaced (SET)
  * an "Assembly Note" field on the parts that need an instruction (NOTE); fab/bom_pcbway.py prints it

Run it again after changing the tables: every step only touches what still differs.
"""
import re
import sys

FILES = ('WPT-01-TRANSMITTER.kicad_sch', 'WPT-01-TRANSMITTER-POWER.kicad_sch', 'WPT-01-TRANSMITTER-TX.kicad_sch', 'MCU.kicad_sch')

MAKER = {'Murata Electronics ': 'Murata Electronics', 'microchip': 'Microchip Technology', 'ULO Electronic': 'ULO Electronics', 'EPSON': 'Epson',
         'ON Semiconductor': 'onsemi', 'Silicon Labs': 'Skyworks Solutions'}      # the makers' names today (the Si5351 went to Skyworks)
# part number as it was -> as the manufacturer writes it, or the part that replaces it (BOM audit of 2026-11-14)
MPN_FIX = {
    'MCP45HV51-104E_ST': 'MCP45HV51-104E/ST',            # the ordering code has a slash
    'FA-238_25.0000MB-K3': 'FA-238 25.0000MB-K3',        # ... and this one a blank
    '2929SQ-391JEB': '2929SQ-391JEC',                    # Coilcraft retired packaging code B
    'NR5040T4R7N': 'LSXND5050YAL4R7NMG',                 # phased out; successor with the same size, terminals and ratings (ex NRS5040T4R7NMGK)
    'CL31A106KBHNNNE': 'CL31B106KBHNNNE',                # the value says X7R, CL31A is X5R; CL31B is the X7R part of the same size
    'GRM1555C1HR50BA01D': 'GJM1555C1HR50BB01D',          # 0.5 pF: the GRM part is "not for new designs"
}
WURTH = 'Wurth Elektronik'
# reference -> fields to set (parts that had no part number, parts that change maker, parts merged onto a line that exists already)
SET = {
    # 2.54 mm pin headers: Wurth WR-PHD 6130xx11121, xx = number of pins
    'J1': {'Manufacturer': WURTH, 'Manufacturer Part Number': '61300211121'},
    'J4': {'Manufacturer': WURTH, 'Manufacturer Part Number': '61300411121'},
    'J301': {'Manufacturer': WURTH, 'Manufacturer Part Number': '61301011121'},
    'J2': {'Manufacturer': WURTH, 'Manufacturer Part Number': '61301211121'},
    # the same kind of header under a brand no distributor carries ("ULO"); one of the two codes was a footprint name
    'CN203': {'Manufacturer': WURTH, 'Manufacturer Part Number': '61300311121', 'Value': 'PinHeader_1x03'},
    'CN207': {'Manufacturer': WURTH, 'Manufacturer Part Number': '61300311121', 'Value': 'PinHeader_1x03'},
    'CN208': {'Manufacturer': WURTH, 'Manufacturer Part Number': '61300211121', 'Value': 'PinHeader_1x02'},
    'CN209': {'Manufacturer': WURTH, 'Manufacturer Part Number': '61300211121', 'Value': 'PinHeader_1x02'},
    'CN210': {'Manufacturer': WURTH, 'Manufacturer Part Number': '61300211121', 'Value': 'PinHeader_1x02'},
    'CN302': {'Manufacturer': WURTH, 'Manufacturer Part Number': '61300211121', 'Value': 'PinHeader_1x02'},
    'J202': {'Manufacturer': WURTH, 'Manufacturer Part Number': '61300211121', 'Value': 'PinHeader_1x02'},
    # 1 uF 0402 at VDDA / VREF+: GRM155R61A105KE15D is being discontinued
    'C7': {'Manufacturer': 'Samsung Electro-Mechanics', 'Manufacturer Part Number': 'CL05A105KA5NQNC'},
    'C9': {'Manufacturer': 'Samsung Electro-Mechanics', 'Manufacturer Part Number': 'CL05A105KA5NQNC'},
    # 100 nF and 10 nF 0402 of the MCU section onto the lines the power section already has
    'C1': {'Manufacturer Part Number': 'GCM155R71H104KE02D'}, 'C2': {'Manufacturer Part Number': 'GCM155R71H104KE02D'},
    'C3': {'Manufacturer Part Number': 'GCM155R71H104KE02D'}, 'C4': {'Manufacturer Part Number': 'GCM155R71H104KE02D'},
    'C8': {'Manufacturer Part Number': 'GCM155R71H104KE02D'}, 'C10': {'Manufacturer Part Number': 'GCM155R71H104KE02D'},
    'C15': {'Manufacturer Part Number': 'GCM155R71H104KE02D'},
    'C6': {'Manufacturer': 'Yageo', 'Manufacturer Part Number': 'CC0402KRX7R9BB103'},
    'C16': {'Manufacturer': 'Yageo', 'Manufacturer Part Number': 'CC0402KRX7R9BB103'},
    # values that were the old part number
    'U204': {'Value': 'MCP45HV51-104E/ST'}, 'X301': {'Value': 'FA-238 25.0000MB-K3'},
    'L201': {'Value': '4.7uH'}, 'L202': {'Value': '4.7uH'},
}
# reference -> instruction for the assembler
NOTE = {'J3': 'Keying slot of the shroud faces the board edge; pin 1 is the square pad at the north-west corner',
        'J5': 'Solder the four shell stakes in their plated slots (no paste is printed there)',
        'SW1': 'Solder both frame lugs (they ground the shaft)',
        'D201': 'Or equivalent: 3 mm red LED, diffused, high brightness (it runs at 0.6 mA), 2.54 mm lead pitch',
        'U3': 'Original STMicroelectronics part only (other makers sell clones under the same number)'}


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
        for name, value in SET.get(ref, {}).items():
            if prop(nb, name) != value:
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

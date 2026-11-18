#!/usr/bin/env python3
"""Schematic edits of 2026-11-14 (run inside the project directory hardware/kicad/WPT-TX).

1. MCU sheet: C16 10 nF from ADC1_IN1_VDC (PA0) to GND. The DC-bus divider is 75 k / 3.6 k, the line to PA0 crosses
   the board; the capacitor at the pin holds the sample charge and takes switching noise off the line.
2. MCU sheet: label BOOT0 on the net J1.1 - R2 - PB8, which had only an automatic name.
3. TX sheet: J301 becomes 1x10; pin 9 = +3V3 and pin 10 = GND, so that an add-on board (comparators for the
   zero-voltage detection) can be powered from the header. Pins 1 to 8 keep their function.
"""
import re
import sys
import uuid

MCU, TX = 'MCU.kicad_sch', 'WPT-01-TRANSMITTER-TX.kicad_sch'
SYMLIB = '/usr/share/kicad/symbols/Connector.kicad_sym'
uid = lambda: str(uuid.uuid4())


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


def inst_block(t, ref):
    i = t.index('(property "Reference" "%s"' % ref)
    j = t.rfind('\n\t(symbol\n', 0, i) + 1
    return j, block_at(t, j)


def n(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def shifted(b, dx, dy):
    return re.sub(r'\(at (-?[\d.]+) (-?[\d.]+) (-?\d+)\)', lambda m: '(at %s %s %s)' % (n(float(m.group(1)) + dx), n(float(m.group(2)) + dy), m.group(3)), b)


def fresh(b):
    return re.sub(r'\(uuid "[^"]+"\)', lambda m: '(uuid "%s")' % uid(), b)


def wire(a, b):
    return ('\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)\n'
            % (n(a[0]), n(a[1]), n(b[0]), n(b[1]), uid()))


def label(name, x, y):
    return ('\t(label "%s"\n\t\t(at %s %s 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)\n'
            % (name, n(x), n(y), uid()))


def append(t, new):
    k = t.rindex('\n\t(sheet_instances\n') + 1 if '\n\t(sheet_instances\n' in t else t.rindex('\n\t(embedded_fonts')+1 if '\n\t(embedded_fonts' in t else t.rindex(')')
    return t[:k] + new + t[k:]


mcu = open(MCU, encoding='utf-8').read()
tx = open(TX, encoding='utf-8').read()
if '(property "Reference" "C16"' in mcu:
    sys.exit('already applied')

# ---- 1. C16
_, c6 = inst_block(mcu, 'C6')
X, Y = 195.58, 69.85          # pin 1 at (X, Y - 3.81) on a wire from the PA0 label, pin 2 at (X, Y + 3.81) to GND
c16 = fresh(shifted(c6, X - 162.56, Y - 57.15)).replace('"Reference" "C6"', '"Reference" "C16"').replace('(reference "C6")', '(reference "C16")')
i = mcu.index('(lib_id "power:GND")')
j = mcu.rfind('\n\t(symbol\n', 0, i) + 1
g = block_at(mcu, j)
gm = re.search(r'\(at (-?[\d.]+) (-?[\d.]+) (\d+)\)', g)
assert gm.group(3) == '0', gm.group(0)
oldref = re.search(r'\(property "Reference" "(#PWR\d+)"', g).group(1)
gnd = fresh(shifted(g, X - float(gm.group(1)), Y + 3.81 - float(gm.group(2)))).replace(oldref, '#PWR0370')
new = '\t' + c16.lstrip('\t') + '\n' if not c16.startswith('\t') else c16 + '\n'
new += (gnd if gnd.startswith('\t') else '\t' + gnd) + '\n'
# wired to the end of the PA0 wire (no label: a second local label would rename the net)
assert '(xy 165.1 71.12) (xy 172.72 71.12)' in mcu
new += wire((172.72, 71.12), (172.72, 66.04)) + wire((172.72, 66.04), (X, Y - 3.81))
# ---- 2. BOOT0
assert '(xy 165.1 134.62) (xy 198.12 134.62)' in mcu
new += label('BOOT0', 180.34, 134.62)
mcu = append(mcu, new)

# ---- 3. J301 -> 1x10
lib = open(SYMLIB, encoding='utf-8').read()
i = lib.index('\n\t(symbol "Conn_01x10_Pin"\n') + 1
sym = block_at(lib, i + 1)
sym = sym.replace('(symbol "Conn_01x10_Pin"', '(symbol "Connector:Conn_01x10_Pin"', 1)
sym = '\n'.join('\t' + l for l in ('\t' + sym).split('\n'))               # library files are one level less indented
k = tx.index('\n\t\t(symbol "Connector:Conn_01x08_Pin"\n') + 1
tx = tx[:k] + sym + '\n' + tx[k:]
j, b = inst_block(tx, 'J301')
nb = b.replace('(lib_id "Connector:Conn_01x08_Pin")', '(lib_id "Connector:Conn_01x10_Pin")')
nb = nb.replace('(at 297.18 228.6 0)', '(at 297.18 231.14 0)')
nb = nb.replace('(property "Value" "Conn_01x08_Pin"\n\t\t\t(at 297.18 241.3 0)', '(property "Value" "Conn_01x10_Pin"\n\t\t\t(at 297.18 248.92 0)')
nb = nb.replace('PinHeader_1x08_P2.54mm_Vertical', 'PinHeader_1x10_P2.54mm_Vertical')
nb = nb.replace('single row, 01x08', 'single row, 01x10')
assert nb.count('Conn_01x10_Pin') == 2 and '1x10_P2.54mm' in nb
k = nb.index('\t\t(instances')
nb = nb[:k] + ''.join('\t\t(pin "%d"\n\t\t\t(uuid "%s")\n\t\t)\n' % (p, uid()) for p in (9, 10)) + nb[k:]
tx = tx[:j] + nb + tx[j + len(b):]
i = tx.index('(global_label "GND"\n\t\t(shape passive)\n\t\t(at 304.8 223.52 0)')
gl = block_at(tx, i)
new = wire((302.26, 241.3), (304.8, 241.3)) + wire((302.26, 243.84), (304.8, 243.84))
new += '\t' + fresh(shifted(gl, 0, 241.3 - 223.52)).replace('(global_label "GND"', '(global_label "+3V3"') + '\n'
new += '\t' + fresh(shifted(gl, 0, 243.84 - 223.52)) + '\n'
tx = append(tx, new)

for name, t in ((MCU, mcu), (TX, tx)):
    assert t.count('(') == t.count(')'), name
    open(name, 'w', encoding='utf-8').write(t)
print('applied')

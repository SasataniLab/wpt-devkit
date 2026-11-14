#!/usr/bin/env python3
"""Schematic edit of 2026-11-14, third revision (run inside the project directory hardware/kicad/WPT-TX).

J3, the SWD header, becomes the ST debug connector STDC14 (2 x 7, 1.27 mm; Samtec FTSH-107-01-L-D-K, through-hole with
keying shroud), so that an STLINK-V3 cable plugs straight in. Pin use (UM2448 numbering, as in KiCad's symbol
Connector:Conn_ST_STDC14):
    3 VCC -> +3V3      4 SWDIO      5, 7 GND      6 SWCLK      11 GNDDetect -> GND      12 NRST
    1, 2, 8 (SWO), 9, 10, 13 (VCP_RX), 14 (VCP_TX) not connected
SWO is not available (PB3 is GPIO_SW_MISC1).
The virtual COM port pins stay open. USART1 (PC4 / PC5) goes to J4 through the footprint of the slide switch, and the
passages between the switch pins are all in use; the only free pins that carry a UART (PB6 / PB7) are fenced in by
the tracks east of the MCU. Wiring pins 13 / 14 would mean laying out that corner again (see docs/stm32-tx/layout_notes.md).
The three signal wires keep their place, so the net names (/MCU/NRST, /MCU/SWCLK, /MCU/SWDIO) do not change.
"""
import re
import sys
import uuid

ROOT = 'WPT-01-TRANSMITTER.kicad_sch'
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


def wire(*pts):
    out = ''
    for a, b in zip(pts, pts[1:]):
        out += ('\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)\n'
                % (n(a[0]), n(a[1]), n(b[0]), n(b[1]), uid()))
    return out


def no_connect(x, y):
    return '\t(no_connect\n\t\t(at %s %s)\n\t\t(uuid "%s")\n\t)\n' % (n(x), n(y), uid())


def junction(x, y):
    return '\t(junction\n\t\t(at %s %s)\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "%s")\n\t)\n' % (n(x), n(y), uid())


def remove(t, b):
    i = t.index(b)
    j = i + len(b)
    if t[j] == '\n':
        j += 1
    return t[:i] + t[j:]


t = open(ROOT, encoding='utf-8').read()
if 'Conn_ST_STDC14' in t:
    sys.exit('already applied')

# ---- the old header and its two power symbols go
j, old = inst_block(t, 'J3')
assert '(lib_id "Connector:Conn_01x05_Pin")' in old and '(at 96.52 111.76 270)' in old
project = re.search(r'\(project "([^"]+)"\s*\(path "([^"]+)"', old).groups()
t = remove(t, old)
moved = {}
for ref, at in (('#PWR0273', '(at 93.98 119.38 180)'), ('#PWR0272', '(at 91.44 119.38 0)')):
    j, b = inst_block(t, ref)
    assert at in b, ref
    moved[ref] = b
    t = remove(t, b)
for a, b in (((93.98, 119.38), (93.98, 116.84)), ((91.44, 119.38), (91.44, 116.84))):
    m = re.search(r'\t\(wire\s*\(pts\s*\(xy %s %s\) \(xy %s %s\)\s*\)' % (n(a[0]), n(a[1]), n(b[0]), n(b[1])), t)
    assert m, (a, b)
    t = remove(t, block_at(t, m.start()))

# ---- library symbol
lib = open(SYMLIB, encoding='utf-8').read()
i = lib.index('\n\t(symbol "Conn_ST_STDC14"\n') + 1
sym = block_at(lib, i + 1)
sym = sym.replace('(symbol "Conn_ST_STDC14"', '(symbol "Connector:Conn_ST_STDC14"', 1)
sym = '\n'.join('\t' + l for l in ('\t' + sym).split('\n'))
k = t.index('\n\t\t(symbol "Connector:Conn_01x04_Pin"\n') + 1
t = t[:k] + sym + '\n' + t[k:]

# ---- the new instance: symbol origin (X, Y); a pin at library (px, py) sits at (X + px, Y - py)
X, Y = 55.88, 119.38
P = lambda px, py: (X + px, Y - py)
props = [('Reference', 'J3', X - 8.89, Y - 16.51, False), ('Value', 'STDC14', X + 2.54, Y - 16.51, False),
         ('Footprint', 'Connector_Samtec_FTSH:FTSH-107-01-L-D-K_2x07_P1.27mm_Vertical', X, Y, True),
         ('Datasheet', 'https://www.st.com/resource/en/user_manual/um2448-stlinkv3set-debuggerprogrammer-for-stm8-and-stm32-stmicroelectronics.pdf', X, Y, True),
         ('Description', 'ST Debug Connector, standard ARM Cortex-M SWD and JTAG interface plus UART', X, Y, True),
         ('Manufacturer', 'Samtec', X, Y, True), ('Manufacturer Part Number', 'FTSH-107-01-L-D-K', X, Y, True)]
inst = '\t(symbol\n\t\t(lib_id "Connector:Conn_ST_STDC14")\n\t\t(at %s %s 0)\n\t\t(unit 1)\n\t\t(body_style 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n\t\t(uuid "%s")\n' % (n(X), n(Y), uid())
for name, val, x, y, hide in props:
    inst += ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s 0)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n%s\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n%s\t\t\t)\n\t\t)\n'
             % (name, val, n(x), n(y), '\t\t\t(hide yes)\n' if hide else '', '\t\t\t\t(justify left)\n' if name in ('Reference', 'Value') else ''))
for p in range(1, 15):
    inst += '\t\t(pin "%d"\n\t\t\t(uuid "%s")\n\t\t)\n' % (p, uid())
inst += '\t\t(instances\n\t\t\t(project "%s"\n\t\t\t\t(path "%s"\n\t\t\t\t\t(reference "J3")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n' % project

new = inst
new += wire(P(12.7, 12.7), (101.6, Y - 12.7), (101.6, 116.84))          # ~RST -> NRST (the wire to the MCU sheet pin)
new += wire(P(12.7, 7.62), (99.06, Y - 7.62), (99.06, 116.84))          # SWCLK
new += wire(P(12.7, 5.08), (96.52, Y - 5.08), (96.52, 116.84))          # SWDIO
for py in (2.54, 0, -5.08, -10.16, -12.7):                              # SWO, JTDI, JRCLK, VCP_RX, VCP_TX
    new += no_connect(*P(12.7, py))


def place(b, x, y, rot):
    m = re.search(r'\(at (-?[\d.]+) (-?[\d.]+) (\d+)\)', b)
    dx, dy = x - float(m.group(1)), y - float(m.group(2))
    first = [True]

    def sub(mm):
        r = mm.group(3)
        if first[0]:
            first[0] = False
            r = str(rot)
        return '(at %s %s %s)' % (n(float(mm.group(1)) + dx), n(float(mm.group(2)) + dy), r)
    return re.sub(r'\(at (-?[\d.]+) (-?[\d.]+) (\d+)\)', sub, b)


vx, vy = P(0, 17.78)
new += '\t' + place(moved['#PWR0273'], vx, vy, 0).lstrip('\t') + '\n'            # +3V3 on VCC
gx, gy = P(0, -17.78)
dx, dy = P(-2.54, -17.78)
new += wire((gx, gy), (gx, gy + 2.54)) + wire((dx, dy), (dx, gy + 2.54), (gx, gy + 2.54))
new += '\t' + place(moved['#PWR0272'], gx, gy + 2.54, 0).lstrip('\t') + '\n'    # GND on pins 5, 7 and 11
k = t.rindex('\n\t(sheet_instances\n') + 1 if '\n\t(sheet_instances\n' in t else t.rindex('\n\t(embedded_fonts') + 1
t = t[:k] + new + t[k:]
assert t.count('(') == t.count(')')
open(ROOT, 'w', encoding='utf-8').write(t)
print('applied; J3 symbol uuid', re.search(r'\(uuid "([^"]+)"\)', inst).group(1))

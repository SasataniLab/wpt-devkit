#!/usr/bin/env python3
"""Schematic edit of 2026-11-14, fourth revision, part 1: the UART goes to the debug connector
(run inside the project directory hardware/kicad/WPT-TX).

  J3 (STDC14), pins 13 and 14: the virtual COM port of an STLINK-V3 is wired to USART1 (PC4 / PC5), the UART that
        went to J4 only.
          pin 14  T_VCP_TX (input of the probe)   <-  USART1_TX_EXTERNAL (PC4)
          pin 13  T_VCP_RX (output of the probe)  ->  R12 560 ohm  ->  USART1_RX_EXTERNAL (PC5)
        R12 keeps the peace if a USB-UART adapter on J4 and the probe ever drive the receive line together (6 mA),
        and limits the current into PC5 when the probe is powered and the board is not.
  J4 (1x4 header: RX, TX, +3V3, GND): stays on the board with its tracks, but is no longer fitted (DNP). It is the
        access for a probe without a virtual COM port; a header can be soldered in by hand.
"""
import re
import sys
import uuid

uid = lambda: str(uuid.uuid4())
FN = 'WPT-01-TRANSMITTER.kicad_sch'
t = open(FN, encoding='utf-8').read()
if '(property "Reference" "R12"' in t:
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


def inst(t, ref):
    i = t.index('(property "Reference" "%s"' % ref)
    j = t.rfind('\n\t(symbol\n', 0, i) + 1
    return j, block_at(t, j)


def setp(b, name, value):
    b2, n = re.subn(r'(\(property "%s" ")((?:[^"\\]|\\.)*)(")' % re.escape(name), lambda m: m.group(1) + value + m.group(3), b, count=1)
    assert n == 1, name
    return b2


def getp(b, name):
    return re.search(r'\(property "%s" "((?:[^"\\]|\\.)*)"' % re.escape(name), b).group(1)


def fmt(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def wire(*pts):
    out = ''
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        out += ('\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)\n'
                % (fmt(x0), fmt(y0), fmt(x1), fmt(y1), uid()))
    return out


def junction(x, y):
    return '\t(junction\n\t\t(at %s %s)\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "%s")\n\t)\n' % (fmt(x), fmt(y), uid())


def drop_no_connect(t, x, y):
    m = re.search(r'\t\(no_connect\n\t\t\(at %s %s\)\n\t\t\(uuid "[^"]+"\)\n\t\)\n' % (re.escape(fmt(x)), re.escape(fmt(y))), t)
    assert m, ('no_connect', x, y)
    return t[:m.start()] + t[m.end():]


# the two "not connected" marks on J3 pins 13 (68.58, 129.54) and 14 (68.58, 132.08)
t = drop_no_connect(t, 68.58, 129.54)
t = drop_no_connect(t, 68.58, 132.08)

# R12: a copy of R8 (same library symbol, 0402), lying between pin 13 and the receive line
_, r8 = inst(t, 'R8')
assert '(lib_id "Device:R")' in r8 and '(at 123.19 96.52 0)' in r8 and getp(r8, 'Manufacturer Part Number') == 'RC0402FR-0715KL'
CX, CY = 74.93, 129.54                                     # rotated 90 degrees: pin 1 at (71.12, 129.54), pin 2 at (78.74, 129.54)
r12 = r8.replace('(at 123.19 96.52 0)', '(at %s %s 90)' % (fmt(CX), fmt(CY)), 1)
r12 = setp(setp(setp(r12, 'Reference', 'R12'), 'Value', '560R'), 'Manufacturer Part Number', 'RC0402FR-07560RL')
r12 = r12.replace('(reference "R8")', '(reference "R12")')
assert r12.count('"R12"') == 2, r12.count('"R12"')
# field positions: reference and value above the body, everything else (hidden) on the body
first = [True]


def place(m):
    name = m.group(1)
    pos = {'Reference': (CX - 2.2, CY - 1.9), 'Value': (CX + 2.2, CY - 1.9)}.get(name, (CX, CY))
    return '(property "%s" "%s"\n\t\t\t(at %s %s 90)' % (name, m.group(2), fmt(pos[0]), fmt(pos[1]))


r12 = re.sub(r'\(property "([^"]+)" "((?:[^"\\]|\\.)*)"\n\t\t\t\(at [-\d.]+ [-\d.]+ \d+\)', place, r12)
r12 = re.sub(r'\(uuid "[^"]+"\)', lambda m: '(uuid "%s")' % uid(), r12)

new = (wire((68.58, 129.54), (71.12, 129.54))                                        # J3 pin 13 -> R12
       + wire((78.74, 129.54), (78.74, 142.24), (91.44, 142.24)) + junction(91.44, 142.24)   # R12 -> receive line (J4 pin 1 / PC5)
       + wire((68.58, 132.08), (73.66, 132.08), (73.66, 144.78), (88.9, 144.78)) + junction(88.9, 144.78)   # J3 pin 14 -> transmit line
       + '\t' + r12.lstrip('\t') + '\n')
k = t.rindex('\n\t(sheet_instances\n') + 1 if '\n\t(sheet_instances\n' in t else t.rindex('\n\t(embedded_fonts') + 1
t = t[:k] + new + t[k:]

# J4: not fitted
j, b = inst(t, 'J4')
assert '(dnp no)' in b
t = t[:j] + b.replace('(dnp no)', '(dnp yes)', 1) + t[j + len(b):]

assert t.count('(') == t.count(')')
open(FN, 'w', encoding='utf-8').write(t)
print('applied')

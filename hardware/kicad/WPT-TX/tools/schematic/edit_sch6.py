#!/usr/bin/env python3
"""Schematic edit of 2026-11-14, third revision, part 4: changes from the pre-order review
(run inside the project directory hardware/kicad/WPT-TX).

  R320, R323, R326, R329   0 ohm -> 560 ohm (RC0402FR-07560RL). The links from the HRTIM outputs to the LM5113 inputs.
        EPC9065 has 390 / 470 ohm into the 22 pF at each driver input, and TI's data sheet (SNVSAR1B, section 7.3.1,
        figure 16: 1 k + 22 pF) asks for this filter so that the driver never sees a pulse shorter than 3 ns. With
        0 ohm the 22 pF did nothing. 560 ohm x 27 pF = 15 ns: pulses below 13 ns are swallowed, what passes is at
        least 3.3 ns wide at the threshold; delay 14.8 ns rising / 10.4 ns falling, i.e. 4.4 ns of dead time added.
  C302, C318               22 nF -> 100 nF (GCM155R71H104KE02D, the part of C301). The bootstrap capacitors; EPC9065 has
        100 nF here (C4), 22 nF is its level-shift capacitor (C3). Ripple 0.2 V -> 0.04 V on about 4.5 V.
  R339, R341               15 k stays, part ERJ-PA2F1502X (0.2 W) instead of RC0402FR-0715KL (1/16 W): 47 mW at 40 V on
        the bus is 75 % of the standard part's rating and more than its derated rating above 85 degC.
  R207                     10 k -> 2.2 k (RC0402FR-072K2L). Series resistor of D201, the "high voltage enabled" LED on the
        enable line. That line was 5 V from the Arduino and is 3.3 V from the STM32 now: with 10 k the LED would get
        0.14 mA, less than half of what it had. 2.2 k gives 0.6 mA.
  SW1                      symbol Device:RotaryEncoder_Switch -> Device:RotaryEncoder_Switch_MP, frame lugs (MP) to GND.
        The metal shaft and frame of the encoder were floating; a discharge from a hand had no path but the terminals
        on PC6 / PC7 / PC13.
"""
import re
import sys
import uuid

uid = lambda: str(uuid.uuid4())
STOCK = '/usr/share/kicad/symbols/Device.kicad_sym'


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


def lib_symbol(t, name):
    i = t.index('\n\t\t(symbol "%s"\n' % name) + 1
    return block_at(t, i)


def geometry(sym):
    """a library symbol without its property blocks and its name, for comparison"""
    s = re.sub(r'\t\t\t\(property .*?\n\t\t\t\)\n', '', sym, flags=re.S)
    return re.sub(r'\(symbol "[^"]*"', '(symbol', s)


changed = 0
# ------------------------------------------------------------------ power-stage sheet
FN = 'WPT-01-TRANSMITTER-TX.kicad_sch'
t = open(FN, encoding='utf-8').read()
for ref in ('R320', 'R323', 'R326', 'R329'):
    j, b = inst(t, ref)
    if getp(b, 'Value') == '0':
        assert getp(b, 'Manufacturer Part Number') == 'RC0402FR-070RL', ref
        nb = setp(setp(b, 'Value', '560R'), 'Manufacturer Part Number', 'RC0402FR-07560RL')
        t = t[:j] + nb + t[j + len(b):]
        changed += 1
_, c301 = inst(t, 'C301')
assert getp(c301, 'Manufacturer Part Number') == 'GCM155R71H104KE02D'
old_lib, new_lib = 'yageo:CC0402KRX7R8BB223', re.search(r'\(lib_id "([^"]+)"\)', c301).group(1)
assert geometry(lib_symbol(t, old_lib)) == geometry(lib_symbol(t, new_lib)), 'the two capacitor symbols differ in shape'
for ref in ('C302', 'C318'):
    j, b = inst(t, ref)
    if getp(b, 'Value') != getp(c301, 'Value'):
        assert '(lib_id "%s")' % old_lib in b, ref
        nb = b.replace('(lib_id "%s")' % old_lib, '(lib_id "%s")' % new_lib, 1)
        for name in ('Value', 'Datasheet', 'Manufacturer', 'Manufacturer Part Number'):
            nb = setp(nb, name, getp(c301, name))
        t = t[:j] + nb + t[j + len(b):]
        changed += 1
open(FN, 'w', encoding='utf-8').write(t)
FNP = 'WPT-01-TRANSMITTER-POWER.kicad_sch'
tp = open(FNP, encoding='utf-8').read()
j, bb = inst(tp, 'R207')
if getp(bb, 'Manufacturer Part Number') == 'RC0402FR-0710KL':
    nb = setp(setp(bb, 'Value', '2.2kF'), 'Manufacturer Part Number', 'RC0402FR-072K2L')
    tp = tp[:j] + nb + tp[j + len(bb):]
    assert tp.count('(') == tp.count(')')
    open(FNP, 'w', encoding='utf-8').write(tp)
    changed += 1
for ref in ('R339', 'R341'):
    j, b = inst(t, ref)
    if getp(b, 'Manufacturer Part Number') == 'RC0402FR-0715KL':
        nb = setp(setp(b, 'Manufacturer', 'Panasonic Electronic Components'), 'Manufacturer Part Number', 'ERJ-PA2F1502X')
        t = t[:j] + nb + t[j + len(b):]
        changed += 1
assert t.count('(') == t.count(')')
open(FN, 'w', encoding='utf-8').write(t)

# ------------------------------------------------------------------ root sheet: the encoder
FN = 'WPT-01-TRANSMITTER.kicad_sch'
t = open(FN, encoding='utf-8').read()
if '(lib_id "Device:RotaryEncoder_Switch")' in t:
    lib = open(STOCK, encoding='utf-8').read()
    i = lib.index('\n\t(symbol "RotaryEncoder_Switch_MP"\n') + 1
    sym = block_at(lib, i + 1).replace('(symbol "RotaryEncoder_Switch_MP"', '(symbol "Device:RotaryEncoder_Switch_MP"', 1)
    sym = '\n'.join('\t' + l for l in ('\t' + sym).split('\n'))
    k = t.index('\n\t\t(symbol "Device:RotaryEncoder_Switch"\n') + 1
    old_sym = block_at(t, k + 2)
    assert t.count('(lib_id "Device:RotaryEncoder_Switch")') == 1
    t = t[:k] + sym + t[k + 2 + len(old_sym):]             # the plain symbol has no other user
    j, b = inst(t, 'SW1')
    assert '(at 101.6 228.6 180)' in b
    nb = b.replace('(lib_id "Device:RotaryEncoder_Switch")', '(lib_id "Device:RotaryEncoder_Switch_MP")', 1)
    m = re.search(r'\t\t\(pin "C"\n\t\t\t\(uuid "[^"]+"\)\n\t\t\)\n', nb)
    nb = nb[:m.end()] + '\t\t(pin "MP"\n\t\t\t(uuid "%s")\n\t\t)\n' % uid() + nb[m.end():]
    t = t[:j] + nb + t[j + len(b):]
    # the MP pin of the symbol (0, -7.62), symbol rotated 180 degrees at (101.6, 228.6): on the sheet at (101.6, 220.98)
    X, Y0, Y1 = 101.6, 220.98, 218.44
    wire = ('\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)\n'
            % (X, Y0, X, Y1, uid()))
    # a ground symbol: copy of the one beside the encoder, turned so that it points up
    gi = t.index('(lib_id "power:GND")\n\t\t(at 109.22 228.6 90)')
    gj = t.rfind('\n\t(symbol\n', 0, gi) + 1
    g = block_at(t, gj)
    nums = [int(n) for n in re.findall(r'"#PWR0*(\d+)"', t)]
    new_ref = '#PWR0%d' % (max(nums) + 1)
    old_ref = getp(g, 'Reference')
    dx, dy = X - 109.22, Y1 - 228.6
    first = [True]

    def move(mm):
        x, y, r = float(mm.group(1)) + dx, float(mm.group(2)) + dy, mm.group(3)
        if first[0]:
            first[0] = False
            r = '180'
        f = lambda v: ('%.4f' % v).rstrip('0').rstrip('.')
        return '(at %s %s %s)' % (f(x), f(y), r)
    g2 = re.sub(r'\(at (-?[\d.]+) (-?[\d.]+) (\d+)\)', move, g)
    g2 = g2.replace('"%s"' % old_ref, '"%s"' % new_ref)
    g2 = re.sub(r'\(uuid "[^"]+"\)', lambda mm: '(uuid "%s")' % uid(), g2)
    k = t.rindex('\n\t(sheet_instances\n') + 1 if '\n\t(sheet_instances\n' in t else t.rindex('\n\t(embedded_fonts') + 1
    t = t[:k] + wire + '\t' + g2.lstrip('\t') + '\n' + t[k:]
    assert t.count('(') == t.count(')')
    open(FN, 'w', encoding='utf-8').write(t)
    changed += 1
print('changes:', changed)
if not changed:
    sys.exit('already applied')

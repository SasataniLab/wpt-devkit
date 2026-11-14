#!/usr/bin/env python3
"""Schematic edit of 2026-11-14, fourth revision, part 2: fast comparators on the board, J301 goes
(run inside the project directory hardware/kicad/WPT-TX).

Until now the two divider taps went to the MCU's own comparators (delay 16.7 ns typical, 31 ns maximum) and to the
header J301, where a small board with fast comparators could be plugged in later. The comparators are now on the board
and J301 is removed.

  U308, U309   TLV3601 (2.5 ns, push-pull, SOT-23-5, 3.3 V). IN+ = VSWA_CMP / VSWB_CMP, the nets behind R343 / R344
               that also go to PA1 / PC1; IN- = ZVS_VTH; outputs through R335 / R337 to HRTIM1_EEV1 / EEV2.
  R335, R337   0 ohm -> 100 ohm: series resistors at the comparator outputs (40 mm of track to the MCU pins).
  R345, C344, C345   threshold: PB11 -> 560 ohm -> ZVS_VTH, 100 nF at each comparator. PB11 is the output of OPAMP6,
               which as a follower repeats DAC3_CH1 - the DAC that is also the threshold of the internal comparators
               COMP1 / COMP3 (RM0440 tables 196 and 211). The net of PB11 is renamed HRTIM1_FLT4 -> ZVS_VTH_DAC; it
               was a spare fault input that only went to J301.
  R334         10 k -> 100 k: PB11 to ground (threshold 0 V while the pin is not driven); 10 k would load the
               operational amplifier with 0.3 mA.     R333 (pull-up, was not fitted) is removed.
  C340, C341   36 pF (C0G, 2 %) from each tap to ground, and
  C338, C339   0.5 pF -> 3.3 pF across the 15 k resistors. The divider is now compensated by capacitors that are large
               against the stray capacitance behind it: 15 k x 3.3 pF = 1 k x (36 pF + about 14 pF of track, MCU pin
               and comparator input; 36 pF is the middle between the two legs and two likely stack-ups). Before, 0.5 pF stood against 12 to 14 pF of stray capacitance alone, the step
               arrived in two parts (60 % at once, the rest with 12 ns), and the value had to be trimmed on the bench.
               R343 / R344 (100 ohm) stay where they are and now feed the track to the comparators as well: they
               terminate it at the source, so that the 36 pF sits at the divider and the line cannot ring.
  C342, C343   100 nF at the supply pins of the comparators.
  TP301 .. TP304   1 mm pads: VSWA_CMP, VSWB_CMP, ZVS_VTH, HRTIM1_FLT3 (what J301 offered for a probe).
  J301         removed.
  TP223        removed: the second +5 V test point (plated hole) beside the leg-B driver stood where C341 has to be.
               TP213, 6 mm away on the same net, stays.

New parts are fitted in the variant HRTIM only (base state "not fitted", like R343 / R344 / C338 / C339 before).
"""
import glob
import re
import sys
import uuid

uid = lambda: str(uuid.uuid4())
TX = 'WPT-01-TRANSMITTER-TX.kicad_sch'
ROOT = 'WPT-01-TRANSMITTER.kicad_sch'
MCU = 'MCU.kicad_sch'
POWER = 'WPT-01-TRANSMITTER-POWER.kicad_sch'
SYMLIB = 'lib/symbols/texas_instruments.kicad_sym'
STOCK = '/usr/share/kicad/symbols/Comparator.kicad_sym'

t = open(TX, encoding='utf-8').read()
if '(property "Reference" "U308"' in t:
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


def setp(b, name, value):
    b2, n = re.subn(r'(\(property "%s" ")((?:[^"\\]|\\.)*)(")' % re.escape(name), lambda m: m.group(1) + value + m.group(3), b, count=1)
    assert n == 1, name
    return b2


def getp(b, name):
    return re.search(r'\(property "%s" "((?:[^"\\]|\\.)*)"' % re.escape(name), b).group(1)


def fmt(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def at_of(b):
    m = re.search(r'\(at (-?[\d.]+) (-?[\d.]+) (\d+)\)', b)
    return float(m.group(1)), float(m.group(2)), int(m.group(3))


def clone(b, x, y, ref, fields=None, field_at=None):
    """copy of a placed symbol at (x, y): every position shifted alike, new identifiers, reference and fields set"""
    x0, y0, _ = at_of(b)
    dx, dy = x - x0, y - y0
    old_ref = getp(b, 'Reference')
    nb = re.sub(r'\(at (-?[\d.]+) (-?[\d.]+) (\d+)\)', lambda m: '(at %s %s %s)' % (fmt(float(m.group(1)) + dx), fmt(float(m.group(2)) + dy), m.group(3)), b)
    nb = re.sub(r'\(uuid "[^"]+"\)', lambda m: '(uuid "%s")' % uid(), nb)
    nb = setp(nb, 'Reference', ref).replace('(reference "%s")' % old_ref, '(reference "%s")' % ref)
    for k, v in (fields or {}).items():
        nb = setp(nb, k, v)
    for k, (fx, fy, fr) in (field_at or {}).items():
        nb, n = re.subn(r'(\(property "%s" "(?:[^"\\]|\\.)*"\n\t\t\t)\(at [-\d.]+ [-\d.]+ \d+\)' % re.escape(k),
                        lambda m: m.group(1) + '(at %s %s %s)' % (fmt(fx), fmt(fy), fr), nb, count=1)
        assert n == 1, k
    assert nb.count('"%s"' % ref) == 2, (ref, nb.count('"%s"' % ref))
    return nb


def wire(*pts):
    out = ''
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        out += ('\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)\n'
                % (fmt(x0), fmt(y0), fmt(x1), fmt(y1), uid()))
    return out


def junction(x, y):
    return '\t(junction\n\t\t(at %s %s)\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "%s")\n\t)\n' % (fmt(x), fmt(y), uid())


def label(name, x, y, rot):
    just = {0: 'left bottom', 180: 'right bottom', 90: 'left bottom', 270: 'right bottom'}[rot]
    return ('\t(label "%s"\n\t\t(at %s %s %d)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n\t)\n'
            % (name, fmt(x), fmt(y), rot, just, uid()))


def hlabel(name, shape, x, y, rot):
    just = {0: 'left', 180: 'right', 90: 'left', 270: 'right'}[rot]
    return ('\t(hierarchical_label "%s"\n\t\t(shape %s)\n\t\t(at %s %s %d)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n\t)\n'
            % (name, shape, fmt(x), fmt(y), rot, just, uid()))


def note(s, x, y):
    return ('\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at %s %s 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)\n'
            % (s.replace('\n', '\\n'), fmt(x), fmt(y), uid()))


def cut(s, pattern, count=1):
    """remove what the regular expression matches, exactly `count` times"""
    s2, n = re.subn(pattern, '', s)
    assert n == count, (pattern[:70], n)
    return s2


def cut_wire(s, a, b):
    for p, q in ((a, b), (b, a)):
        pat = (r'\t\(wire\n\t\t\(pts\n\t\t\t\(xy %s %s\) \(xy %s %s\)\n\t\t\)\n\t\t\(stroke\n\t\t\t\(width 0\)\n\t\t\t\(type default\)\n\t\t\)\n\t\t\(uuid "[^"]+"\)\n\t\)\n'
               % tuple(re.escape(fmt(v)) for v in p + q))
        if re.search(pat, s):
            return cut(s, pat)
    raise AssertionError(('wire', a, b))


def cut_label(s, kind, name, x, y):
    i = s.index('\t(%s "%s"\n' % (kind, name))
    while True:
        b = block_at(s, i + 1)
        if re.search(r'\(at %s %s \d+\)' % (re.escape(fmt(x)), re.escape(fmt(y))), b[:200]):
            return s[:i] + s[i + 1 + len(b) + 1:]
        i = s.index('\t(%s "%s"\n' % (kind, name), i + 1)


def cut_symbol(s, ref):
    j, b = inst(s, ref)
    return s[:j] + s[j + len(b) + 1:]


# ------------------------------------------------------------------ the library symbol of the comparator
stock = open(STOCK, encoding='utf-8').read()
base = block_at(stock, stock.index('\n\t(symbol "MCP6561-OT"\n') + 2)          # pins 1 OUT, 2 V-, 3 +, 4 -, 5 V+: the pinout of the TLV3601
sym = base.replace('"MCP6561-OT', '"TLV3601DBV')
sym = setp(sym, 'Value', 'TLV3601DBV')
sym = setp(sym, 'Datasheet', 'https://www.ti.com/lit/ds/symlink/tlv3601.pdf')
sym = setp(sym, 'Description', '325 MHz high-speed comparator, 2.5 ns propagation delay, push-pull output, SOT-23-5')
sym = setp(sym, 'ki_keywords', 'cmp fast')
m = re.search(r'\t\t\(property "Description" .*?\n\t\t\)\n', sym, re.S)
extra = ''
for name, value in (('Manufacturer', 'Texas Instruments'), ('Manufacturer Part Number', 'TLV3601DBVR')):
    extra += m.group(0).replace('"Description"', '"%s"' % name, 1).replace(getp(sym, 'Description'), value, 1)
sym = sym[:m.end()] + extra + sym[m.end():]
assert sym.count('(') == sym.count(')')
lib = open(SYMLIB, encoding='utf-8').read()
if '(symbol "TLV3601DBV"' not in lib:
    k = lib.rindex('\n)')
    lib = lib[:k] + '\n\t' + sym + lib[k:]
    assert lib.count('(') == lib.count(')')
    open(SYMLIB, 'w', encoding='utf-8').write(lib)
emb = '\n'.join('\t' + l for l in ('\t' + sym).split('\n')).replace('(symbol "TLV3601DBV"\n', '(symbol "texas_instruments:TLV3601DBV"\n', 1)
# the test pad symbol comes from the supply sheet
pw = open(POWER, encoding='utf-8').read()
tp_lib = block_at(pw, pw.index('\n\t\t(symbol "testpooint:TP1.0"\n') + 3)
_, tp_tpl = inst(pw, 'TP216')
i = t.index('\n\t(lib_symbols\n') + 2
k = i + len(block_at(t, i)) - 3                                # before the line that closes (lib_symbols ...)
assert t[k:k + 3] == '\n\t)' and '(symbol "testpooint:TP1.0"' not in t
t = t[:k] + '\n\t\t' + tp_lib + '\n' + emb.rstrip('\n') + t[k:]

# ------------------------------------------------------------------ what goes
t = cut_symbol(t, 'J301')
for i in range(10):
    t = cut_wire(t, (302.26, 220.98 + 2.54 * i), (304.8, 220.98 + 2.54 * i))
for kind, name, y in (('label', 'VSWA_SENSE', 220.98), ('global_label', 'GND', 223.52), ('label', 'VSWB_SENSE', 226.06),
                      ('global_label', 'GND', 228.6), ('label', 'ZVS_A_IN', 231.14), ('label', 'ZVS_B_IN', 233.68),
                      ('hierarchical_label', 'HRTIM1_FLT3', 236.22), ('hierarchical_label', 'HRTIM1_FLT4', 238.76),
                      ('global_label', '+3V3', 241.3), ('global_label', 'GND', 243.84)):
    t = cut_label(t, kind, name, 304.8, y)
t = cut_symbol(t, 'R333')
j, b = inst(t, '#PWR0361')
assert '(at 270.51 241.3 0)' in b
t = cut_symbol(t, '#PWR0361')
t = cut_wire(t, (270.51, 248.92), (270.51, 251.46))
if '(lib_id "Connector:Conn_01x10_Pin")' not in t:              # the embedded copy of the header symbol has no user left
    i = t.index('\n\t\t(symbol "Connector:Conn_01x10_Pin"\n') + 1
    blk = block_at(t, i + 2)
    t = t[:i] + t[i + 2 + len(blk) + 1:]

# ------------------------------------------------------------------ what changes
for ref, value, old_mpn, mpn in (('R334', '100k', 'RC0402FR-0710KL', 'RC0402FR-07100KL'),
                                 ('R335', '100R', 'RC0402FR-070RL', 'RC0402FR-07100RL'), ('R337', '100R', 'RC0402FR-070RL', 'RC0402FR-07100RL'),
                                 ('C338', '3.3p', 'GJM1555C1HR50BB01D', 'GJM1555C1H3R3BB01D'), ('C339', '3.3p', 'GJM1555C1HR50BB01D', 'GJM1555C1H3R3BB01D')):
    j, b = inst(t, ref)
    assert getp(b, 'Manufacturer Part Number') == old_mpn, (ref, getp(b, 'Manufacturer Part Number'))
    t = t[:j] + setp(setp(b, 'Value', value), 'Manufacturer Part Number', mpn) + t[j + len(b):]
# PB11: the name of the net and the direction of its sheet pin
old = '\t(hierarchical_label "HRTIM1_FLT4"\n\t\t(shape output)'
assert t.count(old) == 1
t = t.replace(old, '\t(hierarchical_label "ZVS_VTH_DAC"\n\t\t(shape input)')

# ------------------------------------------------------------------ what comes
nums = []
for fn in glob.glob('*.kicad_sch'):
    nums += [int(n) for n in re.findall(r'"#PWR0*(\d+)"', open(fn, encoding='utf-8').read())]
pwr_n = [max(nums)]
_, gnd_tpl = inst(t, '#PWR0360')
_, v33_tpl = inst(t, '#PWR0359')
assert '(lib_id "power:GND")' in gnd_tpl and '(lib_id "power:+3.3V")' in v33_tpl


def power(tpl, x, y):
    pwr_n[0] += 1
    return '\t' + clone(tpl, x, y, '#PWR0%d' % pwr_n[0]).lstrip('\t') + '\n'


_, c_tpl = inst(t, 'C338')                    # Device:C, 0402, "not fitted" with the HRTIM variant fitted
_, r_tpl = inst(t, 'R343')                    # Device:R lying (rotated 90), same population
assert '(name "HRTIM")' in c_tpl and '(name "HRTIM")' in r_tpl and at_of(r_tpl)[2] == 90
SHEET_PATH = re.search(r'\(path "([^"]+)"', c_tpl).group(1)
C100N = {'Value': '100n', 'Manufacturer': 'Murata Electronics', 'Manufacturer Part Number': 'GCM155R71H104KE02D'}
C36P = {'Value': '36p', 'Manufacturer': 'Murata Electronics', 'Manufacturer Part Number': 'GCM1555C1H360GA16D'}


def cap(ref, x, y, fields):
    return '\t' + clone(c_tpl, x, y, ref, fields).lstrip('\t') + '\n'


def comparator(ref, x, y):
    b = clone(c_tpl, x, y, ref, {'Value': 'TLV3601DBV', 'Footprint': 'Package_TO_SOT_SMD:SOT-23-5',
                                 'Datasheet': 'https://www.ti.com/lit/ds/symlink/tlv3601.pdf',
                                 'Description': '325 MHz high-speed comparator, 2.5 ns propagation delay, push-pull output, SOT-23-5',
                                 'Manufacturer': 'Texas Instruments', 'Manufacturer Part Number': 'TLV3601DBVR'},
              {'Reference': (x + 3.81, y - 6.35, 0), 'Value': (x + 9.525, y + 3.81, 0)})
    b = b.replace('(lib_id "Device:C")', '(lib_id "texas_instruments:TLV3601DBV")', 1)
    pins = ''.join('\t\t(pin "%d"\n\t\t\t(uuid "%s")\n\t\t)\n' % (n, uid()) for n in range(1, 6))
    b, n = re.subn(r'\t\t\(pin "1"\n\t\t\t\(uuid "[^"]+"\)\n\t\t\)\n\t\t\(pin "2"\n\t\t\t\(uuid "[^"]+"\)\n\t\t\)\n', lambda m: pins, b)
    assert n == 1
    return '\t' + b.lstrip('\t') + '\n'


def testpad(ref, x, y, ref_at):
    b = clone(tp_tpl, x, y, ref, None, {'Reference': (ref_at[0], ref_at[1], 0)})
    b = re.sub(r'\(path "[^"]+"', '(path "%s"' % SHEET_PATH, b)
    b, n = re.subn(r'(\(property "Value" "TP1\.0"\n\t\t\t\(at [^)]*\)\n)', lambda m: m.group(1) + '\t\t\t(hide yes)\n', b, count=1)   # the pad needs no value text
    assert n == 1
    return '\t' + b.lstrip('\t') + '\n'


new = ''
# U308 (leg A) at (314.96, 220.98): + (307.34, 218.44), - (307.34, 223.52), V+ (312.42, 213.36), V- (312.42, 228.6), OUT (322.58, 220.98)
new += comparator('U308', 314.96, 220.98) + power(v33_tpl, 312.42, 213.36) + power(gnd_tpl, 312.42, 228.6)
new += wire((307.34, 218.44), (304.8, 218.44), (302.26, 218.44)) + junction(304.8, 218.44) + testpad('TP301', 304.8, 218.44, (302.8, 215.0))
new += hlabel('VSWA_CMP', 'output', 302.26, 218.44, 180)
new += wire((307.34, 223.52), (304.8, 223.52)) + label('ZVS_VTH', 304.8, 223.52, 180)
new += wire((322.58, 220.98), (335.28, 220.98))                                     # ends on the stub that carries the label ZVS_A_IN
# U309 (leg B) at (322.58, 238.76): + (314.96, 236.22), - (314.96, 241.3), V+ (320.04, 231.14), V- (320.04, 246.38), OUT (330.2, 238.76)
new += comparator('U309', 322.58, 238.76) + power(v33_tpl, 320.04, 231.14) + power(gnd_tpl, 320.04, 246.38)
new += wire((314.96, 236.22), (309.88, 236.22), (307.34, 236.22)) + junction(309.88, 236.22) + testpad('TP302', 309.88, 236.22, (308.0, 238.5))
new += hlabel('VSWB_CMP', 'output', 307.34, 236.22, 180)
new += wire((314.96, 241.3), (312.42, 241.3)) + label('ZVS_VTH', 312.42, 241.3, 180)
new += wire((330.2, 238.76), (332.74, 238.76), (332.74, 236.22), (335.28, 236.22))   # up to the stub with the label ZVS_B_IN
# threshold: PB11 (node of R334 at (270.51, 251.46)) -> R345 -> ZVS_VTH with C344 / C345 and TP303
r345 = clone(r_tpl, 281.94, 251.46, 'R345', {'Value': '560R', 'Manufacturer Part Number': 'RC0402FR-07560RL'},
             {'Reference': (278.13, 248.92, 90), 'Value': (285.75, 248.92, 90)})
new += '\t' + r345.lstrip('\t') + '\n'
new += wire((270.51, 251.46), (278.13, 251.46))
new += wire((285.75, 251.46), (287.02, 251.46), (295.91, 251.46), (298.45, 251.46)) + junction(287.02, 251.46) + junction(295.91, 251.46)
new += label('ZVS_VTH', 288.29, 251.46, 0) + testpad('TP303', 298.45, 251.46, (296.45, 248.06))
new += cap('C344', 287.02, 255.27, C100N) + power(gnd_tpl, 287.02, 259.08)
c345 = clone(c_tpl, 295.91, 255.27, 'C345', C100N, {'Reference': (291.5, 254.0, 0), 'Value': (291.5, 256.54, 0)})
new += '\t' + c345.lstrip('\t') + '\n' + power(gnd_tpl, 295.91, 259.08)
# supply decoupling of the two comparators
for ref, x in (('C342', 281.94), ('C343', 292.1)):
    new += cap(ref, x, 273.05, C100N) + power(v33_tpl, x, 269.24) + power(gnd_tpl, x, 276.86)
# the spare fault input keeps a pad
new += wire((270.51, 220.98), (278.13, 220.98)) + testpad('TP304', 278.13, 220.98, (276.13, 217.58))
# capacitors from the taps to ground, beside R340 / R342
new += cap('C340', 363.22, 233.68, C36P) + wire((363.22, 229.87), (368.3, 229.87)) + wire((363.22, 237.49), (368.3, 237.49))
new += junction(368.3, 229.87) + junction(368.3, 237.49)
new += cap('C341', 383.54, 233.68, C36P) + wire((383.54, 229.87), (388.62, 229.87)) + wire((383.54, 237.49), (388.62, 237.49))
new += junction(388.62, 229.87) + junction(388.62, 237.49)
new += note('ZVS detection, revision 4:\n'
            'U308 / U309 sit on the divider taps behind\n'
            'R343 / R344 (shared with PA1 / PC1).\n'
            'Threshold ZVS_VTH: PB11 = OPAMP6 output,\n'
            'follower of DAC3_CH1.\n'
            'Divider: 15k || 3.3p over 1k || (36p + 14p\n'
            'of track and inputs). C342 / C343: supply\n'
            'decoupling of U308 / U309.', 226.06, 285.0)
k = t.rindex(')')                                    # a sub-sheet ends with its last item; new items go before the closing bracket
t = t[:k] + new + t[k:]
assert t.count('(') == t.count(')')
open(TX, 'w', encoding='utf-8').write(t)

# ------------------------------------------------------------------ the other sheets: name and direction of the PB11 net
r = open(ROOT, encoding='utf-8').read()
assert r.count('(pin "HRTIM1_FLT4" output') == 1 and r.count('(pin "HRTIM1_FLT4" input') == 1 and r.count('(label "HRTIM1_FLT4"') == 2
r = r.replace('(pin "HRTIM1_FLT4" output', '(pin "ZVS_VTH_DAC" input').replace('(pin "HRTIM1_FLT4" input', '(pin "ZVS_VTH_DAC" output')
r = r.replace('(label "HRTIM1_FLT4"', '(label "ZVS_VTH_DAC"')
open(ROOT, 'w', encoding='utf-8').write(r)
mc = open(MCU, encoding='utf-8').read()
i = mc.index('\t(hierarchical_label "HRTIM1_FLT4"\n')
hb = block_at(mc, i + 1)
assert '(shape input)' in hb, hb[:120]
mc = mc[:i + 1] + hb.replace('"HRTIM1_FLT4"', '"ZVS_VTH_DAC"', 1).replace('(shape input)', '(shape output)', 1) + mc[i + 1 + len(hb):]
open(MCU, 'w', encoding='utf-8').write(mc)
# ------------------------------------------------------------------ supply sheet: the second +5 V test point goes
# TP223 (a plated hole on +5 V beside the leg-B driver) sits where C341 has to be; TP213, 6 mm away on the same net, stays.
pw = open(POWER, encoding='utf-8').read()
j, b = inst(pw, 'TP223')
assert '(at 257.81 223.52 0)' in b
pw = cut_symbol(pw, 'TP223')
if not re.search(r'\(junction\n\t\t\(at 257\.81 223\.52\)', pw):          # three wires met on its pin
    k = pw.rindex(')')
    pw = pw[:k] + junction(257.81, 223.52) + pw[k:]
assert pw.count('(') == pw.count(')')
open(POWER, 'w', encoding='utf-8').write(pw)
print('applied; power symbols up to #PWR0%d' % pwr_n[0])

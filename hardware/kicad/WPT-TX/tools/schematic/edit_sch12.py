#!/usr/bin/env python3
"""Schematic edit of 2026-11-18, eighth revision (run inside the project directory hardware/kicad/WPT-TX).

The board is to run from one 36 V adapter (XP Power ACM36US36: 36.0 V, 1 A, total regulation +/-5 %, plug 5.5 x 2.5 mm)
and VPP is to reach about 35 V. What the first prototype carried for trying things out goes, except the 2020 drive
path (Si5351 and the 74LVC gates), which stays as the fall-back for the HRTIM.

Input
  CN207          removed. The 7 V converter (U207) is fed from the input net directly.
  J202           in parallel with the jack J201 through D204 (S210FA, as D202 / D203): reverse protection of the
                 hand-wired input, and the adapter cannot feed back into whatever hangs on the pins.
  CN203          pin 3 (was: J202) is no longer connected. Jumper on 1-2 = VPP from the converter, on 2-3 = parked.
  DC_IN          name of the input net (jack, both converters, V+ of the pot, divider of ADC_VDC).
  C224           100 uF / 50 V aluminium electrolytic at the jack. Plugging a live adapter into ceramic capacitors alone
                 rings to 55 .. 65 V (cable 1 .. 1.5 uH, 0.1 .. 0.2 ohm; TS30042: 42 V absolute maximum); with 100 uF
                 and 0.3 ohm in parallel the ringing is gone. New library symbol Device:C_Polarized.
  J201           54-00129 (plug 5.5 x 2.1 mm) -> 54-00130 (5.5 x 2.5 mm, the plug of the ACM36). Same land pattern.
VPP
  R210           3.9 k -> 2.0 k: VPP = 0.9 V x (1 + (Rab + 100) / 2.0 k); 35 V at Rab = 76 k, reached even by a pot at
                 -20 %. The converter itself ends about 1.5 V below its input. Power-on default (mid-scale): 23 V.
I2C at 3.3 V
  U202 (PCA9306), R214, C210, R217, R218   removed.
  U203 (PAC1720) VDD, U204 (MCP45HV51) VL and SHDN   +5V -> +3V3 (3.0 .. 5.5 V and 2.7 .. 5.5 V by their datasheets).
  R221, R222     now fitted (0 ohm): they join the section of U203 / U204 to the MCU's bus, as R219 / R220 join the
                 section of the Si5351. The net names SCL_5V / SDA_5V stay.
  R215, R216     10 k -> 4.7 k (one pair of pull-ups for the whole bus).
Smaller things
  CN209, CN210   removed (three identical 5 V headers; CN208 stays).
  ~{WLAT}        R223 and the line to the MCU (PB1) removed; R225 holds the pin low, so a write takes effect at once.
  R226           (27 mohm in the 5 V rail, current reading of the logic supply) removed; the LDO output is +5V.
  J4             (UART header, never fitted) removed; the UART is on the debug connector J3.
Notes on the sheet rewritten where they named the old values.

Run once; a second run stops with "already applied".
"""
import re
import sys
import uuid

sys.path.insert(0, __file__.rsplit('/', 1)[0])
import sx

ROOT, MCU, PW = 'WPT-01-TRANSMITTER.kicad_sch', 'MCU.kicad_sch', 'WPT-01-TRANSMITTER-POWER.kicad_sch'
DEVICE_LIB = '/usr/share/kicad/symbols/Device.kicad_sym'
R = lambda v: round(float(v), 3)
fmt = lambda v: ('%.4f' % v).rstrip('0').rstrip('.')
uid = lambda: str(uuid.uuid4())


class Sch:
    def __init__(self, path):
        self.path = path
        self.s = open(path, encoding='utf-8').read()
        self.log = []

    # ---------------------------------------------------------------- finding
    def kids(self, name):
        return sx.parse(self.s).kids(name)

    def wire(self, a, b):
        for w in self.kids('wire'):
            pts = [(R(p.a(0)), R(p.a(1))) for p in w.kid('pts').kids('xy')]
            if {pts[0], pts[-1]} == {a, b}:
                return w
        raise KeyError('wire %s %s' % (a, b))

    def at(self, name, p, first=None):
        for n in self.kids(name):
            q = n.kid('at')
            if (R(q.a(0)), R(q.a(1))) == p and (first is None or n.a(0) == first):
                return n
        raise KeyError('%s at %s %s' % (name, p, first or ''))

    def symbol(self, ref):
        for n in self.kids('symbol'):
            for pr in n.kids('property'):
                if pr.a(0) == 'Reference' and pr.a(1) == ref:
                    return n
        raise KeyError(ref)

    def power(self, value, p):
        for n in self.kids('symbol'):
            if n.val('lib_id', '').startswith('power:') and (R(n.kid('at').a(0)), R(n.kid('at').a(1))) == p:
                assert [pr.a(1) for pr in n.kids('property') if pr.a(0) == 'Value'] == [value], (value, p)
                return n
        raise KeyError('power %s %s' % (value, p))

    # ---------------------------------------------------------------- editing
    def cut(self, n, tabs=1):
        lead = '\n' + '\t' * tabs
        assert self.s[n.start - len(lead):n.start] == lead, self.s[n.start - 6:n.start + 30]
        self.s = self.s[:n.start - len(lead)] + self.s[n.end:]

    def add(self, text):
        k = self.s.rindex('\n\t(embedded_fonts') if '\n\t(embedded_fonts' in self.s else self.s.rindex('\n)')
        for mark in ('\n\t(sheet_instances', '\n\t(symbol_instances'):
            if mark in self.s:
                k = min(k, self.s.rindex(mark))
        self.s = self.s[:k] + '\n\t' + text + self.s[k:]

    def del_wire(self, a, b): self.cut(self.wire(a, b))
    def del_junction(self, p): self.cut(self.at('junction', p))
    def del_symbol(self, ref): self.cut(self.symbol(ref))
    def del_power(self, value, p): self.cut(self.power(value, p))
    def del_label(self, kind, name, p): self.cut(self.at(kind, p, name))

    def add_wire(self, a, b):
        self.add('(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)'
                 % (fmt(a[0]), fmt(a[1]), fmt(b[0]), fmt(b[1]), uid()))

    def add_junction(self, p):
        self.add('(junction\n\t\t(at %s %s)\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "%s")\n\t)' % (fmt(p[0]), fmt(p[1]), uid()))

    def add_nc(self, p):
        self.add('(no_connect\n\t\t(at %s %s)\n\t\t(uuid "%s")\n\t)' % (fmt(p[0]), fmt(p[1]), uid()))

    def add_text(self, text, p):
        self.add('(text %s\n\t\t(exclude_from_sim no)\n\t\t(at %s %s 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)'
                 % (sx.quote(text), fmt(p[0]), fmt(p[1]), uid()))

    def text(self, old, p=None):
        hit = [n for n in self.kids('text') if n.a(0) == old and (p is None or (R(n.kid('at').a(0)), R(n.kid('at').a(1))) == p)]
        assert len(hit) == 1, (old, p, len(hit))
        return hit[0]

    def set_text(self, old, new, p=None, move=None):
        n = self.text(old, p)
        a, at = n.atoms()[0], n.kid('at')
        if move:                                                # the later edit first: the offsets of the earlier one stay valid
            self.s = self.s[:at.start] + '(at %s %s 0)' % (fmt(move[0]), fmt(move[1])) + self.s[at.end:]
        self.s = self.s[:a.start] + sx.quote(new) + self.s[a.end:]

    def del_text(self, old, p=None):
        self.cut(self.text(old, p))

    def replace_node(self, n, text):
        self.s = self.s[:n.start] + text + self.s[n.end:]

    def save(self):
        assert self.s.count('(') == self.s.count(')'), self.path
        sx.parse(self.s)
        open(self.path, 'w', encoding='utf-8').write(self.s)


PROP = r'\(property "%s" "(?:[^"\\]|\\.)*"'


def setp(block, name, value):
    new, k = re.subn(PROP % re.escape(name), lambda _: '(property "%s" %s' % (name, sx.quote(value)), block, count=1)
    assert k == 1, name
    return new


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


def add_prop(block, after, name, value):
    """a hidden field `name`, a copy of the field `after`, placed behind it"""
    j, k = prop_block(block, after)
    new = setp(block[j:k], after, value).replace('(property "%s"' % after, '(property "%s"' % name, 1)
    if '(hide yes)' not in new:
        new = re.sub(r'(\n\t\t\t\(at [^)]*\))', r'\1\n\t\t\t(hide yes)', new, count=1)
    return block[:k] + '\n\t\t' + new + block[k:]


def set_prop_at(block, name, x, y, rot=0):
    j, k = prop_block(block, name)
    new = re.sub(r'\(at [^)]*\)', '(at %s %s %s)' % (fmt(x), fmt(y), rot), block[j:k], count=1)
    return block[:j] + new + block[k:]


def clone(block, old_ref, new_ref, dx, dy):
    """a copy of a symbol instance, moved, with new identifiers"""
    b = re.sub(r'\(at (-?[\d.]+) (-?[\d.]+) (\d+)\)', lambda q: '(at %s %s %s)' % (fmt(float(q.group(1)) + dx), fmt(float(q.group(2)) + dy), q.group(3)), block)
    b = re.sub(r'\(uuid "[^"]+"\)', lambda _: '(uuid "%s")' % uid(), b)
    b = b.replace('(property "Reference" "%s"' % old_ref, '(property "Reference" "%s"' % new_ref, 1).replace('(reference "%s")' % old_ref, '(reference "%s")' % new_ref)
    assert b.count('"%s"' % new_ref) == 2, new_ref
    return b


pw, root, mcu = Sch(PW), Sch(ROOT), Sch(MCU)
if '(property "Reference" "D204"' in pw.s:
    sys.exit('already applied')
used = set(re.findall(r'"(#PWR\d+)"', ''.join(open(f, encoding='utf-8').read() for f in (ROOT, MCU, PW, 'WPT-01-TRANSMITTER-TX.kicad_sch'))))
NEW_PWR = '#PWR0291'
assert NEW_PWR not in used and '"C224"' not in pw.s

# ================================================================= input
pw.del_symbol('CN207')
for a, b in (((57.15, 184.15), (64.77, 184.15)), ((57.15, 186.69), (64.77, 186.69)), ((57.15, 189.23), (59.69, 189.23)),
             ((59.69, 189.23), (196.85, 189.23)), ((196.85, 55.88), (196.85, 189.23)), ((64.77, 184.15), (64.77, 137.16))):
    pw.del_wire(a, b)
pw.del_junction((59.69, 189.23))
pw.add_wire((64.77, 137.16), (64.77, 181.61))
pw.add_wire((64.77, 181.61), (64.77, 186.69))                 # the 7 V converter now hangs on the input
pw.add_junction((64.77, 181.61))
pw.add_nc((196.85, 55.88))                                     # CN203 pin 3
pw.del_text('Select by Jumber', (33.02, 185.42))                # the note of CN207
# D204: J202 -> input. A copy of D202 (cathode up), anode on the line that comes up from J202
d202 = pw.symbol('D202').text(pw.s)
assert '(at 133.35 71.12 270)' in d202
d204 = clone(d202, 'D202', 'D204', 59.69 - 133.35, 185.42 - 71.12)
d204 = set_prop_at(set_prop_at(d204, 'Reference', 54.61, 184.785), 'Value', 56.515, 183.515)   # both read upwards, left of the diode
pw.add(d204)
pw.add_wire((59.69, 182.88), (59.69, 181.61))
pw.add_wire((59.69, 181.61), (64.77, 181.61))
pw.add_wire((59.69, 187.96), (59.69, 189.23))
pw.del_power('PWR_FLAG', (73.66, 223.52))                      # the input net keeps the flag at the jack
pw.log.append('CN207 removed, U207 on the input net, J202 through D204, CN203 pin 3 open')

# C224: polarised capacitor from the system library, on the input wire between the jack and C201
lib = open(DEVICE_LIB, encoding='utf-8').read()
i = lib.index('\n\t(symbol "C_Polarized"\n') + 2
node = [n for n in sx.parse(lib).kids('symbol') if n.a(0) == 'C_Polarized'][0]
cp = lib[node.start:node.end].replace('(symbol "C_Polarized"', '(symbol "Device:C_Polarized"', 1)
assert node.start == i and 'Device:C_Polarized' not in pw.s
cp = cp.replace('\n', '\n\t')
k = sx.parse(pw.s).kid('lib_symbols').end - 1                  # before the closing parenthesis of lib_symbols
assert pw.s[k - 2:k + 1] == '\n\t)', repr(pw.s[k - 4:k + 1])
pw.s = pw.s[:k - 2] + '\n\t\t' + cp + pw.s[k - 2:]
c201 = pw.symbol('C201').text(pw.s)
assert '(at 86.36 71.12 0)' in c201
c224 = clone(c201, 'C201', 'C224', 73.66 - 86.36, 0).replace('(lib_id "samsung:CL31A106KBHNNNE")', '(lib_id "Device:C_Polarized")')
for name, value in (('Value', '100u/50(AL)'), ('Footprint', 'Capacitor_SMD:CP_Elec_8x10'),
                    ('Datasheet', 'https://industrial.panasonic.com/cdbs/www-data/pdf/RDE0000/ABA0000C1181.pdf'),
                    ('Description', 'Aluminium electrolytic capacitor, 100 uF, 50 V, 8 x 10.2 mm, surface mount'),
                    ('Size', '8x10.2'), ('Manufacturer', 'Panasonic'), ('Manufacturer Part Number', 'EEE-FK1H101P')):
    c224 = setp(c224, name, value)
c224 = add_prop(c224, 'Manufacturer Part Number', 'Assembly Note',
                'Polarised: pad 1 is +, the marked side of the can goes to GND. Damps the plug-in overshoot of the 36 V input: must be fitted. '
                'Alternative: Nichicon UCD1H101MNL1GS')
c224 = set_prop_at(set_prop_at(c224, 'Reference', 69.85, 76.2, 90), 'Value', 71.755, 76.2, 90)
j, k = prop_block(c224, 'Description')
assert '(hide yes)' not in c224[j:k]
c224 = c224[:j] + re.sub(r'(\n\t\t\t\(at [^)]*\))', r'\1\n\t\t\t(hide yes)', c224[j:k], count=1) + c224[k:]
pw.add(c224)
gnd = clone(pw.power('GND', (86.36, 76.2)).text(pw.s), '#PWR0205', NEW_PWR, 73.66 - 86.36, 0)
pw.add(gnd)
pw.del_wire((64.77, 66.04), (80.01, 66.04))
pw.add_wire((64.77, 66.04), (73.66, 66.04))
pw.add_wire((73.66, 66.04), (80.01, 66.04))
pw.add_junction((73.66, 66.04))
pw.add_wire((73.66, 67.31), (73.66, 66.04))
pw.add_wire((73.66, 74.93), (73.66, 76.2))
pw.add('(label "DC_IN"\n\t\t(at 66.04 66.04 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)' % uid())
pw.log.append('C224 (100 uF / 50 V) at the input')

# J201: the jack for 5.5 x 2.5 mm plugs
n = pw.symbol('J201')
b = n.text(pw.s)
b = setp(setp(setp(b, 'Value', '54-00130'), 'Manufacturer Part Number', '54-00130'), 'Datasheet', 'https://tensility.s3.amazonaws.com/uploads/pdffiles/54-00130.pdf')
b = add_prop(b, 'Manufacturer Part Number', 'Assembly Note',
             'For plugs 5.5 x 2.5 mm (XP Power ACM36US36). Land pattern identical to 54-00129 (the version for 5.5 x 2.1 mm plugs), whose footprint is used')
pw.replace_node(n, b)
pw.log.append('J201 -> 54-00130')

# ================================================================= VPP up to 35 V
n = pw.symbol('R210')
b = n.text(pw.s)
assert '"Value" "3.9kF"' in b
pw.replace_node(n, setp(setp(b, 'Value', '2.0kF'), 'Manufacturer Part Number', 'RC0402FR-072KL'))
pw.log.append('R210 3.9 k -> 2.0 k')

# ================================================================= I2C at 3.3 V
for ref in ('U202', 'R214', 'C210', 'R217', 'R218'):
    pw.del_symbol(ref)
for value, p in (('+5V', (365.76, 104.14)), ('GND', (342.9, 129.54)), ('GND', (365.76, 129.54)), ('PWR_FLAG', (365.76, 114.3))):
    pw.del_power(value, p)
for a, b in (((342.9, 129.54), (342.9, 114.3)), ((342.9, 114.3), (344.17, 114.3)), ((344.17, 116.84), (341.63, 116.84)), ((341.63, 116.84), (341.63, 105.41)),
             ((330.2, 119.38), (344.17, 119.38)), ((336.55, 121.92), (344.17, 121.92)), ((365.76, 107.95), (365.76, 105.41)), ((365.76, 105.41), (372.11, 105.41)),
             ((364.49, 116.84), (365.76, 116.84)), ((365.76, 114.3), (365.76, 116.84)), ((364.49, 121.92), (378.46, 121.92)), ((365.76, 110.49), (365.76, 114.3)),
             ((364.49, 119.38), (372.11, 119.38)), ((372.11, 119.38), (383.54, 119.38)), ((386.08, 146.05), (386.08, 121.92)), ((365.76, 105.41), (365.76, 104.14)),
             ((372.11, 105.41), (378.46, 105.41)), ((378.46, 116.84), (378.46, 121.92)), ((364.49, 114.3), (365.76, 114.3)), ((372.11, 116.84), (372.11, 119.38)),
             ((386.08, 121.92), (378.46, 121.92)), ((365.76, 129.54), (365.76, 127.0)), ((365.76, 116.84), (365.76, 124.46)), ((378.46, 105.41), (378.46, 114.3)),
             ((372.11, 105.41), (372.11, 114.3)), ((383.54, 119.38), (383.54, 143.51)), ((320.04, 143.51), (383.54, 143.51)), ((317.5, 146.05), (386.08, 146.05))):
    pw.del_wire(a, b)
pw.add_wire((320.04, 143.51), (321.31, 143.51))               # the labels SCL_5V / SDA_5V now end these two lines
pw.add_wire((317.5, 146.05), (321.31, 146.05))
for p in ((330.2, 119.38), (336.55, 121.92), (365.76, 114.3), (378.46, 121.92), (372.11, 105.41), (372.11, 119.38), (365.76, 105.41), (365.76, 116.84), (341.63, 105.41)):
    pw.del_junction(p)
for ref in ('R221', 'R222'):
    n = pw.symbol(ref)
    b = n.text(pw.s)
    assert '(dnp yes)' in b and '"Value" "OPEN"' in b
    pw.replace_node(n, setp(b.replace('(dnp yes)', '(dnp no)', 1), 'Value', '0'))
for ref in ('R215', 'R216'):
    n = pw.symbol(ref)
    b = n.text(pw.s)
    assert '"Value" "10kF"' in b
    pw.replace_node(n, setp(setp(b, 'Value', '4.7kF'), 'Manufacturer Part Number', 'RC0402FR-074K7L'))
for p in ((101.6, 142.24), (96.52, 172.72), (203.2, 127.0)):     # VL and SHDN of U204, VDD of U203
    n = pw.power('+5V', p)
    b = n.text(pw.s)
    pw.replace_node(n, setp(b.replace('(lib_id "power:+5V")', '(lib_id "power:+3.3V")', 1), 'Value', '+3V3'))
pw.add_text('I2C at 3.3 V (revision 8): U203 and the logic side of U204 run from +3V3.\nR219 .. R222 (0 ohm) join the three sections of the bus;\n'
            'the names SCL_5V / SDA_5V are kept from the 5 V bus of 2020.', (289.56, 157.48))
pw.log.append('PCA9306 and its parts removed; U203 / U204 logic from +3V3; R221 / R222 fitted; R215 / R216 4.7 k')

# ================================================================= CN209, CN210
for ref in ('CN209', 'CN210'):
    pw.del_symbol(ref)
for a, b in (((254.0, 254.0), (248.92, 254.0)), ((254.0, 256.54), (251.46, 256.54)), ((254.0, 260.35), (248.92, 260.35)), ((254.0, 262.89), (251.46, 262.89)),
             ((248.92, 247.65), (248.92, 254.0)), ((248.92, 260.35), (248.92, 254.0)), ((251.46, 250.19), (251.46, 256.54)), ((251.46, 256.54), (251.46, 262.89))):
    pw.del_wire(a, b)
pw.add_wire((251.46, 250.19), (251.46, 262.89))
for p in ((248.92, 254.0), (251.46, 256.54)):
    pw.del_junction(p)
pw.set_text('+5V/GND Through Holes for External Devices', '+5V / GND for external devices')
pw.log.append('CN209, CN210 removed')

# ================================================================= ~{WLAT} tied low at the pot
pw.del_symbol('R223')
pw.del_wire((78.74, 176.53), (86.36, 176.53))
pw.del_wire((88.9, 176.53), (91.44, 176.53))
pw.del_junction((91.44, 176.53))
pw.del_label('hierarchical_label', '~{WLAT}', (78.74, 176.53))
pw.del_label('label', '~{WLAT}', (80.01, 176.53))
done = 0
for name, p in (('~{WLAT}', (168.91, 162.56)), ('GPIO_N_WLAT', (134.62, 162.56))):    # one sheet pin at a time: the offsets move
    for sheet in sx.parse(root.s).kids('sheet'):
        hit = [q for q in sheet.kids('pin') if q.a(0) == name and (R(q.kid('at').a(0)), R(q.kid('at').a(1))) == p]
        if hit:
            root.cut(hit[0], tabs=2)
            done += 1
            break
assert done == 2, done
root.del_wire((134.62, 162.56), (168.91, 162.56))
n = mcu.at('hierarchical_label', (172.72, 116.84), 'GPIO_N_WLAT')
u = n.val('uuid')
mcu.replace_node(n, '(no_connect\n\t\t(at 172.72 116.84)\n\t\t(uuid "%s")\n\t)' % u)
pw.log.append('~{WLAT}: R223 and the line to the MCU removed (PB1 free)')

# ================================================================= R226
pw.del_symbol('R226')
pw.add_wire((232.41, 223.52), (234.95, 223.52))
pw.del_power('PWR_FLAG', (242.57, 223.52))                     # +5V is now driven by the output pin of the LDO itself
pw.log.append('R226 removed')

# ================================================================= J4 (root sheet)
root.del_symbol('J4')
root.del_power('+3V3', (86.36, 137.16))
root.del_power('GND', (83.82, 137.16))
root.del_wire((91.44, 137.16), (91.44, 147.32))
root.del_wire((88.9, 137.16), (88.9, 147.32))
root.add_wire((91.44, 142.24), (91.44, 147.32))
root.add_wire((88.9, 144.78), (88.9, 147.32))
root.del_junction((91.44, 142.24))
root.del_junction((88.9, 144.78))
pw.log.append('J4 removed')

# ================================================================= notes
pw.set_text('12-24V DC Input', 'DC input 36 V (34.2 .. 37.8 V)\ncentre positive, plug 5.5 x 2.5 mm\n(XP Power ACM36US36)', move=(13.97, 93.98))
pw.set_text('Throught Hole\nfor External DC Input\n(24-40 V)', 'Pin input, parallel to\nthe jack through D204.\n36 V, pin 1 = +', move=(20.32, 237.49))
pw.set_text('Vout\n = 24 V(@Rab: 100k ohm)\n = 0.9V(@Rab: 0 ohm)',
            'Vout = 0.9 V x (1 + (Rab + 100) / 2.0k)\n = 35 V at Rab = 76k, 0.95 V at Rab = 0\nends about 1.5 V below the input;\nkeep >= 2.4 V (input / 16)', move=(140.97, 55.88))
pw.set_text('24V full-scale\nADC_VDC = 24 * 3.6k / (3.6k + 75k) = 1.099 V', '36 V input\nADC_VDC = 36 * 3.6k / (3.6k + 75k) = 1.649 V')
pw.set_text('Ext. DC Input < 40 V', 'VPP link')
pw.set_text('Select by Jumber', 'jumper 1-2: VPP on, 2-3: parked (VPP off)', (186.69, 48.26))
pw.set_text('V+ to V-: 40V(abs,max)', 'V+: 36 V specified, 40 V abs. max (input: up to 37.8 V)')

for sch in (pw, root, mcu):
    sch.save()
print('\n'.join(pw.log))

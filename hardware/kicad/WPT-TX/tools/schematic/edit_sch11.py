#!/usr/bin/env python3
"""Schematic edit of 2026-11-17, seventh revision (run inside the project directory hardware/kicad/WPT-TX).

1. Switch-node detection.
   Before: complete divider at the half bridge -> 100 ohm -> one line of 55 / 80 mm -> comparator at the top edge, MCU pin, test pad.
   Now:    only the upper leg (15 kohm || 3.3 pF) and the 100 ohm (R343 / R344) stay at the half bridge. The line carries the
           node behind the 100 ohm, and the lower leg (1 kohm || C340 / C341) sits at the comparator input. Divider and
           comparator share one ground; the 100 ohm terminates the line at its source.
     R340, C340 (leg A), R342, C341 (leg B)   from the tap VSWx_SENSE to the comparator net VSWx_CMP
     PA1 / PC1 (MCU)   no longer connected: the lines to the MCU's own comparators would hang on the divider. With them go
                       the sheet pins; VSWA_CMP / VSWB_CMP are now nets inside the transmitter sheet
     C340 / C341       36 pF -> 47 pF: the lower leg now also carries the line (firmware/tools/sense_tap_sim.py)

2. J2 becomes a header of 2 x 6 pins (2.54 mm). Pin n keeps its net, so the odd pins form one row and the even pins the
   other. The symbol stays the column of twelve pins; value, description and a note say that the part has two rows.

3. Clock link R346 (0 ohm, not fitted) from CLK1 of the Si5351 (U306 pin 9) to PF0 of the MCU (net HSE_EXT, a global
   label). Fitted - and Y1 removed - it lets the Si5351 clock the MCU, which makes the HRTIM frequency adjustable in
   fine steps (the period register alone gives steps of 8.5 kHz).

Each edit is skipped if the schematic already has it.
"""
import re
import sys
import uuid

ROOT, MCU, TX = 'WPT-01-TRANSMITTER.kicad_sch', 'MCU.kicad_sch', 'WPT-01-TRANSMITTER-TX.kicad_sch'
root, mcu, tx = (open(f, encoding='utf-8').read() for f in (ROOT, MCU, TX))
done = []


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


def find_block(s, head, at):
    """the top-level block that starts with `head` and holds `(at x y`"""
    for m in re.finditer(r'\n\t\(' + re.escape(head), s):
        b = block_at(s, m.start() + 2)
        if re.search(r'\(at %s %s[ )]' % (re.escape(at[0]), re.escape(at[1])), b[:300]):
            return m.start() + 2, b
    return None, None


def cut(s, j, b):
    """remove the block and the newline + tab in front of it"""
    assert s[j - 2:j] == '\n\t'
    return s[:j - 2] + s[j + len(b):]


def symbol(s, ref):
    i = s.index('(property "Reference" "%s"' % ref)
    j = s.rfind('\n\t(symbol\n', 0, i) + 2
    return j, block_at(s, j)


LABEL = '''(label "%s"
		(at %s %s 180)
		(effects
			(font
				(size 1.27 1.27)
			)
			(justify right bottom)
		)
		(uuid "%s")
	)'''

# ---- TX sheet: the lower legs leave the taps and join the comparator nets
for x, name in (('368.3', 'VSWA_CMP'), ('388.62', 'VSWB_CMP')):
    old = '(xy %s 227.33) (xy %s 229.87)' % (x, x)
    if old in tx:
        tx = tx.replace(old, '(xy %s 227.33) (xy %s 228.6)' % (x, x), 1)
        k = tx.rindex('\n\t(embedded_fonts') if '\n\t(embedded_fonts' in tx else tx.rindex('\n)')
        tx = tx[:k] + '\n\t' + LABEL % (name, x, '229.87', uuid.uuid4()) + tx[k:]
        done.append('lower leg at x = %s -> %s' % (x, name))

# ---- TX sheet: the comparator nets no longer leave the sheet
for name in ('VSWA_CMP', 'VSWB_CMP'):
    while True:
        m = re.search(r'\n\t\(hierarchical_label "%s"' % name, tx)
        if not m:
            break
        b = block_at(tx, m.start() + 2)
        nb = re.sub(r'\n\t\t\(shape \w+\)', '', b.replace('(hierarchical_label "%s"' % name, '(label "%s"' % name, 1), count=1)
        tx = tx[:m.start() + 2] + nb + tx[m.start() + 2 + len(b):]
        done.append('%s: hierarchical label -> label' % name)

# ---- TX sheet: 47 pF
for ref in ('C340', 'C341'):
    j, b = symbol(tx, ref)
    if '"Value" "36p"' not in b:
        continue
    nb = b.replace('"Value" "36p"', '"Value" "47p"').replace('GCM1555C1H360GA16D', 'GCM1555C1H470GA16D').replace('36 pF', '47 pF')
    tx = tx[:j] + nb + tx[j + len(b):]
    done.append('%s 36 pF -> 47 pF' % ref)

# ---- root sheet: the sheet pins of both sheets, their wires and labels
for at in (('303.53', '186.69'), ('303.53', '189.23'), ('134.62', '198.12'), ('134.62', '200.66')):
    m = re.search(r'\n\t\t\(pin "VSW[AB]_CMP" \w+\n\t\t\t\(at %s %s ' % (re.escape(at[0]), re.escape(at[1])), root)
    if not m:
        continue
    b = block_at(root, m.start() + 3)
    root = root[:m.start()] + root[m.start() + 3 + len(b):]
    done.append('sheet pin at %s %s removed' % at)
for a, e in ((('134.62', '198.12'), ('139.7', '198.12')), (('303.53', '186.69'), ('298.45', '186.69')), (('303.53', '189.23'), ('298.45', '189.23')),
             (('134.62', '200.66'), ('139.7', '200.66'))):
    m = re.search(r'\n\t\(wire\n\t\t\(pts\n\t\t\t\(xy %s %s\) \(xy %s %s\)' % tuple(map(re.escape, a + e)), root)
    if m:
        b = block_at(root, m.start() + 2)
        root = cut(root, m.start() + 2, b)
        j, b = find_block(root, 'label "VSW', e)
        assert j is not None, e
        root = cut(root, j, b)
        done.append('wire and label at %s %s removed' % e)

# ---- MCU sheet: PA1 / PC1 end in a no-connect flag
for old, at in (('VSWA_CMP', ('172.72', '73.66')), ('VSWB_CMP', ('121.92', '96.52'))):
    j, b = find_block(mcu, 'hierarchical_label "%s"' % old, at)
    if j is None:
        continue
    u = re.search(r'\(uuid "([^"]+)"\)', b).group(1)
    mcu = mcu[:j] + '(no_connect\n\t\t(at %s %s)\n\t\t(uuid "%s")\n\t)' % (at[0], at[1], u) + mcu[j + len(b):]
    done.append('MCU sheet: %s -> no connect' % old)

# ---- J2: two rows of six (root sheet)
j, b = symbol(root, 'J2')
if 'PinHeader_1x12_P2.54mm_Vertical' in b:
    nb = (b.replace('"Value" "Conn_01x12_Pin"', '"Value" "Conn_02x06_Odd_Even"')
           .replace('Connector_PinHeader_2.54mm:PinHeader_1x12_P2.54mm_Vertical', 'Connector_PinHeader_2.54mm:PinHeader_2x06_P2.54mm_Vertical')
           .replace('"Generic connector, single row, 01x12, script generated"',
                    '"Pin header, 2 x 6, 2.54 mm. Pins 1, 3 ... 11 form one row and 2, 4 ... 12 the other; drawn here as one column"')
           .replace('"61301211121"', '"61301221121"'))
    assert nb.count('61301221121') == 1 and 'PinHeader_2x06' in nb
    root = root[:j] + nb + root[j + len(b):]
    k = root.rindex('\n\t(sheet_instances') if '\n\t(sheet_instances' in root else root.rindex('\n)')
    root = root[:k] + ('\n\t(text "J2: 2 x 6 pins. Odd pins: outer row (board edge),\\neven pins: inner row."\n\t\t(exclude_from_sim no)\n\t\t(at 39.37 191.77 0)\n'
                       '\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)' % uuid.uuid4()) + root[k:]
    done.append('J2 -> 2 x 6')

# ---- clock link: U306 CLK1 - R346 (0 ohm, not fitted) - global label HSE_EXT - PF0
GLABEL = """(global_label "HSE_EXT"
		(shape %s)
		(at %s %s %s)
		(effects
			(font
				(size 1.27 1.27)
			)
			(justify %s)
		)
		(uuid "%s")
		(property "Intersheetrefs" "${INTERSHEET_REFS}"
			(at %s %s 0)
			(hide yes)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify %s)
			)
		)
	)"""
WIRE = '(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)'
PROP = r'\(property "%s" "(?:[^"\\]|\\.)*"'


def add(s, text):
    k = s.rindex('\n\t(embedded_fonts') if '\n\t(embedded_fonts' in s else s.rindex('\n)')
    return s[:k] + '\n\t' + text + s[k:]


if '(property "Reference" "R346"' not in tx:
    NOTE = ('R346 (not fitted): link from CLK1 of the Si5351 (U306) to the clock input PF0 of the MCU. To clock the MCU from the Si5351: '
            'fit 0 ohm (RC0402FR-070RL), remove Y1, select HSE bypass in the firmware')
    jn, nc = find_block(tx, 'no_connect', ('120.65', '189.23'))
    assert jn is not None
    tx = cut(tx, jn, nc)
    j, r = symbol(tx, 'R313')
    assert '(at 92.71 191.77 0)' in r and '"Value" "0"' in r
    dx, dy = 128.27 - 92.71, 189.23 - 191.77                          # this symbol lies: pins at x = 127.00 and 129.54
    fmt = lambda v: ('%.4f' % v).rstrip('0').rstrip('.')
    nr = re.sub(r'\(at (-?[\d.]+) (-?[\d.]+) (\d+)\)', lambda q: '(at %s %s %s)' % (fmt(float(q.group(1)) + dx), fmt(float(q.group(2)) + dy), q.group(3)), r)
    nr = re.sub(r'\(uuid "[^"]+"\)', lambda _: '(uuid "%s")' % uuid.uuid4(), nr)
    nr = nr.replace('(property "Reference" "R313"', '(property "Reference" "R346"', 1).replace('(reference "R313")', '(reference "R346")')
    nr = re.sub(r'\n\t+\(variant\n\t+\(name "[^"]+"\)\n\t+\(dnp \w+\)\n\t+\)', '', nr)
    nr = nr.replace('(dnp no)', '(dnp yes)', 1).replace('"Footprint" "yageo:R_0402"', '"Footprint" "Resistor_SMD:R_0402_1005Metric"')
    assert nr.count('"R346"') == 2 and '(dnp yes)' in nr and '(variant' not in nr

    if '(property "Assembly Note"' in nr:
        nr = re.sub(PROP % 'Assembly Note', lambda _: '(property "Assembly Note" "%s"' % NOTE, nr, count=1)
    else:
        mm = re.search(r'\t\t' + PROP % 'Manufacturer Part Number' + r'\n.*?\n\t\t\)\n', nr, re.S)
        new = re.sub(PROP % 'Manufacturer Part Number', lambda _: '(property "Assembly Note" "%s"' % NOTE, mm.group(0), count=1)
        nr = nr[:mm.end()] + new + nr[mm.end():]
    tx = tx[:j + len(r)] + '\n\t' + nr + tx[j + len(r):]
    tx = add(tx, WIRE % ('120.65', '189.23', '127', '189.23', uuid.uuid4()))
    tx = add(tx, GLABEL % ('output', '129.54', '189.23', '0', 'left', uuid.uuid4(), '130.81', '189.23', 'left'))
    done.append('R346 and the global label HSE_EXT at CLK1 of U306')
if '(global_label "HSE_EXT"' not in mcu:
    assert '(xy 129.54 81.28) (xy 81.28 81.28)' in mcu and '(xy 81.28 81.28) (xy 81.28 87.63)' in mcu
    mcu = add(mcu, GLABEL % ('input', '81.28', '81.28', '180', 'right', uuid.uuid4(), '80.01', '81.28', 'right'))
    done.append('MCU sheet: global label HSE_EXT at PF0')

if not done:
    sys.exit('already applied')
for f, s in ((ROOT, root), (MCU, mcu), (TX, tx)):
    assert s.count('(') == s.count(')'), f
    open(f, 'w', encoding='utf-8').write(s)
print('\n'.join(done))

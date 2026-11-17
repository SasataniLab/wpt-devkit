#!/usr/bin/env python3
"""Schematic of the display board (run inside hardware/kicad/WPT-TX-DISPLAY): writes WPT-TX-DISPLAY.kicad_sch.

The board plugs onto J2 of the transmitter board (1 x 12 header, 3.3 V only) and carries a 0.96 inch IPS TFT with
ST7735S controller. Signals of J2 (docs/stm32-tx/display_shield_study.md):

   1 GND   2 +3V3   3 SCK (PA5)   4 MISO (PA6)   5 MOSI (PA7)   6 ADC (PC2)
   7 CS (PA2)   8 DC (PA3)   9 RST (PA4)   10 IO (PB3, TIM2_CH2)   11 +3V3   12 GND

Used here: SCK, MOSI, CS, DC, RST, and IO as the backlight switch (PWM capable). MISO and ADC are not connected:
the ST7735S is written to only, and the board has no keys. The supply comes from pin 11, next to the display; pin 2
is left open (a track from there would have to cross the signals on the narrow strip; 3 mA + 20 mA need one pin).

Backlight: one white LED, 2.9 to 3.1 V at 15 to 20 mA (data sheet of the Wisevision panel; Midas gives 3.2 V at
15 mA, Focus 2.7 / 3.1 / 3.4 V at 20 mA). From 3.3 V that leaves 0.2 to 0.4 V at best, so the switch has to be a MOSFET
with a few tens of milliohms at a gate voltage of 2.5 V and the current is set by R1 and the LED alone: with 22 ohm
about 14 mA at 3.0 V, 18 mA at 2.9 V (the limit is 20 mA, so R1 must not be smaller), and less than half of that
with an LED of 3.2 V. The brightness therefore depends on the panel; that is the price of a 3.3 V supply (J2 of the
transmitter board has no 5 V). R2 keeps the backlight off until firmware drives the pin (PB3 floats after reset).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schgen  # noqa: E402

PRJ = 'WPT-TX-DISPLAY'
sh = schgen.Sheet(PRJ, 'WPT transmitter: display board (provisional)', '2026-11-17', '0.1', local_dir='lib/symbols',
                  comment='Plugs onto J2 of WPT-01-TRANSMITTER. 3.3 V only.')
YAGEO, MURATA, SAMSUNG = 'Yageo', 'Murata Electronics', 'Samsung Electro-Mechanics'


def part(mfr, mpn, footprint, note=None, **kw):
    f = {'Footprint': footprint, 'Manufacturer': mfr, 'Manufacturer Part Number': mpn}
    if note:
        f['Assembly Note'] = note
    f.update(kw)
    return f


def gnd(p):
    """ground symbol below the point"""
    sh.wire(p, (p[0], p[1] + 2.54))
    sh.power('power:GND', (p[0], p[1] + 2.54))


# ------------------------------------------------------------------ J1: the socket that goes onto J2
J = sh.place('Connector:Conn_01x12_Socket', 'J1', 'to J2 of the transmitter', 60.96, 86.36, mirror=True,
             fields=part('Wurth Elektronik', '61301211821', 'Connector_PinSocket_2.54mm:PinSocket_1x12_P2.54mm_Vertical',
                         note='J1: on the back of the board (the side that faces the transmitter board), soldered from the display side '
                              'before the display is fitted. Body height 8.5 mm: do not substitute another height',
                         Datasheet='https://www.we-online.com/components/products/datasheet/61301211821.pdf',
                         Description='Socket header, 2.54 mm, 1 x 12, through hole, vertical, 8.5 mm high'),
             ref_at=(58.42, 68.58), val_at=(58.42, 106.68))
NETS = {3: 'SCK', 5: 'MOSI', 7: '~{CS}', 8: 'DC', 9: '~{RST}', 10: 'BL_PWM'}
for n in range(1, 13):
    p = J[str(n)]
    if n in NETS:
        sh.wire(p, (p[0] + 15.24, p[1]))
        sh.label(NETS[n], (p[0] + 15.24, p[1]))
    elif n in (2, 4, 6):
        sh.nc(p)
    else:                                              # supply pins: the symbols lie on their side, pointing away from the connector
        sh.wire(p, (p[0] + 5.08, p[1]))
        sh.power('power:GND' if n in (1, 12) else 'power:+3V3', (p[0] + 5.08, p[1]), side='right')
sh.text('Not used: 2 (+3V3, the board is fed from 11),\n4 (MISO) and 6 (ADC)', (45.72, 113.03))
sh.text('J2 of the transmitter board:\n1 GND  2 +3V3  3 SCK  4 MISO  5 MOSI  6 ADC\n7 CS  8 DC  9 RST  10 IO (PB3)  11 +3V3  12 GND', (45.72, 63.5))

# ------------------------------------------------------------------ DS1: the display
X, Y = 165.1, 88.9
D = sh.place('WPT_Display:TFT_0.96in_80x160_ST7735S_FPC13', 'DS1', 'N096-1608TBBIG11-H13', X, Y,
             fields=part('Wisevision', 'N096-1608TBBIG11-H13', 'WPT_Display:TFT_0.96in_80x160_FPC13_P0.7mm_Folded',
                         note='DS1: not fitted by the assembler. By hand, after everything else: solder the 13 contacts of the flex tail to the '
                              'lands with the module lying face down beside the board (the two holes of the tail over the two circles of the '
                              'silkscreen, contact 1 at the "1"), cover the joints with polyimide tape, then fold the module over onto '
                              'double-sided tape. Same tail and pins: Midas MDT0096A2IS-SPI, Focus LCDs E096GA-SW500-N'),
             ref_at=(154.94, 74.93), val_at=(176.53, 104.14), in_pos=False)
for num, name in (('3', 'MOSI'), ('4', 'SCK'), ('5', 'DC'), ('6', '~{RST}'), ('7', '~{CS}')):
    p = D[num]
    sh.wire(p, (p[0] - 5.08, p[1]))
    sh.label(name, (p[0] - 5.08, p[1]), 180)

# supply and decoupling: a rail at y = 66.04
RAIL = 66.04
vdd = D['10']
sh.wire(vdd, (vdd[0], RAIL))
sh.power('power:+3V3', (vdd[0], RAIL))
C1 = sh.place('Device:C', 'C1', '100n', 137.16, RAIL + 3.81, fields=part(MURATA, 'GCM155R71H104KE02D', 'Capacitor_SMD:C_0402_1005Metric'),
              ref_at=(139.7, RAIL + 2.54), val_at=(139.7, RAIL + 5.08))
C2 = sh.place('Device:C', 'C2', '1u', 127.0, RAIL + 3.81, fields=part(SAMSUNG, 'CL05A105KA5NQNC', 'Capacitor_SMD:C_0402_1005Metric'),
              ref_at=(129.54, RAIL + 2.54), val_at=(129.54, RAIL + 5.08))
sh.wire(C2['1'], C1['1'])
sh.wire(C1['1'], (vdd[0], RAIL))
sh.junction(C1['1'])
sh.junction((vdd[0], RAIL))
gnd(C1['2'])
gnd(C2['2'])
sh.power('power:PWR_FLAG', C2['1'])

# ground of the display
g1, g2 = D['8'], D['13']
sh.wire(g1, (g1[0], g1[1] + 2.54))
sh.wire(g2, (g2[0], g2[1] + 2.54))
sh.wire((g1[0], g1[1] + 2.54), (g2[0], g2[1] + 2.54))
sh.power('power:GND', (g1[0], g1[1] + 2.54))

# backlight: +3V3 - R1 - LED (in the module) - Q1 - GND
la, lk = D['12'], D['11']
R1 = sh.place('Device:R', 'R1', '22R', la[0], 62.23, fields=part(YAGEO, 'RC0402FR-0722RL', 'Resistor_SMD:R_0402_1005Metric'),
              ref_at=(la[0] + 2.54, 60.96), val_at=(la[0] + 2.54, 63.5))
sh.wire(R1['2'], la)
sh.power('power:+3V3', R1['1'])
Q1 = sh.place('Transistor_FET:Q_NMOS_GSD', 'Q1', 'AO3400A', lk[0] - 2.54, 116.84,
              fields=part('Alpha & Omega Semiconductor', 'AO3400A', 'Package_TO_SOT_SMD:SOT-23',
                          note='Q1: any N-channel MOSFET in SOT-23 (gate 1, source 2, drain 3) with a gate threshold below 1.5 V and at most '
                               '0.2 ohm at a gate voltage of 2.5 V may be substituted',
                          Datasheet='https://www.aosmd.com/res/datasheets/AO3400A.pdf',
                          Description='N-channel MOSFET, 30 V, logic level (less than 48 mohm at a gate voltage of 2.5 V, threshold 0.65 to 1.45 V), SOT-23'),
              ref_at=(lk[0] + 2.54, 115.57), val_at=(lk[0] + 2.54, 118.11))
assert Q1['3'] == (lk[0], 111.76), Q1
sh.wire(lk, Q1['3'])
gnd(Q1['2'])
gate = Q1['1']
R2 = sh.place('Device:R', 'R2', '100k', 154.94, gate[1] + 3.81, fields=part(YAGEO, 'RC0402FR-07100KL', 'Resistor_SMD:R_0402_1005Metric'),
              ref_at=(148.59, gate[1] + 2.54), val_at=(148.59, gate[1] + 5.08))
assert R2['1'] == (154.94, gate[1]), R2
sh.wire(gate, R2['1'])
sh.wire(R2['1'], (147.32, gate[1]))
sh.label('BL_PWM', (147.32, gate[1]), 180)
sh.junction(R2['1'])
gnd(R2['2'])
sh.text('Backlight off until BL_PWM is driven high.\nOne LED, 3.0 V typ.: R1 sets about 14 mA.', (176.53, 123.19))

# ------------------------------------------------------------------ H1: the screw hole on the spacer
# Its pad is not joined to the ground of this board. The hole below it on the transmitter board is ground, so a metal
# spacer would close a loop of about 6 cm2 between the two boards (J1 at one end, the spacer at the other), and this
# board works next to a 6.78 MHz coil. Ground is joined where the signals are, at J1, and nowhere else.
H = sh.place('Mechanical:MountingHole_Pad', 'H1', 'M3 on an 11 mm spacer', 220.98, 86.36,
             fields={'Footprint': 'MountingHole:MountingHole_3.2mm_M3_Pad',
                     'Description': 'Screw hole for M3, on the 11 mm spacer that stands on the north-east mounting hole of the transmitter board'},
             ref_at=(224.79, 81.28), val_at=(224.79, 83.82), in_bom=False)
sh.nc(H['1'])
sh.text('Pad not joined to ground on purpose:\nground is joined at J1 only (no loop\nbetween the boards next to the coil).', (205.74, 96.52))
sh.text('Not on this board, needed to fit it:\nspacer M3 x 11 mm, internal thread at both\nends (Harwin R30-1001102), two M3 screws', (205.74, 109.22))
# the ground net is fed through J1: tell ERC so
sh.power('power:GND', (243.84, 128.27))
sh.wire((243.84, 128.27), (243.84, 123.19))
sh.power('power:PWR_FLAG', (243.84, 123.19))

sh.write(PRJ + '.kicad_sch')
print('written', PRJ + '.kicad_sch', 'with', len(sh.refs), 'symbols')

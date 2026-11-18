#!/usr/bin/env python3
"""Hand-designed fan-out of the STM32 (U2): every pin gets its escape before anything is auto-routed.

usage: fan.py BOARD_IN BOARD_OUT

Plan (U2 at 183.9/153.9, rotated 270 deg; pin 16..1 on the north row, 17..32 west, 33..48 south, 64..49 east):
  * supply pins: one via per pin right beside its decoupling capacitor on the back
  * crystal: both tracks on the top side, nothing else crosses them
  * north row: CS and ADC2_IN8 leave northwards on the top side; ADC_VDC, the two comparator inputs, NRST and
    the encoder push line go to vias inside the pad ring
  * the back side north of the MCU is kept as an east -> west highway (NRST, encoder push, later the east column)
  * west row: display signals leave westwards on top; UART / HV enable go through vias and leave on the back
  * south row: the four HRTIM outputs drop to vias inside the ring and leave on the back towards the gate
    drivers; encoder / I2C / FLT4 leave on top, turning west below the pad row
  * east row: alternating vias outside / inside the ring; USB was routed by hand earlier
"""
import sys

import pcbnew

import router as R

src, dst = sys.argv[1:3]
MM = 1e6
b = pcbnew.LoadBoard(src)


def move(ref, x, y, rot=None):
    fp = b.FindFootprintByReference(ref)
    fp.SetPosition(pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM))))
    if rot is not None:
        fp.SetOrientationDegrees(rot)
    print(ref, [(p.GetNumber(), p.GetNetname().split('/')[-1], round(p.GetPosition().x / MM, 3), round(p.GetPosition().y / MM, 3)) for p in fp.Pads()])


# --- part moves that make room for the escapes
move('C2', 178.3, 157.4)                 # under the west pad row instead of inside the ring
move('C12', 183.48, 144.3, 90)          # crystal load capacitor: upright, left of the crystal
c10 = b.FindFootprintByReference('C10')
move('C10', 184.6, 150.4, c10.GetOrientationDegrees() + 180)   # NRST pad towards the pin
r2 = b.FindFootprintByReference('R2')
move('R2', 187.3, 153.25, r2.GetOrientationDegrees() + 180)    # BOOT0 pull-down: out of the east lanes
r1 = b.FindFootprintByReference('R1')
move('R1', 184.4, 155.4, r1.GetOrientationDegrees() + 180)     # VDDA pad next to C9, supply pad towards C5
pcbnew.SaveBoard(dst, b)

r = R.Router(dst, corridors=())
r._fixed = True
F = lambda net, pts, w=0.2: [r.add_track(net, 'F.Cu', p, q, w) for p, q in zip(pts, pts[1:])]
B = lambda net, pts, w=0.2: [r.add_track(net, 'B.Cu', p, q, w) for p, q in zip(pts, pts[1:])]
V = lambda net, c: r.add_via(net, c)
names = {n.split('/')[-1]: n for n in r.nets}


def N(short):
    full = [n for n in r.board.GetNetsByName().asdict().keys() if str(n).split('/')[-1] == short]
    assert len(full) == 1, (short, full)
    return str(full[0])


P3, GND, VDDA = '+3V3', 'GND', N('Net-(U2-VDDA)')
W = 0.25    # supply stubs

# ------------------------------------------------------------------ supplies
# pin 16 VDD / 15 VSS with C1
F(P3, [(180.15, 148.975), (180.15, 149.5), (180.0, 149.75), (180.0, 150.95)], W); V(P3, (180.0, 150.95)); B(P3, [(180.0, 150.95), (179.92, 150.1)], W)
F(GND, [(180.65, 148.975), (180.65, 149.5), (180.88, 149.75), (180.88, 150.5), (181.0, 150.95)], W); V(GND, (181.0, 150.95)); B(GND, [(181.0, 150.95), (180.88, 150.1)], W)
# pin 1 VBAT, 64 VDD, 63 VSS with C4
V(P3, (187.8, 149.42)); F(P3, [(187.65, 148.975), (187.8, 149.42)], W); F(P3, [(188.825, 150.15), (188.35, 150.15), (187.95, 149.75), (187.8, 149.42)], W)
B(P3, [(187.8, 149.42), (187.8, 150.12)], W)
V(GND, (186.95, 151.08)); F(GND, [(188.825, 150.65), (188.3, 150.65), (187.87, 151.08), (186.95, 151.08)], W); B(GND, [(186.95, 151.08), (187.8, 151.08)], W)
# pin 32 VDD / 31 VSS with C2 (moved)
V(P3, (179.4, 158.4)); F(P3, [(178.975, 157.65), (179.05, 157.72), (179.4, 158.07), (179.4, 158.4)]); B(P3, [(179.4, 158.4), (178.9, 157.88), (178.3, 157.88)], W)
V(GND, (179.55, 157.05)); F(GND, [(178.975, 157.15), (179.55, 157.05)], W); B(GND, [(179.55, 157.05), (179.2, 156.92), (178.3, 156.92)], W)
# pin 48 VDD / 47 VSS with C3
V(P3, (187.75, 158.42)); F(P3, [(187.65, 158.825), (187.75, 158.42)], W); B(P3, [(187.75, 158.42), (187.88, 157.7)], W)
V(GND, (186.2, 157.7)); F(GND, [(187.15, 158.825), (187.15, 158.6), (186.75, 158.2), (186.3, 157.75), (186.2, 157.7)]); B(GND, [(186.2, 157.7), (186.92, 157.7)], W)
# VSSA pin 27 -> ground via between C6 and C7; VREF+/VDDA pins 28, 29 -> via beside C6
V(GND, (180.55, 154.2)); F(GND, [(178.975, 155.15), (179.9, 155.15), (180.55, 154.5), (180.55, 154.2)], W)
B(GND, [(180.55, 154.2), (180.0, 154.75), (180.0, 154.92)], W); B(GND, [(180.55, 154.2), (181.1, 154.75), (181.1, 154.92)], W)
V(VDDA, (179.29, 155.9)); F(VDDA, [(178.975, 155.65), (179.29, 155.9)], W); F(VDDA, [(178.975, 156.15), (179.29, 155.9)], W); B(VDDA, [(179.29, 155.9), (180.0, 155.88)], W)
B(VDDA, [(180.0, 155.88), (183.3, 155.88), (184.4, 155.91)], W)                           # C6-C7-C8-C9 filter capacitors and R1
# C5 (bulk) and the BOOT0 pull-down share the ground via
V(P3, (184.52, 153.45)); B(P3, [(184.52, 153.45), (184.52, 152.6)], W); B(P3, [(184.52, 153.45), (184.4, 154.89)], W)   # C5 and R1 supply side
V(GND, (186.15, 153.05)); B(GND, [(186.15, 153.05), (185.48, 152.6)], W); B(GND, [(186.15, 153.05), (186.79, 153.25)], W)
# NRST capacitor ground
V(GND, (185.35, 150.88)); B(GND, [(185.35, 150.88), (184.6, 150.88)], W)

# ------------------------------------------------------------------ crystal (top side only)
PF0, PF1 = N('Net-(U2-PF0)'), N('Net-(U2-PF1)')
F(PF0, [(185.65, 147.475), (185.65, 146.2)]); F(PF0, [(185.97, 145.93), (187.32, 145.9)])
F(PF1, [(185.15, 147.475), (185.15, 147.25), (184.8, 146.9), (183.75, 146.9), (183.35, 146.5), (183.35, 144.85)]); F(PF1, [(183.48, 144.78), (184.82, 144.55)])
V(GND, (184.0, 145.8)); F(GND, [(184.0, 145.8), (184.7, 145.93)], W)                       # crystal case pad 4
F(GND, [(185.97, 144.47), (186.1, 143.5), (186.24, 142.2)], W)                             # crystal case pad 2 -> J2 pin 12 (GND)
V(GND, (184.2, 143.3)); F(GND, [(183.48, 143.82), (183.9, 143.4), (184.2, 143.3)], W)                     # load capacitor C12

# crystal load capacitor C11 and the CC2 pull-down share one ground via
F(GND, [(188.28, 145.9), (188.9, 145.7), (189.2, 145.7)], W); V(GND, (189.2, 145.7)); F(GND, [(189.2, 145.7), (189.09, 144.6)], W)

# ------------------------------------------------------------------ north row
n = N
F(n('GPIO_DISP_CS'), [(181.15, 147.475), (181.15, 146.8)])
F(n('ADC2_IN8_EXTERNAL'), [(183.15, 147.475), (183.15, 147.3), (182.85, 147.0), (182.85, 146.3)])
# ADC_VDC: via inside, leaves westwards on the back
F(n('ADC_VDC'), [(182.15, 148.975), (182.15, 149.05), (182.5, 149.4), (182.5, 150.95)]); V(n('ADC_VDC'), (182.5, 150.95))
B(n('ADC_VDC'), [(182.5, 150.95), (182.5, 151.3), (182.15, 151.65), (176.4, 151.65)])
# comparator inputs: straight across the inside of the ring on top, vias next to the south row
F(n('VSWA_CMP'), [(181.65, 148.975), (181.65, 149.2), (181.85, 149.4), (181.85, 156.7), (182.2, 157.05), (182.2, 157.1)]); V(n('VSWA_CMP'), (182.2, 157.1))
B(n('VSWA_CMP'), [(182.2, 157.1), (183.0, 157.1), (183.4, 157.5), (183.4, 160.7)])
F(n('VSWB_CMP'), [(183.65, 148.975), (183.65, 149.1), (183.9, 149.35), (183.9, 156.9), (184.3, 157.3)]); V(n('VSWB_CMP'), (184.3, 157.3))
B(n('VSWB_CMP'), [(184.3, 157.3), (184.3, 160.7)])
# NRST: capacitor on the back, then the innermost highway lane, back to the top between DC and RST
F(n('NRST'), [(184.65, 148.975), (184.65, 149.2), (185.1, 149.65), (185.35, 149.92)]); V(n('NRST'), (185.35, 149.92))
B(n('NRST'), [(185.35, 149.92), (184.6, 149.92)]); B(n('NRST'), [(185.35, 149.92), (185.35, 149.2), (184.9, 148.75), (178.2, 148.75)])
V(n('NRST'), (178.2, 148.75)); F(n('NRST'), [(178.2, 148.75), (178.2, 147.2)])
# encoder push: second highway lane straight into the switch pad
F(n('GPIO_ENCODER_PUSH'), [(187.15, 148.975), (187.15, 149.1), (186.9, 149.35), (186.9, 149.55)]); V(n('GPIO_ENCODER_PUSH'), (186.9, 149.55))
B(n('GPIO_ENCODER_PUSH'), [(186.9, 149.55), (186.9, 148.7), (186.5, 148.3), (179.3, 148.3), (179.1, 148.1), (174.9, 148.1)])

# ------------------------------------------------------------------ west row
F(n('GPIO_DISP_DC'), [(177.475, 150.15), (177.0, 150.15), (177.0, 147.2)])
F(n('GPIO_DISP_RST'), [(178.975, 150.65), (179.4, 150.65), (179.4, 147.2)])
F(n('SPI1_CLK_DISP'), [(177.475, 151.15), (177.3, 151.15), (176.8, 150.65), (176.0, 150.65)])
F(n('SPI1_MISO_DISP'), [(177.475, 151.65), (177.2, 151.65), (176.7, 151.15), (176.0, 151.15)])
F(n('SPI1_MOSI_DISP'), [(177.475, 152.15), (177.1, 152.15), (176.6, 151.65), (176.0, 151.65)])
F(n('USART1_TX_EXTERNAL'), [(178.975, 152.65), (179.3, 152.65), (179.55, 152.4), (179.75, 152.4)]); V(n('USART1_TX_EXTERNAL'), (179.75, 152.4))
B(n('USART1_TX_EXTERNAL'), [(179.75, 152.4), (178.5, 152.4), (176.4, 154.5), (175.9, 154.5)])
F(n('USART1_RX_EXTERNAL'), [(178.975, 153.15), (180.75, 153.15)]); V(n('USART1_RX_EXTERNAL'), (180.75, 153.15))
B(n('USART1_RX_EXTERNAL'), [(180.75, 153.15), (178.4, 153.15), (176.55, 155.0), (175.9, 155.0)])
F(n('HV_EN_MCU'), [(178.975, 153.65), (179.3, 153.65), (179.55, 153.9), (179.75, 153.9)]); V(n('HV_EN_MCU'), (179.75, 153.9))
B(n('HV_EN_MCU'), [(179.75, 153.9), (178.3, 153.9), (176.7, 155.5), (175.9, 155.5)])
F(n('~{WLAT}'), [(177.475, 154.15), (177.2, 154.15), (176.7, 154.65), (176.0, 154.65)])
F(n('~{ALERT}'), [(177.475, 154.65), (177.3, 154.65), (176.8, 155.15), (176.0, 155.15)])
F(n('HRTIM1_FLT3'), [(177.475, 156.65), (176.5, 156.65)])

# ------------------------------------------------------------------ south row
for net, tip, via in (('HRTIM1_CHC1', [(180.65, 158.825), (180.65, 158.65), (180.35, 158.35)], (180.35, 158.25)),
                      ('HRTIM1_CHC2', [(181.15, 158.825), (181.15, 158.5), (181.05, 158.4)], (181.05, 157.3)),
                      ('HRTIM1_CHD1', [(181.65, 158.825), (181.75, 158.6)], (181.75, 158.25)),
                      ('HRTIM1_CHD2', [(182.15, 158.825), (182.15, 158.75), (182.55, 158.35)], (182.65, 158.25))):
    F(n(net), tip + [via]); V(n(net), via); B(n(net), [via, (via[0], 160.7)])
F(n('HRTIM1_FLT4'), [(180.15, 160.325), (180.15, 160.75), (179.5, 160.75)])
F(n('TIM3_CH1_ENCODER'), [(182.65, 160.325), (182.65, 161.25), (179.5, 161.25)])
F(n('TIM3_CH2_ENCODER'), [(183.15, 160.325), (183.15, 161.75), (179.5, 161.75)])
F(n('SCL'), [(183.65, 160.325), (183.65, 162.25), (179.5, 162.25)])
F(n('SDA'), [(184.15, 160.325), (184.15, 162.75), (179.5, 162.75)])

# ------------------------------------------------------------------ east row
J1 = n('Net-(J1-Pin_1)')
F(J1, [(188.825, 151.65), (188.5, 151.65), (188.1, 152.05), (187.9, 152.05)]); V(J1, (187.9, 152.05)); B(J1, [(187.9, 152.05), (187.81, 153.25)])
F(n('GPIO_SW_MISC1'), [(188.825, 154.15), (188.2, 154.15)]); V(n('GPIO_SW_MISC1'), (188.2, 154.15))
F(n('HRTIM1_EEV2'), [(188.825, 155.65), (188.2, 155.65)]); V(n('HRTIM1_EEV2'), (188.2, 155.65))
for net, y in (('HV_SW_STATE', 153.65), ('HRTIM1_EEV1', 155.15), ('GPIO_VUSB_SENSE', 156.15), ('SWCLK', 157.15)):
    F(n(net), [(190.325, y), (191.1, y)]); V(n(net), (191.1, y))
F(n('SWDIO'), [(190.325, 157.65), (190.55, 157.65), (191.1, 158.2)]); V(n('SWDIO'), (191.1, 158.2))
# back-side lanes under the east pad row, all heading north to the highway (the southern pin takes the lane further east)
B(J1, [(187.9, 152.05), (188.45, 151.5), (188.45, 149.0)])
B(n('GPIO_SW_MISC1'), [(188.2, 154.15), (188.9, 153.45), (188.9, 149.0)])
B(n('HRTIM1_EEV2'), [(188.2, 155.65), (189.35, 154.5), (189.35, 149.0)])
B(n('SWDIO'), [(191.1, 158.2), (190.4, 158.2), (189.8, 157.6), (189.8, 149.0)])
B(n('SWCLK'), [(191.1, 157.15), (190.5, 157.15), (190.25, 156.9), (190.25, 149.0)])
# two lanes east of the via column (under the USB pair, which is on the top side)
B(n('HV_SW_STATE'), [(191.1, 153.65), (191.4, 153.35), (191.4, 147.6)])
B(n('HRTIM1_EEV1'), [(191.1, 155.15), (192.45, 155.15), (192.95, 154.65), (192.95, 147.6)])
B(n('GPIO_VUSB_SENSE'), [(191.1, 156.15), (193.5, 156.15)])
r.save()
print('fan-out written to', dst)

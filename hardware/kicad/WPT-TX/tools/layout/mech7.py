#!/usr/bin/env python3
"""Fourth revision, part 1: the virtual COM port of the debug connector. usage: mech7.py BOARD_IN BOARD_OUT NETLIST

USART1 (PC4 transmit, PC5 receive) ran through the slide switch SW2 to the header J4 and nowhere else. J3 (STDC14)
sits north of the switch, so its pins 13 / 14 need two more crossings of the switch's pin rows. On the two outer
layers the passages between the pins are taken (latch line and enable on the row of pins 2 / 5, switch state on the
row of pins 1 / 4). Two passages were not used so far:

  transmit (PC4 -> J3 pin 14)   inner layer In2, straight north between the two pin columns (x = 154.5). A via is
                                added on the existing front-side track inside the switch outline (154.50, 156.75), away
                                from the cover walls; from there 11 mm on In2 to the pad of pin 14 (a through-hole pad
                                has copper on every layer). The +3V3 plane gets a slot 0.6 mm wide along it.
  receive (J3 pin 13 -> PC5)    back side, west of the pin columns (x = 152.0), then between the north-west lug of the
                                cover and pin 4 (0.3 mm to each), to R12 (560 ohm, back side, between J3 and the switch).

Nothing that existed moves except
  * the front-side piece of the transmit line inside the switch: it now passes through the new via and continues to J4
    on x = 154.5 (was 154.55), all on 45 degrees (the old piece had a 53 degree segment);
  * one ground stitching via inside the switch outline, (154.95, 156.50), which sat where the new via and the inner-layer
    track have to be. It is removed; the pours around pin 6 (GND) of the switch keep the stitching via south of that pin,
    (153.70, 160.10).
J4 keeps its copper and is no longer fitted.
"""
import shutil
import sys

import pcbnew

import newfp
from newfp import seg, via, rip, rip_via, place, pads, net, flush

src, dst, netlist = sys.argv[1:4]
shutil.copy(src, dst)
b = pcbnew.LoadBoard(dst)
comps = newfp.load_netlist(netlist)
TX = newfp.full_name(b, 'USART1_TX_EXTERNAL')
RX = newfp.full_name(b, 'USART1_RX_EXTERNAL')
VCP = comps['R12']['pins']['1']
assert comps['J3']['pins']['13'] == VCP and comps['J3']['pins']['14'] == TX and comps['R12']['pins']['2'] == RX

# J3: pads 13 / 14 get their nets
j3 = b.FindFootprintByReference('J3')
for p in j3.Pads():
    if p.GetNumber() in ('13', '14'):
        p.SetNet(net(b, comps['J3']['pins'][p.GetNumber()]))
p13, p14 = pads(j3)['13'], pads(j3)['14']
assert p13 == (152.4, 144.11) and p14 == (153.67, 144.11), (p13, p14)

# the ground stitching via in the way goes
rip_via(b, 'GND', (154.95, 156.50))

# transmit: the front-side piece inside the switch is laid again through the new via
rip(b, TX, 'F.Cu', [(156.25, 155.95), (154.75, 157.95), (154.55, 158.15), (154.55, 164.20), (152.40, 166.35)], expect=4)
seg(b, TX, [(156.25, 155.95), (155.45, 156.75), (154.50, 156.75), (154.50, 164.25), (152.40, 166.35)], layer='F.Cu')
via(b, TX, (154.50, 156.75))
seg(b, TX, [(154.50, 156.75), (154.50, 145.77), (153.67, 144.94), p14], layer='In2.Cu')

# receive: a branch on the back side from the existing back-side track (it turns south-west at (155.25, 157.45))
r12 = place(b, comps, 'R12', 153.10, 146.40, rot=90.0, side='B', ref_at=(1.55, 0.0), ref_rot=90.0)
pp = pads(r12)
if pp['1'][1] > pp['2'][1]:                      # pad 1 (to J3) has to be the northern one
    r12.SetOrientationDegrees(270.0)
    pp = pads(r12)
assert pp['1'] == (153.1, 145.89) and pp['2'] == (153.1, 146.91), pp
seg(b, RX, [(155.25, 157.45), (154.09, 157.45), (152.00, 155.36), (152.00, 150.18), (153.10, 149.08), pp['2']], layer='B.Cu')
seg(b, VCP, [pp['1'], (153.10, 145.60), (152.40, 144.90), p13], layer='B.Cu')

print('track pieces removed:', flush(b))
pcbnew.SaveBoard(dst, b)
print('saved', dst)

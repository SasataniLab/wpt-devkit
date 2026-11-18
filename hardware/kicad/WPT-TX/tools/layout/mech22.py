#!/usr/bin/env python3
"""DRC clean-up of 2026-11-18 (the user ran the DRC in the GUI and saw the list). usage: mech22.py BOARD_IN BOARD_OUT

  zones_intersect (11)  zones of ONE net that overlap with equal priority (VPP, GND, DC_IN, +7V, the node of C207).
                        Every zone gets its own priority: old priority x 100 + a running number, so the order between
                        zones of different priority stays as it was. The copper does not change.
  starved_thermal (3)   U207 pad 17 (a via of the exposed pad, back side) and U201 pads 4 and 15 (front side) had one
                        spoke where two are asked for. These three pads now join their GND zone solid.
  C314                  its reference lay on the land of L301 (clipped by the mask opening, under the inductor):
                        now beside the capacitor.
"""
import sys
import pcbnew
from newfp import P, V

src, dst, cx, cy = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
MODE = sys.argv[5] if len(sys.argv) > 5 else 'fwd'
b = pcbnew.LoadBoard(src)
zones = list(b.Zones())
if MODE == 'rev':
    zones.reverse()
if MODE == 'mix':                       # file order for GND, reverse file order for the rest: the fill then matches the one before
    zones = [z for z in zones if z.GetNetname() == 'GND'] + [z for z in reversed(zones) if z.GetNetname() != 'GND']
for k, z in enumerate(zones):
    if not z.GetIsRuleArea():
        z.SetAssignedPriority(z.GetAssignedPriority() * 100 + k)
for ref, num in (('U207', '17'), ('U201', '4'), ('U201', '15')):
    for p in b.FindFootprintByReference(ref).Pads():
        if p.GetNumber() == num:
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
r = b.FindFootprintByReference('C314').Reference()
assert P(r.GetPosition()) == (210.15, 179.25), P(r.GetPosition())
r.SetPosition(V(cx, cy))
pcbnew.SaveBoard(dst, b)
print('zones renumbered:', len(zones))

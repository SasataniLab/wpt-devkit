#!/usr/bin/env python3
"""Stage 1: place the MCU/UI section on the board.

usage: stage1_place.py IN.kicad_pcb OUT.kicad_pcb
"""
import sys

import pcbnew

MM = 1e6


def V(x, y):
    return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))


def xy(p):
    return p.x / MM, p.y / MM


def inbox(p, box):
    x, y = xy(p)
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


# ---------------------------------------------------------------- placement table
# ref: (x, y, rot_deg, side)
PLACE = {
    # --- connectors / UI (front)
    'J3': (152.3, 137.2, 90, 'F'),      # SWD header, top edge, west end (pin 1 = NRST at the left)
    'J301': (183.88, 137.2, 270, 'F'),  # ZVS/fault experiment header, top edge, pin 1 (VSWA_SENSE) at the east end
    'J2': (158.3, 141.5, 90, 'F'),      # display/IO header, second row
    'J5': (193.8, 138.675, 180, 'F'),   # USB-C, opening at the top edge
    'SW2': (155.75, 150.7, 270, 'F'),   # HV interlock slide switch, actuator over the left edge
    'SW1': (160.4, 148.1, 0, 'F'),      # rotary encoder
    'U2': (183.9, 153.9, 270, 'F'),     # MCU: display/UART pins face west, HRTIM/USB south, crystal north
    'J4': (152.4, 164.0, 0, 'F'),       # UART header, left edge below the interlock switch
    'J1': (156.4, 164.0, 0, 'F'),       # BOOT0 jumper next to it
    'TP217': (153.1, 174.6, None, 'F'), # GND test point nudged 0.55 mm to clear the UART header
    # --- USB support parts (front)
    'U3': (192.3, 146.0, 90, 'F'),
    'R9': (195.3, 144.7, 270, 'F'),       # CC1 5.1k
    'R10': (189.6, 144.6, 180, 'F'),      # CC2 5.1k
    'R7': (197.6, 147.0, 270, 'F'),      # VBUS divider top
    'R8': (197.6, 149.0, 270, 'F'),      # VBUS divider bottom
    # --- crystal (front, directly above PF0/PF1)
    'Y1': (185.4, 145.2, 90, 'F'),
    'C11': (187.8, 145.9, 0, 'F'),
    'C12': (183.0, 144.5, 180, 'F'),
    # --- MCU decoupling and small parts (back, under the MCU)
    'C1': (180.4, 150.1, 0, 'B'),       # VDD16/VSS15
    'C4': (187.8, 150.6, 270, 'B'),     # VDD64/VSS63
    'C2': (180.0, 157.4, 90, 'B'),      # VDD32/VSS31
    'C3': (187.4, 157.7, 180, 'B'),     # VDD48/VSS47
    'C5': (185.0, 152.6, 0, 'B'),       # bulk 4.7u
    'C10': (184.6, 150.4, 90, 'B'),     # NRST cap
    'C6': (180.0, 155.4, 90, 'B'), 'C7': (181.1, 155.4, 90, 'B'), 'C8': (182.2, 155.4, 90, 'B'),
    'C9': (183.3, 155.4, 90, 'B'), 'R1': (184.4, 155.4, 90, 'B'),   # VDDA / VREF+ group
    'R2': (188.0, 153.0, 0, 'B'),       # BOOT0 pull-down
    # --- encoder pull-ups / debounce (back, under the encoder)
    'R4': (162.6, 147.3, 0, 'B'), 'C13': (162.6, 148.9, 0, 'B'),
    'R5': (162.6, 153.9, 0, 'B'), 'C14': (162.6, 152.3, 0, 'B'),
    'R6': (172.7, 147.3, 0, 'B'), 'C15': (172.7, 148.9, 0, 'B'),
    'R11': (157.6, 152.7, 90, 'B'),     # interlock bypass
    # --- fault / external-event conditioning (back, between the two header rows, under J301)
    'R334': (165.5, 139.35, 0, 'B'), 'R333': (167.8, 139.35, 0, 'B'),
    'R332': (170.1, 139.35, 0, 'B'), 'R331': (172.4, 139.35, 0, 'B'),
    'R337': (174.7, 139.35, 0, 'B'), 'R338': (177.0, 139.35, 0, 'B'),
    'R335': (179.3, 139.35, 0, 'B'), 'R336': (181.6, 139.35, 0, 'B'),
    # --- HRTIM series resistors and LM5113 input pull-downs (back, under the legacy RC networks)
    'R326': (192.4, 171.6, 0, 'B'), 'R327': (192.4, 172.9, 0, 'B'),
    'R329': (192.4, 174.3, 0, 'B'), 'R330': (192.4, 175.6, 0, 'B'),
    'R320': (192.4, 188.6, 0, 'B'), 'R321': (192.4, 189.9, 0, 'B'),
    'R323': (192.4, 191.3, 0, 'B'), 'R324': (192.4, 192.6, 0, 'B'),
    # --- switch-node sense dividers (back, next to the OutA/OutB vias)
    'R343': (190.2, 179.6, 0, 'B'), 'C338': (192.4, 179.6, 0, 'B'),
    'R339': (192.4, 180.9, 0, 'B'), 'R340': (190.2, 180.9, 0, 'B'),
    'R341': (192.5, 169.0, 0, 'B'), 'C339': (192.5, 170.25, 0, 'B'),
    'R342': (188.3, 168.6, 0, 'B'), 'R344': (188.3, 167.3, 0, 'B'),
}

# new footprints: ref -> (value, net pad1, net pad2, symbol uuid)
NEW = {
    'C13': ('1n', '/MCU/TIM3_CH1_ENCODER', 'GND', '84bb9be7-1c7c-4424-9ffe-852e67ea7915'),
    'C14': ('1n', '/MCU/TIM3_CH2_ENCODER', 'GND', 'df332153-2c60-49f0-83e5-a10a380b93db'),
    'C15': ('100n', '/MCU/GPIO_ENCODER_PUSH', 'GND', 'daf404be-458d-48af-808e-87f0452802be'),
}

CLUSTER = ['U202', 'R214', 'C210', 'R215', 'R216', 'R217', 'R218', 'R219', 'R220', 'R221', 'R222']
CBOX = (166.4, 145.4, 177.1, 153.6)
CDX, CDY = -8.3, 11.3


def main():
    board = pcbnew.LoadBoard(sys.argv[1])
    lid = {board.GetLayerName(i): i for i in board.GetEnabledLayers().Seq()}

    # ---- 1. move the level-shifter cluster rigidly
    delta = V(CDX, CDY)
    for ref in CLUSTER:
        fp = board.FindFootprintByReference(ref)
        fp.Move(delta)
    ALL = list(board.GetTracks())
    gone = set()

    def kill_item(t):
        gone.add(id(t))
        board.Remove(t)

    def live():
        return [t for t in ALL if id(t) not in gone]

    removed = moved = 0
    for t in live():
        ln = board.GetLayerName(t.GetLayer())
        if t.GetClass() == 'PCB_VIA':
            if inbox(t.GetPosition(), CBOX):
                if t.GetNetname() == '+5V':
                    kill_item(t)
                    removed += 1
                else:
                    t.Move(delta)
                    moved += 1
            continue
        a, b = inbox(t.GetStart(), CBOX), inbox(t.GetEnd(), CBOX)
        if ln in ('F.Cu', 'B.Cu'):
            if a and b:
                t.Move(delta)
                moved += 1
            elif a or b:
                kill_item(t)
                removed += 1
    print(f'cluster: moved {moved} tracks/vias, removed {removed} external stubs')

    # ---- 2. remove obsolete copper in the freed area
    n = 0
    for t in live():
        if t.GetClass() == 'PCB_VIA':
            continue
        ln = board.GetLayerName(t.GetLayer())
        net = t.GetNetname()
        (x1, y1), (x2, y2) = xy(t.GetStart()), xy(t.GetEnd())
        kill = False
        if ln == 'In2.Cu':
            # +5V feed to the old cluster position and its run through the MCU area
            if net == '+5V' and max(y1, y2) <= 155.8 and min(x1, x2) >= 166 and max(x1, x2) <= 192.2:
                kill = True
            if net == '+3V3' and max(x1, x2) <= 195.1 and min(x1, x2) >= 150 and t.GetWidth() >= 0.9 * MM:
                kill = True   # ring reinforcement and the feed towards TP214, replaced by the new plane
        elif ln in ('F.Cu', 'B.Cu'):
            if net.endswith('SCL_3.3V') or net.endswith('SDA_3.3V'):
                # run from the old cluster position to the Si5351; re-routed later
                in_cluster = min(x1, x2) >= 158.9 and max(x1, x2) <= 168.0 and min(y1, y2) >= 157.5
                at_si5351 = min(x1, x2) >= 200.7          # pad escapes of the clock generator stay
                if not (in_cluster or at_si5351):
                    kill = True
            if net in ('+3V3', '+5V') and max(x1, x2) <= 158.5 and 159.5 <= min(y1, y2) and max(y1, y2) <= 168:
                kill = True   # leftovers of the removed I2C connector / selector resistors
            if net == 'GND' and ln == 'B.Cu' and 186 <= min(x1, x2) and max(x1, x2) <= 187.6 and 154 <= min(y1, y2) and max(y1, y2) <= 158.5:
                kill = True   # stub of the old Arduino GND pins
        if kill:
            kill_item(t)
            n += 1
    # shorten the In2 +5V spur that ran up through the MCU area
    for t in live():
        if t.GetClass() != 'PCB_VIA' and board.GetLayerName(t.GetLayer()) == 'In2.Cu' and t.GetNetname() == '+5V':
            (x1, y1), (x2, y2) = xy(t.GetStart()), xy(t.GetEnd())
            if abs(x1 - 192.0) < 0.01 and abs(x2 - 192.0) < 0.01 and {round(y1, 2), round(y2, 2)} == {161.7, 155.65}:
                t.SetStart(V(192.0, 161.7))
                t.SetEnd(V(192.0, 158.75))
    print(f'removed {n} obsolete track segments')

    # ---- 3. new footprints
    for ref, (value, n1, n2, uuid) in NEW.items():
        if board.FindFootprintByReference(ref):
            continue
        fp = pcbnew.FootprintLoad('/usr/share/kicad/footprints/Capacitor_SMD.pretty', 'C_0402_1005Metric')
        fp.SetFPIDAsString('Capacitor_SMD:C_0402_1005Metric')
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetPath(pcbnew.KIID_PATH('/' + uuid))
        fp.SetDNP(True)
        board.Add(fp)
        for pad in fp.Pads():
            pad.SetNet(board.FindNet(n1 if pad.GetNumber() == '1' else n2))

    # ---- 4. placement
    for ref, (x, y, rot, side) in PLACE.items():
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            print('MISSING', ref)
            continue
        fp.SetPosition(V(x, y))
        if (side == 'B') != fp.IsFlipped():
            fp.Flip(V(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        if rot is not None:
            fp.SetOrientationDegrees(rot)

    # leg B: PB14 (HRTIM1_CHD1) drives the low side, PB15 (HRTIM1_CHD2) the high side (bootloader-safe)
    for ref, net in (('R326', '/HRTIM1_CHD2'), ('R329', '/HRTIM1_CHD1')):
        for pad in board.FindFootprintByReference(ref).Pads():
            if pad.GetNumber() == '2':
                pad.SetNet(board.FindNet(net))

    # ---- 5. stitching vias that now sit under new through-hole parts
    courts = []
    for ref in ('SW2', 'J3', 'J5', 'J2', 'J301', 'J1', 'SW1', 'J4'):
        fp = board.FindFootprintByReference(ref)
        bb = fp.GetBoundingBox(False)
        courts.append((bb.GetLeft() / MM - 0.3, bb.GetTop() / MM - 0.3, bb.GetRight() / MM + 0.3, bb.GetBottom() / MM + 0.3))
    n = 0
    for t in live():
        if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND':
            if any(inbox(t.GetPosition(), c) for c in courts):
                kill_item(t)
                n += 1
    print(f'removed {n} GND stitching vias under new parts')

    # ---- 6. inner +3V3 plane under the MCU/UI area
    for z in board.Zones():
        if z.GetNetname() == '+3V3' and board.GetLayerName(z.GetLayer()) == 'In2.Cu':
            o = z.Outline()
            o.RemoveAllContours()
            o.NewOutline()
            # the neck between the LDO (east) and the MCU plane is 5 mm wide so that a few vias cannot pinch it
            for x, y in [(198.35, 152.85), (201.75, 152.85), (201.75, 154.1), (191.3, 154.1),
                         (191.3, 163.0), (158.6, 163.0), (158.6, 172.3), (150.5, 172.3), (150.5, 135.5),
                         (189.1, 135.5), (189.1, 143.55)]:
                o.Append(int(x * MM), int(y * MM))
            z.SetIsFilled(False)
            print('re-shaped In2 +3V3 zone')

    n = 0
    for t in live():
        net = t.GetNetname()
        ln = board.GetLayerName(t.GetLayer())
        if t.GetClass() == 'PCB_VIA':
            x, y = xy(t.GetPosition())
            if net == 'GND' and abs(x - 156.75) < 0.01 and abs(y - 165.25) < 0.01:
                kill_item(t); n += 1
            continue
        (x1, y1), (x2, y2) = xy(t.GetStart()), xy(t.GetEnd())
        if ln == 'F.Cu' and net == 'GND' and max(x1, x2) <= 156.8 and min(x1, x2) >= 151 and 160.5 <= min(y1, y2) and max(y1, y2) <= 167:
            kill_item(t); n += 1      # ground stubs of the removed I2C connector
        elif ln == 'F.Cu' and net == 'Net-(U301-A)' and min(x1, x2) >= 188.0 and max(x1, x2) <= 199.6 and min(y1, y2) >= 159.0 and max(y1, y2) <= 164.0:
            kill_item(t); n += 1      # clock run across the MCU's south-east corner, re-routed below the mounting hole
        elif ln == 'In2.Cu' and net == '+5V':
            pts = {(round(x1, 2), round(y1, 2)), (round(x2, 2), round(y2, 2))}
            if pts == {(162.4, 162.3), (160.83, 162.3)}:
                kill_item(t); n += 1
            elif pts == {(171.39, 171.29), (162.4, 162.3)}:
                if round(x1, 2) == 162.4: t.SetStart(V(164.5, 164.4))
                else: t.SetEnd(V(164.5, 164.4))
            elif pts == {(160.83, 179.66), (160.83, 162.3)}:
                if round(y1, 2) == 162.3: t.SetStart(V(160.83, 164.4))
                else: t.SetEnd(V(160.83, 164.4))
    tr = pcbnew.PCB_TRACK(board)
    tr.SetStart(V(160.83, 164.4)); tr.SetEnd(V(164.5, 164.4)); tr.SetWidth(int(1.0 * MM)); tr.SetLayer(lid['In2.Cu'])
    tr.SetNet(board.FindNet('+5V')); board.Add(tr)
    print(f'second clean-up pass removed {n} items')
    for pad in board.FindFootprintByReference('J5').Pads():
        if pad.GetNetname() == 'GND':
            pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    pcbnew.SaveBoard(sys.argv[2], board)
    print('saved', sys.argv[2])


if __name__ == '__main__':
    main()

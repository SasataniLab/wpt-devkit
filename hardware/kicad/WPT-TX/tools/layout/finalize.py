#!/usr/bin/env python3
"""Put a routed board into the repo: schematic data sync, board-only mounting holes, DRC with parity.

usage: finalize.py BOARD_IN REPO_PROJECT_DIR PCB_SIDE_PY
"""
import collections
import os
import re
import shutil
import subprocess
import sys

import pcbnew

src, prj, pcb_side = sys.argv[1:4]
name = 'WPT-01-TRANSMITTER'
tmp = os.path.join(os.path.dirname(os.path.abspath(src)), '_final_tmp')
os.makedirs(tmp, exist_ok=True)
net = os.path.join(tmp, 'repo.net')
subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', net, os.path.join(prj, name + '.kicad_sch')],
               capture_output=True, text=True, check=True)
synced = os.path.join(tmp, 'synced.kicad_pcb')
out = subprocess.run([sys.executable, pcb_side, src, synced, net, '--values'], capture_output=True, text=True)
print('\n'.join(l for l in out.stdout.split('\n') if l.startswith('no footprint') or l.startswith('footprint id')))
b = pcbnew.LoadBoard(synced)
DESC = {'C13': 'Unpolarized capacitor', 'C14': 'Unpolarized capacitor', 'C15': 'Unpolarized capacitor', 'C16': 'Unpolarized capacitor',
        'J301': 'Generic connector, single row, 01x10',
        'J3': 'ST Debug Connector, standard ARM Cortex-M SWD and JTAG interface plus UART',
        'SW3': 'Tactile switch, SPST-NO, side-actuated, with locating boss, 3 x 2.5 mm',
        'SW4': 'Tactile switch, SPST-NO, side-actuated, with locating boss, 3 x 2.5 mm',
        'J2': 'Pin header, 2 x 6, 2.54 mm. Pins 1, 3 ... 11 form one row and 2, 4 ... 12 the other; drawn here as one column'}
SMD_NOT_THT = ('L301', 'L302')                   # Coilcraft 2929SQ, two SMD pads
DATASHEET = {'J3': 'https://www.st.com/resource/en/user_manual/um2448-stlinkv3set-debuggerprogrammer-for-stm8-and-stm32-stmicroelectronics.pdf'}
n = 0
for fp in b.GetFootprints():
    ref = fp.GetReference()
    if ref.startswith('REF**'):
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        n += 1
    if ref in DATASHEET:
        fp.GetField('Datasheet').SetText(DATASHEET[ref])
    if re.fullmatch(r'TP\d+', ref):               # test points are bare pads: not in the BOM, not in the placement files (as in the schematic)
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
    if ref in SMD_NOT_THT:                        # surface-mount parts whose library footprint said "through hole": they were missing from the SMD placement file
        fp.SetAttributes((fp.GetAttributes() & ~pcbnew.FP_THROUGH_HOLE) | pcbnew.FP_SMD)
    if ref in DESC:                               # footprints added by script carry no Description field yet
        f = fp.GetField('Description') if fp.HasField('Description') else None
        if f is not None:
            f.SetText(DESC[ref])
        else:
            fp.SetField('Description', DESC[ref])
            g = fp.GetField('Description')
            if g is not None:
                g.SetVisible(False)
print('mounting holes marked board-only:', n)
dst = os.path.join(prj, name + '.kicad_pcb')
# SaveBoard also writes a project file next to the board. Saving into the repo directly would replace the real
# project settings (rules, net classes, variants) with defaults, so save beside the temporary copy and move the board only.
staged = os.path.join(tmp, name + '.kicad_pcb')
pcbnew.SaveBoard(staged, b)
shutil.copy(staged, dst)
rpt = os.path.join(tmp, 'repo_drc.rpt')
subprocess.run(['kicad-cli', 'pcb', 'drc', '--severity-all', '--schematic-parity', '--refill-zones', '--save-board', '--format', 'report',
                '-o', rpt, dst], capture_output=True, text=True)
txt = open(rpt).read()
bl = [x for x in re.split(r'\n(?=\[)', txt) if x.startswith('[')]
print(dict(collections.Counter(x.split(']')[0][1:] for x in bl)))
print('\n'.join(l for l in txt.split('\n') if l.startswith('** Found')))

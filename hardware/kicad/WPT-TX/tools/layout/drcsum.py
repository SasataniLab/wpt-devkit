#!/usr/bin/env python3
"""Run KiCad DRC on a board (refill zones, save) and summarise. usage: drcsum.py BOARD [--all]"""
import json
import subprocess
import sys
from collections import Counter
board = sys.argv[1]
rpt = board.replace('.kicad_pcb', '_drc.json')
subprocess.run(['kicad-cli', 'pcb', 'drc', '--refill-zones', '--save-board', '--format', 'json', '--severity-all', '-o', rpt, board],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
d = json.load(open(rpt))
c = Counter(v['type'] for v in d.get('violations', []))
u = d.get('unconnected_items', [])
print({k: v for k, v in c.items() if not k.startswith('silk') and not k.startswith('lib_')}, 'unconnected', len(u))
show = ('clearance', 'shorting_items', 'tracks_crossing', 'track_dangling', 'via_dangling', 'hole_clearance', 'copper_edge_clearance', 'hole_to_hole', 'solder_mask_bridge')
for v in d.get('violations', []):
    if v['type'] in show or '--all' in sys.argv:
        if v['type'].startswith('silk') or v['type'].startswith('lib_'):
            continue
        print(' ', v['type'], '|', v['description'][:70], '|', ' ; '.join('%s @(%.2f,%.2f)' % (i['description'][:60], i['pos']['x'], i['pos']['y']) for i in v['items']))
for v in u:
    print('  UNCONNECTED', ' ; '.join('%s @(%.2f,%.2f)' % (i['description'][:60], i['pos']['x'], i['pos']['y']) for i in v['items']))

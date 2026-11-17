#!/usr/bin/env python3
"""Print what a DRC report (kicad-cli pcb drc --format json) contains. usage: drc_summary.py REPORT.json [-v]"""
import collections
import json
import sys

d = json.load(open(sys.argv[1]))
verbose = '-v' in sys.argv
total = 0
for key in ('violations', 'unconnected_items', 'schematic_parity'):
    items = d.get(key, [])
    total += len(items)
    print('%-18s %3d  %s' % (key, len(items), dict(collections.Counter(v['type'] for v in items))))
    if verbose:
        for v in items:
            print('   %s | %s' % (v['type'], v['description'][:110]))
            for it in v.get('items', []):
                print('        %s %s' % (it['description'][:100], it.get('pos')))
sys.exit(1 if total else 0)

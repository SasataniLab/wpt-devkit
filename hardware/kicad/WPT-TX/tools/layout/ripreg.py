#!/usr/bin/env python3
"""Take the auto-routed copper of the named nets out of a board (hand-placed copper stays). usage: ripreg.py BOARD REG.json NET..."""
import json
import sys

from nego import rip_text

path, regfile = sys.argv[1:3]
want = set(sys.argv[3:])
tup = lambda q: tuple(tuple(x) if isinstance(x, list) else x for x in q)
reg = json.load(open(regfile))
keys = set()
for n in reg:
    if n.split('/')[-1] in want:
        keys |= {tup(q) for q in reg[n]}
        reg[n] = []
print('removed', rip_text(path, keys), 'of', len(keys))
json.dump(reg, open(regfile, 'w'))

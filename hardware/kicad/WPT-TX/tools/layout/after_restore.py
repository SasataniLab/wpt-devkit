#!/usr/bin/env python3
"""After restore_old.py: take out the leftovers of the old header entries and the old SDA_3.3V crossing under the
east side of the MCU, and give HRTIM1_FLT4 its new entry from J301 pin 8. usage: after_restore.py BOARD REG.json"""
import json
import sys

import pcbnew

import router as R
from nego import rip_text

R.DEFAULT_CORRIDORS = ()
path, regfile = sys.argv[1:3]
MM = 1e6
short = lambda n: n.split('/')[-1]
tup = lambda q: tuple(tuple(x) if isinstance(x, list) else x for x in q)
REG = {n: [tup(q) for q in ks] for n, ks in json.load(open(regfile)).items()}
# (net, box, layers): every registered piece of the net with all its points inside the box goes out
KILL = [('HRTIM1_FLT4', (165.0, 137.0, 168.6, 141.0), ('B.Cu',)),      # old entry from the former J301 position
        ('HRTIM1_FLT3', (168.5, 137.0, 173.0, 140.1), ('B.Cu',)),
        ('SDA_3.3V', (166.3, 155.0, 188.5, 160.6), None),                # old run east under the MCU: the corridor east of
        ('SCL_3.3V', (162.25, 140.5, 162.6, 141.2), ('B.Cu',))]          # the MCU now belongs to the divider taps (back side)
kill = set()
for net, ks in REG.items():
    for name, (x0, y0, x1, y1), layers in KILL:
        if short(net) != name:
            continue
        for k in ks:
            pts = [k[2]] if k[0] == 'V' else [k[3], k[4]]
            if (layers is None or k[0] == 'V' or k[2] in layers) and all(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in pts):
                kill.add(k)
print('removed', rip_text(path, kill), 'of', len(kill))
REG = {n: [k for k in ks if k not in kill] for n, ks in REG.items()}
r = R.Router(path, reg=REG)
r._fixed = True
flt4 = [n for n in r.nets if short(n) == 'HRTIM1_FLT4'][0]
# through the gap between J2 pins 4 and 5, then one diagonal into J301 pin 8 (1.8 mm beside the one of FLT3)
for p, q in zip([(167.15, 141.05), (167.15, 140.27), (171.00, 136.42)], [(167.15, 140.27), (171.00, 136.42)]):
    r.add_track(flt4, 'B.Cu', p, q, 0.2)
r.save()
json.dump({k: [list(q) for q in v] for k, v in r.reg.items()}, open(regfile, 'w'))
print('written', path)

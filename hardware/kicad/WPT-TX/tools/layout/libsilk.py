#!/usr/bin/env python3
"""Take the silkscreen graphics of footprint file NEW into footprint file OLD and write the result to OUT; everything
else of OLD (fields, attributes, pads, other layers) stays. usage: libsilk.py OLD NEW OUT"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'schematic'))
import sx

old, new, out = sys.argv[1:4]
KINDS = ('fp_line', 'fp_circle', 'fp_arc', 'fp_rect', 'fp_poly')


def silk(text):
    root = sx.parse(text)
    return [n for k in KINDS for n in root.kids(k) if n.val('layer', '') in ('F.SilkS', 'F.Silkscreen')]


so, sn = open(old, encoding='utf-8').read(), open(new, encoding='utf-8').read()
no, nn = sorted(silk(so), key=lambda n: n.start), sorted(silk(sn), key=lambda n: n.start)
assert no and nn, (len(no), len(nn))
ins = no[0].start
for n in reversed(no):
    lead = so.rfind('\n', 0, n.start)
    so = so[:lead] + so[n.end:] if n is not no[0] else so[:n.start] + so[n.end:]
so = so[:ins] + '\n\t'.join(n.text(sn) for n in nn) + so[ins:]
assert so.count('(') == so.count(')')
sx.parse(so)
open(out, 'w', encoding='utf-8').write(so)
print(os.path.basename(out), 'silk items', len(no), '->', len(nn))

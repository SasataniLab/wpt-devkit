#!/usr/bin/env python3
"""Remove every track and via of the named nets (pads stay). usage: stripnets.py BOARD NET [NET ...]  (last part of the name)"""
import re
import sys

path, names = sys.argv[1], set(sys.argv[2:])
lines = open(path, encoding='utf-8').read().split('\n')
out, i, gone = [], 0, 0
while i < len(lines):
    if lines[i] in ('\t(segment', '\t(via'):
        j = i + 1
        while lines[j] != '\t)':
            j += 1
        m = re.search(r'\(net "(.*)"\)', '\n'.join(lines[i:j + 1]))
        if m and m.group(1).split('/')[-1] in names:
            gone += 1
            i = j + 1
            continue
        out.extend(lines[i:j + 1])
        i = j + 1
        continue
    out.append(lines[i])
    i += 1
open(path, 'w', encoding='utf-8').write('\n'.join(out))
print('removed', gone, 'tracks and vias of', sorted(names))

#!/usr/bin/env python3
"""Remove dead-end copper once every net is connected. usage: cleanup.py BOARD [max_passes]

A track is a candidate only when KiCad DRC reports it as dangling and layer, net, one end point and length all match.
KiCad also calls a track dangling when its end sits exactly on the edge of a pad, so every removal is verified:
if the number of open connections goes up, the pass is undone and its candidates are tried one by one.
"""
import math
import re
import shutil
import sys

import pcbnew

import router as R
from nego import rip_text   # noqa: E402

path = sys.argv[1]
passes = int(sys.argv[2]) if len(sys.argv) > 2 else 12
MM = 1e6
bak = path + '.bak'


def survey():
    txt = R.run_drc(path, path.replace('.kicad_pcb', '_clean.rpt'))
    bl = [b for b in re.split(r'\n(?=\[)', txt) if b.startswith('[')]
    want = []
    for blk in bl:
        kind = blk.split(']')[0][1:]
        if kind not in ('track_dangling', 'via_dangling'):
            continue
        m = R.ITEM.search(blk)
        x, y, desc = float(m.group(1)), float(m.group(2)), m.group(3)
        net = re.search(r'\[([^\]]*)\]', desc).group(1)
        lay = re.search(r' on ([FB]\.Cu|In\d\.Cu)', desc)
        ln = re.search(r'length ([\d.]+) mm', desc)
        want.append((kind, net, x, y, lay.group(1) if lay else None, float(ln.group(1)) if ln else None))
    return len(R.parse_unconnected(txt)), want


def keys_for(want):
    b = pcbnew.LoadBoard(path)
    out = {}
    for t in b.GetTracks():
        net = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            c = (t.GetPosition().x / MM, t.GetPosition().y / MM)
            for w in want:
                if w[0] == 'via_dangling' and w[1] == net and math.dist(c, (w[2], w[3])) < 0.003:
                    out[w] = R.Router.vkey(net, c)
        else:
            a = (t.GetStart().x / MM, t.GetStart().y / MM)
            e = (t.GetEnd().x / MM, t.GetEnd().y / MM)
            layer = b.GetLayerName(t.GetLayer())
            L = t.GetLength() / MM
            for w in want:
                if w[0] == 'track_dangling' and w[1] == net and w[4] == layer and w[5] is not None and abs(L - w[5]) < 0.002 \
                        and (math.dist(a, (w[2], w[3])) < 0.003 or math.dist(e, (w[2], w[3])) < 0.003):
                    out[w] = R.Router.tkey(net, layer, a, e)
    return out


keep = set()                      # reported as dangling but needed
open_now, want = survey()
print(f'start: {open_now} open connections, {len(want)} dangling items')
for it in range(passes):
    cand = keys_for([w for w in want if w not in keep])
    if not cand:
        break
    shutil.copy(path, bak)
    rip_text(path, set(cand.values()))
    n2, want2 = survey()
    if n2 <= open_now:
        print(f'pass {it}: removed {len(cand)}')
        open_now, want = n2, want2
        continue
    # something in this batch was live copper: undo and test one at a time
    shutil.copy(bak, path)
    removed = 0
    for w, k in cand.items():
        shutil.copy(path, bak)
        rip_text(path, {k})
        n2, _ = survey()
        if n2 > open_now:
            shutil.copy(bak, path)
            keep.add(w)
            print(f'   kept (needed): {w[1].split("/")[-1]} {w[4]} at ({w[2]}, {w[3]})')
        else:
            removed += 1
    print(f'pass {it}: removed {removed} one by one, kept {len(keep)}')
    open_now, want = survey()
print(f'end: {open_now} open connections, {len([w for w in want if w not in keep])} dangling left, {len(keep)} kept as needed')

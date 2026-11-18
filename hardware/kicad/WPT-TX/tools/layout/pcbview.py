#!/usr/bin/env python3
"""Render a board JSON model (from pcbdump.py) to PNG with mm axes.

usage: pcbview.py MODEL.json OUT.png [--win x0 y0 x1 y1] [--layers F.Cu,B.Cu] [--scale px_per_mm]
                 [--refs] [--nets] [--rats RATS.json] [--side F|B|both] [--zones] [--padnum]
"""
import argparse
import json
import math

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.patches import Circle, Polygon, Rectangle

COL = {'F.Cu': '#c83232', 'B.Cu': '#3264c8', 'In1.Cu': '#2e9e4a', 'In2.Cu': '#c8a032'}


def rot(px, py, cx, cy, deg):
    a = math.radians(-deg)
    dx, dy = px - cx, py - cy
    return cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)


def pad_poly(p):
    cx, cy = p['pos']
    w, h = p['size']
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    a = math.radians(-p['rot'])
    return [(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)) for x, y in pts]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model')
    ap.add_argument('out')
    ap.add_argument('--win', nargs=4, type=float)
    ap.add_argument('--layers', default='F.Cu,B.Cu,In1.Cu,In2.Cu')
    ap.add_argument('--scale', type=float, default=12)
    ap.add_argument('--refs', action='store_true')
    ap.add_argument('--nets', action='store_true', help='label pads with net names')
    ap.add_argument('--padnum', action='store_true')
    ap.add_argument('--rats', help='json list of [[x,y],[x,y],net] unrouted connections')
    ap.add_argument('--side', default='both')
    ap.add_argument('--zones', action='store_true')
    ap.add_argument('--hl', default='', help='comma separated net names to highlight')
    ap.add_argument('--grid', type=float, default=0)
    a = ap.parse_args()

    m = json.load(open(a.model))
    x0, y0, x1, y1 = a.win if a.win else [m['bbox'][0] - 2, m['bbox'][1] - 2, m['bbox'][2] + 2, m['bbox'][3] + 2]
    layers = a.layers.split(',')
    hl = set(n for n in a.hl.split(',') if n)
    W, H = (x1 - x0), (y1 - y0)
    fig = plt.figure(figsize=(W * a.scale / 100, H * a.scale / 100), dpi=100)
    ax = fig.add_axes([0.045, 0.045, 0.95, 0.95])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y1, y0)
    ax.set_aspect('equal')
    ax.set_facecolor('#101418')
    lw_per_mm = a.scale * 72 / 100  # points per mm

    def inwin(x, y, mrg=3):
        return x0 - mrg <= x <= x1 + mrg and y0 - mrg <= y <= y1 + mrg

    # zones outlines
    if a.zones:
        for z in m['zones']:
            if not any(l in layers for l in z['layers']):
                continue
            for o in z['outline']:
                c = '#ff00ff' if z['rule_area'] else COL.get(z['layers'][0], '#888')
                ax.add_patch(Polygon(o, closed=True, fill=False, ec=c, lw=0.8, ls='--', alpha=0.9))
                cx = sum(p[0] for p in o) / len(o)
                cy = sum(p[1] for p in o) / len(o)
                if inwin(cx, cy, 0):
                    ax.text(cx, cy, ('KEEPOUT' if z['rule_area'] else z['net'].split('/')[-1]) + '@' + z['layers'][0][:3],
                            color=c, fontsize=5, ha='center', alpha=0.9)

    # tracks
    for ln in ['In1.Cu', 'In2.Cu', 'B.Cu', 'F.Cu']:
        if ln not in layers:
            continue
        segs, lws, cols = [], [], []
        for t in m['tracks']:
            if t['layer'] != ln:
                continue
            if not (inwin(*t['start']) or inwin(*t['end'])):
                continue
            segs.append([t['start'], t['end']])
            lws.append(max(t['width'] * lw_per_mm, 0.3))
            cols.append('#ffff00' if t['net'] in hl else COL[ln])
        ax.add_collection(LineCollection(segs, linewidths=lws, colors=cols, alpha=0.75, capstyle='round'))

    # vias
    for v in m['vias']:
        if inwin(*v['pos']):
            ax.add_patch(Circle(v['pos'], v['size'] / 2, fc='#d0d0d0' if v['net'] not in hl else '#ffff00', ec='none', alpha=0.9))
            ax.add_patch(Circle(v['pos'], v['drill'] / 2, fc='#101418', ec='none'))

    # footprints
    for f in m['footprints']:
        if a.side != 'both' and f['side'] != a.side:
            continue
        b = f['court'] or f['bbox']
        if b[2] < x0 or b[0] > x1 or b[3] < y0 or b[1] > y1:
            continue
        ec = '#e0e0e0' if f['side'] == 'F' else '#60a0ff'
        ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fill=False, ec=ec, lw=0.5, ls='-' if f['side'] == 'F' else ':'))
        for p in f['pads']:
            onF = 'F.Cu' in p['layers']
            onB = 'B.Cu' in p['layers']
            c = '#e06060' if onF and not onB else ('#6090e0' if onB and not onF else '#c0a040')
            if p['net'] in hl:
                c = '#ffff00'
            if not p['net']:
                c = '#707070'
            ax.add_patch(Polygon(pad_poly(p), closed=True, fc=c, ec='none', alpha=0.95))
            if p['drill'] > 0:
                ax.add_patch(Circle(p['pos'], p['drill'] / 2, fc='#101418', ec='none'))
            if a.nets and p['net'] and inwin(*p['pos'], 0):
                ax.text(p['pos'][0], p['pos'][1], p['net'].split('/')[-1][:14], color='white', fontsize=3.2, ha='center', va='center')
            elif a.padnum and inwin(*p['pos'], 0):
                ax.text(p['pos'][0], p['pos'][1], p['num'], color='white', fontsize=3.2, ha='center', va='center')
        if a.refs:
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            if inwin(cx, cy, 0):
                ax.text(cx, b[1] - 0.1, f['ref'] + ('*' if f['dnp'] else ''), color='#80ff80' if f['side'] == 'F' else '#80c0ff',
                        fontsize=4.5, ha='center', va='bottom')

    # edge cuts
    for d in m['drawings']:
        if d['layer'] == 'Edge.Cuts' and d.get('shape'):
            if d['shape'] in ('S_SEGMENT', 'Line', 'Segment', 'S_RECT', 'Rect') or 'start' in d:
                if d['shape'].lower().endswith('rect'):
                    ax.add_patch(Rectangle(d['start'], d['end'][0] - d['start'][0], d['end'][1] - d['start'][1], fill=False, ec='#ffff60', lw=1))
                else:
                    ax.plot([d['start'][0], d['end'][0]], [d['start'][1], d['end'][1]], color='#ffff60', lw=1)

    # ratsnest
    if a.rats:
        for r in json.load(open(a.rats)):
            (ax1, ay1), (ax2, ay2) = r[0], r[1]
            if inwin(ax1, ay1) or inwin(ax2, ay2):
                ax.plot([ax1, ax2], [ay1, ay2], color='#00ffff', lw=0.5, alpha=0.8)

    if a.grid:
        ax.set_xticks([x0 + i * a.grid for i in range(int(W / a.grid) + 1)])
        ax.set_yticks([y0 + i * a.grid for i in range(int(H / a.grid) + 1)])
        ax.grid(True, color='#405060', lw=0.3, alpha=0.6)
    ax.tick_params(labelsize=5, colors='black')
    fig.savefig(a.out, dpi=100)
    print('wrote', a.out, fig.get_size_inches() * 100)


if __name__ == '__main__':
    main()

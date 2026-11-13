#!/usr/bin/env python3
"""Negotiated rip-up and re-route on the two outer layers.

usage: nego.py BOARD [max_rips]

The list of open connections is taken once from KiCad DRC. Every connection is routed in turn; when no legal
path exists the connection is routed across copper this router added earlier, the nets it crossed are ripped up
and queued again. A net gets more expensive to cross every time it has been ripped, which is what stops two
nets from evicting each other for ever.
"""
import collections
import json
import math
import sys
import time

import router as R
from do_route import prio, rip, PLANE   # noqa: E402  (do_route is import-safe: see __main__ guard there)

path = sys.argv[1] if len(sys.argv) > 1 else ''
if '--no-corridors' in sys.argv:
    R.DEFAULT_CORRIDORS = ()
MAX_RIPS = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 300
NET_CAP = 10
PROT = {'GND', '+3V3', '+5V', '/VBUS', '/USB_D_P', '/USB_D_N', 'Net-(J5-CC1)', 'Net-(J5-CC2)', 'Net-(U2-VDDA)', 'Net-(U2-PF0)',
        'Net-(U2-PF1)', 'Net-(U301-A)'}


SLOW = ('USART1', 'SCL', 'SDA', 'ENCODER', 'HV_EN_MCU', 'HV_SW_STATE', 'HV_EN_SW', 'J1-Pin_1', 'WLAT', 'ALERT', 'GPIO_DISP_CS',
        'GPIO_DISP_DC', 'GPIO_DISP_RST', 'GPIO_SW_MISC1')
USE_INNER = '--inner' in sys.argv


# sense lines that stay on the back side under the planes, and nets whose new copper must not be ripped up again
BONLY = tuple(sys.argv[sys.argv.index('--back-only') + 1].split(',')) if '--back-only' in sys.argv else ()
KEEP = tuple(sys.argv[sys.argv.index('--keep') + 1].split(',')) if '--keep' in sys.argv else ()


def slow_ok(net):
    """Static or kHz-range signals that may use the inner power layer inside router.INNER_BOXES."""
    return USE_INNER and any(k in net for k in SLOW)


def short(n):
    return n.split('/')[-1]


REGFILE = path.replace('.kicad_pcb', '_reg.json')


def rip_text(board_path, keys):
    """Delete tracks and vias from the board file itself (pcbnew's Remove() leaves the Python bindings unstable)."""
    import re
    lines = open(board_path, encoding='utf-8').read().split('\n')
    out, i, gone = [], 0, 0
    num = r'(-?[\d.]+)'
    while i < len(lines):
        if lines[i] in ('\t(segment', '\t(via'):
            j = i + 1
            while lines[j] != '\t)':
                j += 1
            txt = '\n'.join(lines[i:j + 1])
            m = re.search(r'\(net "(.*)"\)', txt)
            net = m.group(1) if m else ''
            if lines[i] == '\t(via':
                p = re.search(r'\(at ' + num + ' ' + num + r'\)', txt)
                k = ('V', net, (round(float(p.group(1)), 3), round(float(p.group(2)), 3)))
            else:
                s = re.search(r'\(start ' + num + ' ' + num + r'\)', txt)
                e = re.search(r'\(end ' + num + ' ' + num + r'\)', txt)
                lay = re.search(r'\(layer "([^"]+)"\)', txt).group(1)
                pq = sorted([(round(float(s.group(1)), 3), round(float(s.group(2)), 3)), (round(float(e.group(1)), 3), round(float(e.group(2)), 3))])
                k = ('T', net, lay, pq[0], pq[1])
            if k in keys:
                gone += 1
                i = j + 1
                continue
            out.extend(lines[i:j + 1])
            i = j + 1
            continue
        out.append(lines[i])
        i += 1
    open(board_path, 'w', encoding='utf-8').write('\n'.join(out))
    return gone


def rip_nets(r, nets):
    """Remove the copper this router added for the given nets, save board and registry together, reload."""
    import gc
    keys = set(k for n in nets for k in r.reg.get(n, []))
    r.save()
    reg, prot = r.reg, r.protected
    del r
    gc.collect()
    rip_text(path, keys)
    for net in nets:
        reg.pop(net, None)
    json.dump(reg, open(REGFILE, 'w'), default=list)
    json.dump(dict(ripcount), open(RCFILE, 'w'))
    for k in range(4):
        try:
            return R.Router(path, reg=reg, protected=prot)
        except AttributeError:
            gc.collect()
            time.sleep(0.5)
    print('RELOAD FAILED: restart with --resume', flush=True)
    sys.exit(3)


def attempt(r, c, margins=(4.0, 10.0, 30.0)):
    for m in margins:
        if r.route(c['net'], c['A'], c['B'], margin=m, max_nodes=6_000_000, inner=slow_ok(c['net']),
                   allow_via=short(c['net']) not in BONLY, via_cost=12.0 if short(c['net']) in KEEP else 3.0):
            return True
    return False


def main():
    global r, rips, ripcount, RCFILE, REG
    txt = R.run_drc(path, path.replace('.kicad_pcb', '_nego0.rpt'))
    conns = []
    for a, b in R.parse_unconnected(txt):
        net = a['net']
        if net in PLANE or 'CN301' in a['desc'] + b['desc'] or 'Zone' in (a['kind'], b['kind']):
            continue
        if short(net) in KEEP:
            PROT.add(net)
        if 'In2.Cu' in a['desc'] or 'In2.Cu' in b['desc']:
            continue
        conns.append({'net': net, 'A': (a['x'], a['y'], a['layers']), 'B': (b['x'], b['y'], b['layers']),
                      'd': math.dist((a['x'], a['y']), (b['x'], b['y'])), 'desc': (a['desc'][:38], b['desc'][:38])})
    keepfile = path.replace('.kicad_pcb', '_keep.json')
    try:
        PROT.update(json.load(open(keepfile)))          # nets protected in an earlier round stay protected
    except OSError:
        pass
    json.dump(sorted(n for n in PROT if short(n) in KEEP), open(keepfile, 'w'))
    # hand-given extra connections (for a supply pad that the pours cannot reach): --extra 'NET;x,y,LAYERS;x,y,LAYERS'
    donefile = path.replace('.kicad_pcb', '_extra_done')
    import os
    if not os.path.exists(donefile):
        for k, arg in enumerate(sys.argv):
            if arg == '--extra':
                net, pa, pb = sys.argv[k + 1].split(';')
                ax, ay, al = pa.split(',')
                bx, by, bl2 = pb.split(',')
                A = (float(ax), float(ay), al.split('+'))
                B = (float(bx), float(by), bl2.split('+'))
                conns.append({'net': net, 'A': A, 'B': B, 'd': math.dist(A[:2], B[:2]), 'desc': ('extra', 'extra')})
        open(donefile, 'w').write('1')
    conns.sort(key=lambda c: (prio(c['net']), c['d']))
    for i, c in enumerate(conns):
        c['id'] = i
    bynet = collections.defaultdict(list)
    for c in conns:
        bynet[c['net']].append(c)
    print(f'{len(conns)} connections on {len(bynet)} nets', flush=True)

    REG = {}
    if '--resume' in sys.argv:
        # copper added by an earlier run stays rip-able
        def tup(k):
            return tuple(tuple(x) if isinstance(x, list) else x for x in k)
        REG = {net: [tup(k) for k in ks] for net, ks in json.load(open(sys.argv[sys.argv.index('--resume') + 1])).items()}
        print('resumed', sum(len(v) for v in REG.values()), 'pieces of copper on', len(REG), 'nets', flush=True)
    r = R.Router(path, reg=REG, protected=PROT)
    queue = collections.deque(conns)
    queued = set(c['id'] for c in conns)
    RCFILE = path.replace('.kicad_pcb', '_rc.json')
    ripcount = collections.Counter()
    if '--resume' in sys.argv:
        try:
            ripcount.update(json.load(open(RCFILE)))
        except OSError:
            pass
    tries = collections.Counter()
    rips = 0
    fails = {}
    t0 = time.time()
    step = 0
    while queue:
        c = queue.popleft()
        queued.discard(c['id'])
        step += 1
        net = c['net']
        if attempt(r, c):
            fails.pop(c['id'], None)
            continue
        tries[c['id']] += 1
        if rips >= MAX_RIPS or tries[c['id']] > 6:
            fails[c['id']] = 'budget'
            continue
        r.softfac = {n: float((1 + ripcount[n]) ** 2) * (5.0 if prio(n) <= 2 else 1.0) for n in r.nets}
        hit = False
        for sm in (5.0, 12.0, 30.0):
            hit = r.route(net, c['A'], c['B'], margin=sm, max_nodes=10_000_000, soft=True, inner=slow_ok(net), allow_via=short(net) not in BONLY)
            if hit is not False:
                break
        if hit is False:
            fails[c['id']] = 'hard'
            print(f'  [{step}] {short(net)}: no path even across rip-able copper', flush=True)
            continue
        hit = set(hit)
        if not hit:
            # a legal path exists in the wide window after all
            if not attempt(r, c, margins=(30.0, 45.0)):
                fails[c['id']] = 'odd'
            continue
        if any(ripcount[h] >= NET_CAP for h in hit):
            fails[c['id']] = 'cap'
            print(f'  [{step}] {short(net)}: would need {sorted(short(h) for h in hit)} (capped)', flush=True)
            continue
        for h in hit:
            ripcount[h] += 1
        rips += 1
        r = rip_nets(r, hit)
        ok = attempt(r, c)
        print(f'  [{step}] {short(net)}: ripped {sorted(short(h) for h in hit)} -> {"ok" if ok else "FAIL"}  (rips {rips}, queue {len(queue)}, {time.time() - t0:.0f} s)', flush=True)
        if not ok:
            if c['id'] not in queued:
                queue.append(c)
                queued.add(c['id'])
        else:
            fails.pop(c['id'], None)
        for h in hit:
            for c2 in bynet[h]:
                if c2['id'] not in queued:
                    queue.append(c2)
                    queued.add(c2['id'])
    # last chance for everything that was given up on while the board was still changing
    for cid in list(fails):
        c = conns[cid]
        if attempt(r, c):
            fails.pop(cid)
    r.save()
    json.dump(REG, open(REGFILE, 'w'), default=list)
    print(f'done: {len(conns) - len(fails)} of {len(conns)} routed, {rips} rip-ups, {time.time() - t0:.0f} s', flush=True)
    for cid, why in fails.items():
        c = conns[cid]
        print('   FAIL', why, short(c['net']), round(c['d'], 1), c['desc'], flush=True)
    print('ripcount', {short(k): v for k, v in ripcount.most_common(12)}, flush=True)
    json.dump(dict(ripcount), open(RCFILE, 'w'))
    # nets ripped in this run are only queued again when they were in this run's list: let the wrapper start another round
    sys.exit(4 if rips else 0)


if __name__ == '__main__':
    main()

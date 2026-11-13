#!/usr/bin/env python3
"""Routing driver: DRC -> unconnected pairs -> A* -> save, repeated. usage: do_route.py BOARD [max_iters]"""
import collections, math, re, sys, time
import router as R

PLANE = {'GND', '+3V3'}
path = sys.argv[1] if len(sys.argv) > 1 else ''
iters = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 4


def prio(net):
    if net == 'Net-(U301-A)':
        return -1
    if net in ('Net-(U2-PF0)', 'Net-(U2-PF1)', 'Net-(U2-VDDA)') or net in PLANE:
        return 0
    if 'USB' in net or 'VBUS' in net or 'CC' in net:
        return 1
    if any(k in net for k in ('HRTIM1_CH', '_Sig', 'OutA', 'OutB', 'VSW')):
        return 2
    return 3


def manual(r):
    """Hand-placed pieces the grid router should not improvise (kept as fixed copper)."""
    r._fixed = True
    T = lambda net, pts, w=0.2: [r.add_track(net, 'F.Cu', a, b, w) for a, b in zip(pts, pts[1:])]
    # +5V for the relocated level shifter: via onto the In2 +5V link
    r.add_via('+5V', (162.2, 164.2))
    # USB-C: join the two D+ pads below the pad row and the two D- pads above it (under the shell)
    T('/USB_D_P', [(193.05, 142.6), (193.05, 143.35), (194.05, 143.35), (194.05, 142.6)])
    T('/USB_D_N', [(193.55, 142.1), (193.55, 141.35), (194.55, 141.35), (194.55, 142.1)])
    # connector -> ESD array
    T('/USB_D_P', [(193.05, 143.35), (193.05, 143.55), (192.75, 143.85), (191.7, 143.85), (191.35, 144.2), (191.35, 144.5)])
    T('/USB_D_N', [(194.55, 142.6), (194.55, 143.75), (194.05, 144.25), (193.4, 144.25)])
    # ESD array -> MCU: out of the south side, along the south strip, up the east side, straddling the ESD ground pin
    T('/USB_D_P', [(186.65, 160.1), (186.65, 162.3), (187.05, 162.7), (191.6, 162.7), (192.0, 162.3), (192.0, 151.5),
                   (191.35, 150.85), (191.35, 147.4)], 0.3)
    T('/USB_D_N', [(186.15, 160.1), (186.15, 162.7), (186.65, 163.2), (192.0, 163.2), (192.5, 162.7), (192.5, 151.5),
                   (193.25, 150.75), (193.25, 147.4)], 0.3)
    # ESD array ground pin and VBUS pin drop straight to vias
    T('GND', [(192.3, 147.4), (192.3, 148.9)], 0.25)
    r.add_via('GND', (192.3, 148.9))
    T('/VBUS', [(192.3, 145.1), (192.3, 145.95)], 0.25)
    r.add_via('/VBUS', (192.3, 145.95))
    # the ESD array is flow-through: its two pins per line are joined under the body
    T('/USB_D_P', [(191.35, 144.86), (191.35, 147.14)], 0.3)
    T('/USB_D_N', [(193.25, 144.86), (193.25, 147.14)], 0.3)
    # the two VBUS pad groups are joined under the connector shell; one via on the board side of the east group
    T('/VBUS', [(191.55, 142.2), (191.55, 140.6), (196.05, 140.6), (196.05, 142.2)])
    T('/VBUS', [(196.2, 142.6), (196.2, 143.9)], 0.25)
    r.add_via('/VBUS', (196.2, 143.9))
    # VBUS: back-side link to the ESD array, front-side run to the sense divider; divider mid-point link
    for a_, b_ in zip([(192.3, 145.95), (192.9, 145.35), (194.75, 145.35), (196.2, 143.9)], [(192.9, 145.35), (194.75, 145.35), (196.2, 143.9)]):
        r.add_track('/VBUS', 'B.Cu', a_, b_, 0.25)
    T('/VBUS', [(196.2, 143.9), (196.2, 144.6), (197.2, 145.6), (197.6, 146.0), (197.6, 146.4)], 0.25)
    T('/GPIO_VUSB_SENSE', [(197.6, 147.51), (197.6, 148.49)], 0.25)
    # CC lines to their 5.1k resistors
    T('Net-(J5-CC1)', [(195.05, 142.6), (195.05, 143.55), (195.3, 143.8), (195.3, 144.1)])
    T('Net-(J5-CC2)', [(192.05, 142.6), (192.05, 143.15), (191.85, 143.35), (190.9, 143.35), (190.3, 143.95), (190.3, 144.4)])
    r._fixed = False


def rip(path, r, nets):
    """Remove the copper this router added for the given nets and reload."""
    keys = set(k for n in nets for k in r.reg.get(n, []))
    b = r.board
    MMX = 1e6
    n = 0
    for t in list(b.GetTracks()):
        net = t.GetNetname()
        if net not in nets:
            continue
        if t.GetClass() == 'PCB_VIA':
            k = r.vkey(net, (t.GetPosition().x / MMX, t.GetPosition().y / MMX))
        else:
            k = r.tkey(net, b.GetLayerName(t.GetLayer()), (t.GetStart().x / MMX, t.GetStart().y / MMX), (t.GetEnd().x / MMX, t.GetEnd().y / MMX))
        if k in keys:
            b.Remove(t)
            n += 1
    for net in nets:
        r.reg.pop(net, None)
    r.save()
    return R.Router(path, reg=r.reg, protected=r.protected)


INNER = '--inner' in sys.argv
if '--no-corridors' in sys.argv:
    R.DEFAULT_CORRIDORS = ()
PLANES_ONLY = '--planes-only' in sys.argv
FAST = ('HRTIM1_CH', '_Sig', 'USB_D', 'U2-PF', 'VSWA_SENSE', 'VSWB_SENSE', 'OutA', 'OutB', 'U301-A', 'VBUS', 'CC')


def slow(net):
    """Nets that may borrow the inner power layer (as the legacy board already does)."""
    return INNER and not any(k in net for k in FAST) and net not in PLANE


def attempt(r, net, A, B, **kw):
    kw.setdefault('inner', slow(net))
    for margin in (4.0, 10.0, 30.0):
        if r.route(net, A, B, margin=margin, max_nodes=6_000_000, **kw):
            return True
    return False


def main():
    global REG, PROT
    if '--manual' in sys.argv:
        r = R.Router(path)
        manual(r)
        r.save()
    REG, PROT = {}, {'GND', '+3V3', '+5V', '/VBUS', '/USB_D_P', '/USB_D_N', 'Net-(J5-CC1)', 'Net-(J5-CC2)', 'Net-(U2-VDDA)', 'Net-(U2-PF0)', 'Net-(U2-PF1)', 'Net-(U301-A)'}
    RIP_PASSES = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 4
    ripcount = collections.Counter()
    for it in range(iters):
        txt = R.run_drc(path, path.replace('.kicad_pcb', f'_drc{it}.rpt'))
        tasks = R.parse_unconnected(txt)
        print(f'--- iteration {it}: {len(tasks)} unconnected')
        if not tasks:
            break
        r = R.Router(path, reg=REG, protected=PROT)
        tasks.sort(key=lambda t: (prio(t[0]['net']), math.dist((t[0]['x'], t[0]['y']), (t[1]['x'], t[1]['y']))))
        done = fail = 0
        failed = []
        t0 = time.time()
        for a, b in tasks:
            net = a['net']
            if PLANES_ONLY and not (net in PLANE or prio(net) <= 0 or net == '+5V'):
                continue
            if 'CN301' in a['desc'] + b['desc']:
                continue          # pre-existing: the SMA pad and the B.Cu track under it were never joined
            A = (a['x'], a['y'], a['layers'])
            B = (b['x'], b['y'], b['layers'])
            d = math.dist(A[:2], B[:2])
            ok = False
            if 'In2.Cu' in a['desc'] or 'In2.Cu' in b['desc'] or 'Zone' in (a['kind'], b['kind']):
                # one side lives on an inner layer / pour: drop a via next to the outer-layer item
                for it2 in (a, b):
                    if 'In2.Cu' in it2['desc'] or it2['kind'] == 'Zone':
                        continue
                    if net == '+5V':
                        ok = attempt(r, net, (it2['x'], it2['y'], it2['layers']), (162.2, 164.2, ['F.Cu', 'B.Cu']))
                    elif len(it2['layers']) == 1:
                        ok = r.stub_via(net, it2['x'], it2['y'], it2['layers'][0])
            elif net in PLANE:
                if d < 4.0:
                    ok = attempt(r, net, A, B, via_cost=0.6)
                if not ok:
                    for it2 in (a, b):
                        if it2['kind'] == 'Pad' and len(it2['layers']) == 1:
                            ok = r.stub_via(net, it2['x'], it2['y'], it2['layers'][0]) or ok
            else:
                ok = attempt(r, net, A, B)
                if not ok and it < RIP_PASSES:
                    hit = r.route(net, A, B, margin=30.0, max_nodes=6_000_000, soft=True, inner=slow(net))
                    if hit is not False and hit:
                        hit = {h for h in hit if ripcount[h] < 2 and h not in PROT}
                        if hit:
                            for h in hit:
                                ripcount[h] += 1
                            r = rip(path, r, hit)
                            ok = attempt(r, net, A, B)
                            print(f'   rip-up for {net.split("/")[-1]}: {sorted(h.split("/")[-1] for h in hit)} -> {"ok" if ok else "still failing"}')
                            if ok:
                                PROT.add(net)
            if ok:
                done += 1
            else:
                fail += 1
                failed.append((net, round(d, 1), a['desc'][:40], b['desc'][:40]))
        r.save()
        print(f'routed {done}, failed {fail}, {time.time() - t0:.0f} s')
        for f in failed[:40]:
            print('   FAIL', f)
    txt = R.run_drc(path, path.replace('.kicad_pcb', '_drc_final.rpt'))
    blocks = re.split(r'\n(?=\[)', txt)
    c = collections.Counter(b.split(']')[0][1:] for b in blocks if b.startswith('['))
    print({k: v for k, v in c.items() if k not in ('silk_overlap', 'silk_over_copper', 'lib_footprint_issues', 'silk_edge_clearance')})


if __name__ == '__main__':
    main()

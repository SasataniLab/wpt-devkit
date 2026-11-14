#!/usr/bin/env python3
"""Transient of the switch-node sense path of the STM32 TX board, revision 4.

    switch node -- Rtop || Ctop --+-- Rs -- line0 --+-- line1 -- MCU pin (PA1 / PC1)
                                  |                 +-- line2 -- test pad + comparator input (TLV3601)
                           Rbot || Cbot
                                  |
                                 GND

The lines are LC ladders (2 mm per section), solved by modified nodal analysis with trapezoidal integration.
For every case the script prints how much later the comparator input crosses 15 / 50 / 85 % of the swing than an ideal
1 : 16 divider would, and the highest voltage at the MCU pin (limit of PA1 / PC1: VDD + 0.3 V).

Values of the board: Rtop 15 k (R339 / R341), Ctop 3.3 pF (C338 / C339), Rbot 1 k (R340 / R342), Cbot 36 pF (C340 / C341),
Rs 100 ohm (R343 / R344). Lengths from the layout (tools/layout/netpath.py):
    leg A   R343 -> junction 14.3 mm, junction -> PA1 20.5 mm, junction -> U308 47.6 mm, 5 vias and 2 pads
    leg B   R344 -> junction  1.6 mm, junction -> PC1 21.9 mm, junction -> U309 34.5 mm, 3 vias and 2 pads
Track 0.2 mm wide over a plane at 0.20 mm (about 75 ohm, 0.08 pF/mm) or 0.11 mm (about 55 ohm, 0.11 pF/mm).

usage: sense_tap_sim.py            the table of docs/stm32-tx/hrtim_timing_control.md, section 7.9
       sense_tap_sim.py --old      the same for the values of revision 3 (0.5 pF, no Cbot, lines connected to the tap)
"""
import sys

import numpy as np

F = 6.78e6
LEGS = {'A': dict(len0=14.3e-3, len1=20.5e-3, len2=47.6e-3, c_end=1.5e-12),
        'B': dict(len0=1.6e-3, len1=21.9e-3, len2=34.5e-3, c_end=0.9e-12)}
STACKS = {'0.20 mm': dict(z0=75.0, v=3e8 / 1.82), '0.11 mm': dict(z0=55.0, v=3e8 / 1.80)}
BASE = dict(rtop=15e3, rbot=1e3, ctop=3.3e-12, cbot=36e-12, rs=100.0, c_pin=5e-12, c_cmp=1.3e-12)


def network(p):
    """lists of (node a, node b, value) for R, C, L; node -1 is ground"""
    nodes = {}

    def n(name):
        if name == 'gnd':
            return -1
        return nodes.setdefault(name, len(nodes))
    R, C, L = [], [], []
    R.append((n('sw'), n('tap'), p['rtop']))
    C.append((n('sw'), n('tap'), p['ctop'] + 0.07e-12))            # 0.07 pF: the 0402 resistor itself
    R.append((n('tap'), -1, p['rbot']))
    C.append((n('tap'), -1, p['cbot'] + 0.5e-12))                  # 0.5 pF: pads and 4.6 mm of copper on the tap
    R.append((n('tap'), n('N'), max(p['rs'], 1e-3)))
    C.append((n('N'), -1, 0.2e-12))

    def line(a, b, length, tag):
        k = max(3, int(length / 2e-3))
        lt, ct = p['z0'] * length / p['v'], length / (p['z0'] * p['v'])
        prev = a
        for i in range(k):
            mid = b if i == k - 1 else '%s%d' % (tag, i)
            L.append((n(prev), n(mid), lt / k))
            R.append((n(prev), n(mid), 1e9))
            C.append((n(mid), -1, ct / k))
            prev = mid
    line('N', 'J', p['len0'], 'z')
    line('J', 'mcu', p['len1'], 'a')
    C.append((n('mcu'), -1, p['c_pin']))
    line('J', 'cmp', p['len2'], 'b')
    C.append((n('cmp'), -1, p['c_cmp'] + p['c_end']))
    return nodes, R, C, L


def transient(p, vsw, dt):
    nodes, R, C, L = network(p)
    nn, nl, src = len(nodes), len(L), nodes['sw']
    G = np.zeros((nn + nl, nn + nl))
    K = np.zeros((nn + nl, nn + nl))
    for a, b, v in R:
        g = 1.0 / v
        if a >= 0:
            G[a, a] += g
        if b >= 0:
            G[b, b] += g
        if a >= 0 and b >= 0:
            G[a, b] -= g
            G[b, a] -= g
    for a, b, v in C:
        if a >= 0:
            K[a, a] += v
        if b >= 0:
            K[b, b] += v
        if a >= 0 and b >= 0:
            K[a, b] -= v
            K[b, a] -= v
    for i, (a, b, v) in enumerate(L):
        j = nn + i
        if a >= 0:
            G[a, j] += 1
            G[j, a] += 1
        if b >= 0:
            G[b, j] -= 1
            G[j, b] -= 1
        K[j, j] -= v
    A, B = K / dt + G / 2, K / dt - G / 2
    keep = [i for i in range(nn + nl) if i != src]
    ainv = np.linalg.inv(A[np.ix_(keep, keep)])
    a_s, b_k, b_s = A[keep, src], B[np.ix_(keep, keep)], B[keep, src]
    x = np.zeros(len(keep))
    out = {k: np.zeros(len(vsw)) for k in ('tap', 'mcu', 'cmp')}
    idx = {k: keep.index(nodes[k]) for k in out}
    for i in range(1, len(vsw)):
        x = ainv @ (b_k @ x + b_s * vsw[i - 1] - a_s * vsw[i])
        for k in out:
            out[k][i] = x[idx[k]]
    return out


def switch_node(t, v, t_tr, ring=0.0, hard=0.0, f_ring=450e6, tau=4e-9):
    """trapezoid with raised-cosine edges of length t_tr; `hard` = part of the edge that the FET closes abruptly,
    followed by ringing of amplitude ring * v"""
    per, half = 1 / F, 0.5 / F
    out = np.zeros_like(t)
    for i, ti in enumerate(t):
        ph = ti % per
        x = ph if ph < half else ph - half
        y = x / t_tr
        if y >= 1 or (hard > 0 and y > 1 - hard):
            e = 1.0
        else:
            e = 0.5 - 0.5 * np.cos(np.pi * y)
        x0 = x - t_tr * (1 - hard)
        r = ring * v * np.exp(-x0 / tau) * np.sin(2 * np.pi * f_ring * x0) if (ring > 0 and x0 > 0) else 0.0
        out[i] = v * e + r if ph < half else v * (1 - e) - r
    return out


def crossing(t, y, level):
    for i in range(1, len(t)):
        if y[i - 1] < level <= y[i]:
            return t[i - 1] + (level - y[i - 1]) / (y[i] - y[i - 1]) * (t[i] - t[i - 1])
    return float('nan')


def main():
    old = '--old' in sys.argv
    dt = 20e-12
    t = np.arange(0, 3 / F, dt)
    sel = t > 2 / F - 5e-9                                         # the rising edge of the third period
    for v, t_tr, ring, hard in ((24.0, 9.3e-9, 0.0, 0.0), (24.0, 18e-9, 0.0, 0.0), (36.0, 8.3e-9, 0.2, 0.5)):
        vsw = switch_node(t, v, t_tr, ring, hard)
        print('VPP %g V, transition %.1f ns, hard-switched part %g, ringing %g' % (v, t_tr * 1e9, hard, ring))
        for cbot in ((0.0,) if old else (33e-12, 36e-12, 39e-12)):
            for sname, stack in STACKS.items():
                cells = []
                for leg, lp in LEGS.items():
                    p = dict(BASE, **lp, **stack, cbot=cbot)
                    if old:
                        p.update(ctop=0.5e-12, rs=0.0)
                    o = transient(p, vsw, dt)
                    lag = [(crossing(t[sel], o['cmp'][sel], k * v / 16) - crossing(t[sel], vsw[sel] / 16, k * v / 16)) * 1e9 for k in (0.15, 0.5, 0.85)]
                    cells.append('leg %s %.2f / %.2f / %.2f ns, MCU pin %.2f V' % (leg, lag[0], lag[1], lag[2], o['mcu'][sel].max()))
                print('   Cbot %2.0f pF, plane at %s:  %s' % (cbot * 1e12, sname, '   '.join(cells)))


if __name__ == '__main__':
    main()

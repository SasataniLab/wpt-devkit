#!/usr/bin/env python3
"""Step response of the switch-node divider of the STM32 TX board, revision 7 (lumped line model, 20 sections).

    switch node -- R1 || C1 -- Rs --------- line ---------+-- comparator input (TLV3601, about 2 pF with its pads)
                 (15 k, 3.3 pF) (100)                     |
                                                      R2 || C2      (1 k, 47 pF: at the comparator, on its ground)
                                                          |
                                                         GND

 new : this arrangement. Lengths from the layout (tools/layout/lencheck.py): leg A 19.2 mm plus a branch of 3 mm to the
       test pad TP301, leg B 10.8 mm with the test pad TP302 on it. Pad, via and branch are counted as 1 pF at the far end.
 old : revisions 4 to 6: R2 || C2 at the half bridge, then Rs, then 80 / 55 mm of line to comparator, MCU pin and pad.
 bare: as new but Rs = 0 (shows why the resistor stays at the source end).
Edge: 0 -> 40 V in 2 ns and in 5 ns. Printed: lag of the 50 % crossing against an ideal 1 : 16 divider, overshoot,
level after 25 ns. Per mm of line: 0.35 nH, 0.085 pF (0.2 mm track over a plane 0.2 mm away).

usage: sense_line_sim.py        (the table of docs/stm32-tx/hrtim_timing_control.md, section 7.11)
"""
import numpy as np
def run(kind, length_mm, tr=2e-9, Rs=100.0, C2=None, Cload=2e-12, vg=0.0, T=30e-9, dt=1e-12):
    R1, C1, R2 = 15e3, 3.3e-12, 1e3
    n = 20; Lt, Ct = 0.35e-9 * length_mm, 0.085e-12 * length_mm     # per mm: 0.35 nH, 0.085 pF (0.2 mm track over a plane 0.2 mm away)
    L, C = Lt / n, Ct / n
    v = np.zeros(n + 1); i = np.zeros(n)      # node voltages along the line, inductor currents
    vt = 0.0                                   # tap voltage at the source side (old) / node before Rs (new)
    out = []
    for k in range(int(T / dt)):
        t = k * dt
        vs = 40.0 * min(1.0, t / tr); dvs = 40.0 / tr if t < tr else 0.0
        if kind == 'old':
            # source tap: C1 from vs, C2 to ground, Rs to line node 0
            Csum = C1 + C2
            ir = (vs - vt) / R1 - vt / R2 - (vt - v[0]) / Rs
            vt += dt * (ir + C1 * dvs) / Csum
            v[0] += dt * ((vt - v[0]) / Rs - i[0]) / (C + 0.5e-12)
            v[-1] += dt * (i[-1]) / (C + Cload)
        else:
            # node vt between (R1||C1) and Rs; small stray 0.3 pF there
            cs = 0.3e-12
            if Rs > 0:
                ir = (vs - vt) / R1 - (vt - v[0]) / Rs
                vt += dt * (ir + C1 * dvs) / (C1 + cs)
                v[0] += dt * ((vt - v[0]) / Rs - i[0]) / (C + 0.2e-12)
            else:
                ir = (vs - v[0]) / R1
                v[0] += dt * (ir + C1 * dvs - i[0]) / (C1 + C + cs)
                vt = v[0]
            # far end: R2 || C2 to the comparator ground, which sits vg above the source ground
            v[-1] += dt * (i[-1] - (v[-1] - vg) / R2) / (C + C2 + Cload)
        for j in range(1, n):
            v[j] += dt * (i[j - 1] - i[j]) / C
        i += dt * (v[:-1] - v[1:]) / L
        out.append(v[-1] - vg)
    return np.array(out), dt
def lag(y, dt, tr=2e-9):
    fin = 40.0 / 16.0
    k = np.argmax(y >= 0.5 * fin); t50 = k * dt
    return (t50 - 0.5 * tr) * 1e9, (y.max() / fin - 1) * 100, y[int(25e-9 / dt)] / fin
for name, kind, length, kw in (
        ('new, leg A: 19.2 mm, 47 pF     ', 'new', 19.2, dict(C2=47e-12, Cload=3e-12)),
        ('new, leg B: 10.8 mm, 47 pF     ', 'new', 10.8, dict(C2=47e-12, Cload=3e-12)),
        ('new, leg A with 43 pF          ', 'new', 19.2, dict(C2=43e-12, Cload=3e-12)),
        ('new, leg A with 51 pF          ', 'new', 19.2, dict(C2=51e-12, Cload=3e-12)),
        ('old, 80 mm (leg A, revision 6) ', 'old', 80, dict(C2=36e-12, Cload=7.5e-12)),
        ('old, 55 mm (leg B, revision 6) ', 'old', 55, dict(C2=36e-12, Cload=7.5e-12)),
        ('bare, 19.2 mm, no resistor     ', 'new', 19.2, dict(C2=47e-12, Cload=3e-12, Rs=0.0))):
    y, dt = run(kind, length, **kw)
    l, ov, lvl = lag(y, dt)
    y5, _ = run(kind, length, tr=5e-9, **kw); l5, ov5, _ = lag(y5, dt, 5e-9)
    print('%s lag %+.2f ns, overshoot %+5.1f %%, level at 25 ns %.3f | 5 ns edge: lag %+.2f ns, overshoot %+5.1f %%' % (name, l, ov, lvl, l5, ov5))

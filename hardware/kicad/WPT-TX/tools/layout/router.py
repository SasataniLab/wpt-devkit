#!/usr/bin/env python3
"""Small clearance-aware grid router for KiCad boards (F.Cu/B.Cu signals, through vias).

The board is rasterised at 0.05 mm. For the net being routed, every piece of copper of
another net is an obstacle; a track centre must stay (clearance + half width) away from it,
a via centre (clearance + via radius) away on every layer it crosses.
"""
import heapq
import json
import math
import re
import subprocess
import sys

import numpy as np
import pcbnew
from PIL import Image, ImageDraw
from scipy import ndimage

MM = 1e6
RES = 0.05                      # mm per cell
X0, Y0, X1, Y1 = 149.0, 134.0, 221.0, 201.0
W = int(round((X1 - X0) / RES))
H = int(round((Y1 - Y0) / RES))
CLR = 0.2
VIA_D, VIA_DRILL = 0.6, 0.3
EDGE_CLR = 0.3
SIGNAL_LAYERS = ('F.Cu', 'B.Cu')
FORBID = 65535
# Where a slow signal may borrow the inner power layer: the user-interface area west of the MCU only.
# The plane under the MCU, the crystal and the whole power stage stay untouched.
INNER_BOXES = ((151.0, 143.2, 176.0, 163.2), (151.0, 163.2, 158.4, 168.0))
DEFAULT_CORRIDORS = ('U2',)      # fine-pitch parts that get an escape lane reserved in front of every pad


def V(x, y):
    return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))


EPS = 0.01                      # shapes are shrunk by this much so that edge-on cells count as outside


def px(x, y):
    return (x - X0) / RES + 0.5, (y - Y0) / RES + 0.5


class Canvas:
    """Owner maps (net id per cell) for the layers that matter."""

    def __init__(self):
        self.img = {l: Image.new('I;16', (W, H), 0) for l in ('F.Cu', 'B.Cu', 'In2.Cu')}
        self.drw = {l: ImageDraw.Draw(im) for l, im in self.img.items()}
        self.soft = {l: Image.new('I;16', (W, H), 0) for l in ('F.Cu', 'B.Cu', 'In2.Cu')}   # copper this router added
        self.sdrw = {l: ImageDraw.Draw(im) for l, im in self.soft.items()}
        self.pads = {l: Image.new('L', (W, H), 0) for l in ('F.Cu', 'B.Cu')}   # SMD pad areas (any net)
        self.pdrw = {l: ImageDraw.Draw(im) for l, im in self.pads.items()}
        self.holes = Image.new('L', (W, H), 0)
        self.hdrw = ImageDraw.Draw(self.holes)
        self._np = {}

    def invalidate(self):
        self._np = {}

    def arr(self, layer):
        if layer not in self._np:
            self._np[layer] = np.array(self.img[layer], dtype=np.uint16)
        return self._np[layer]

    def poly(self, layer, pts, nid, soft=False):
        self.drw[layer].polygon([px(*p) for p in pts], fill=nid)
        if soft:
            self.sdrw[layer].polygon([px(*p) for p in pts], fill=nid)
        self.invalidate()

    def sarr(self, layer):
        k = 'soft:' + layer
        if k not in self._np:
            self._np[k] = np.array(self.soft[layer], dtype=np.uint16)
        return self._np[k]

    def disk(self, layer, c, r, nid, soft=False):
        r = max(r - EPS, 0.01)
        pts = [(c[0] + r * math.cos(k * math.pi / 12), c[1] + r * math.sin(k * math.pi / 12)) for k in range(24)]
        self.poly(layer, pts, nid, soft)

    def seg(self, layer, a, b, w, nid, soft=False):
        L = math.dist(a, b)
        if L > 1e-6:
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            hw = max(w / 2 - EPS, 0.01)
            nx, ny = -uy * hw, ux * hw
            self.poly(layer, [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)], nid, soft)
        self.disk(layer, a, w / 2, nid, soft)
        self.disk(layer, b, w / 2, nid, soft)


def rot_rect(cx, cy, w, h, deg):
    a = math.radians(-deg)
    out = []
    for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        out.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    return out


class Router:
    def __init__(self, board_path, reg=None, protected=None, corridors=None):
        corridors = DEFAULT_CORRIDORS if corridors is None else corridors
        self.path = board_path
        self.board = pcbnew.LoadBoard(board_path)
        b = self.board
        self.lid = {b.GetLayerName(i): i for i in b.GetEnabledLayers().Seq()}
        self.nets = {}
        self.cv = Canvas()
        self.added = []
        self.own_vias = {}                                 # net -> via centres already on the board
        self.reg = reg if reg is not None else {}          # net -> list of keys of copper this router added
        self.protected = protected if protected is not None else set()
        self._softkeys = {k: n for n, ks in self.reg.items() if n not in self.protected for k in ks}
        self._rasterise()
        for ref in corridors:
            self._corridors(ref)

    @staticmethod
    def tkey(net, layer, a, b):
        p, q = sorted([(round(a[0], 3), round(a[1], 3)), (round(b[0], 3), round(b[1], 3))])
        return ('T', net, layer, p, q)

    @staticmethod
    def vkey(net, c):
        return ('V', net, (round(c[0], 3), round(c[1], 3)))

    def _corridors(self, ref, out_len=0.9, in_len=0.9):
        """Reserve an escape lane in front of and behind every signal pad of a fine-pitch part (canvas only)."""
        fp = self.board.FindFootprintByReference(ref)
        if fp is None:
            return
        cx, cy = fp.GetPosition().x / MM, fp.GetPosition().y / MM
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net or net.startswith('unconnected'):
                continue
            x, y = pad.GetPosition().x / MM, pad.GetPosition().y / MM
            dx, dy = x - cx, y - cy
            if abs(dx) > abs(dy):
                ux, uy = (1 if dx > 0 else -1), 0
            else:
                ux, uy = 0, (1 if dy > 0 else -1)
            half = max(pad.GetSize(pcbnew.F_Cu).x, pad.GetSize(pcbnew.F_Cu).y) / MM / 2
            a = (x - ux * (half + in_len), y - uy * (half + in_len))
            b = (x + ux * (half + out_len), y + uy * (half + out_len))
            self.cv.seg('F.Cu', a, b, 0.2, self.nid(net))

    # -------------------------------------------------------------- net ids
    def nid(self, name):
        if name == '':
            return FORBID
        if name not in self.nets:
            self.nets[name] = len(self.nets) + 1
        return self.nets[name]

    # -------------------------------------------------------------- rasterise
    def _rasterise(self):
        b, cv = self.board, self.cv
        # board edge margin
        for l in cv.img:
            m = EDGE_CLR
            cv.drw[l].rectangle([0, 0, W, H], fill=FORBID)
            cv.drw[l].rectangle([*px(150.0 + m + 0.05, 135.0 + m + 0.05), *px(220.0 - m - 0.1, 200.0 - m - 0.1)], fill=0)
        # zones with a net other than GND on outer layers, and keep-outs
        for z in b.Zones():
            for li in z.GetLayerSet().Seq():
                ln = b.GetLayerName(li)
                if ln not in SIGNAL_LAYERS:
                    continue
                if z.GetIsRuleArea():
                    if not z.GetDoNotAllowTracks():
                        continue
                    nid = FORBID
                elif z.GetNetname() == 'GND':
                    continue
                else:
                    nid = self.nid(z.GetNetname())
                o = z.Outline()
                for i in range(o.OutlineCount()):
                    c = o.Outline(i)
                    cv.poly(ln, [(c.CPoint(k).x / MM, c.CPoint(k).y / MM) for k in range(c.PointCount())], nid)
        # pads
        for fp in b.GetFootprints():
            for pad in fp.Pads():
                self._pad(pad)
        # tracks / vias
        for t in b.GetTracks():
            self._track(t)
        cv.invalidate()

    def _pad(self, pad):
        b, cv = self.board, self.cv
        nid = self.nid(pad.GetNetname())
        c = (pad.GetPosition().x / MM, pad.GetPosition().y / MM)
        sz = pad.GetSize(pcbnew.F_Cu)
        w, h = sz.x / MM, sz.y / MM
        rot = pad.GetOrientationDegrees()
        attr = pad.GetAttribute()
        layers = [b.GetLayerName(i) for i in pad.GetLayerSet().Seq() if b.GetLayerName(i).endswith('.Cu')]
        drill = pad.GetDrillSize().x / MM
        if attr == pcbnew.PAD_ATTRIB_NPTH:
            r = max(drill, pad.GetDrillSize().y / MM) / 2
            for l in cv.img:
                cv.disk(l, c, r + 0.05, FORBID)
            cv.hdrw.ellipse([*px(c[0] - r, c[1] - r), *px(c[0] + r, c[1] + r)], fill=255)
            return
        if not layers:
            return
        for l in (cv.img if drill > 0 else layers):
            if l not in cv.img:
                continue
            if pad.GetShape(pcbnew.F_Cu) == pcbnew.PAD_SHAPE_CIRCLE:
                cv.disk(l, c, w / 2, nid)
            else:
                cv.poly(l, rot_rect(c[0], c[1], w - 2 * EPS, h - 2 * EPS, rot), nid)
        if drill > 0:
            cv.hdrw.ellipse([*px(c[0] - drill / 2, c[1] - drill / 2), *px(c[0] + drill / 2, c[1] + drill / 2)], fill=255)
        else:
            for l in layers:
                if l in cv.pads:
                    cv.pdrw[l].polygon([px(*p) for p in rot_rect(c[0], c[1], w, h, rot)], fill=255)

    def _track(self, t):
        b, cv = self.board, self.cv
        net = t.GetNetname()
        nid = self.nid(net)
        if t.GetClass() == 'PCB_VIA':
            c = (t.GetPosition().x / MM, t.GetPosition().y / MM)
            self.own_vias.setdefault(net, []).append(c)
            soft = self.vkey(net, c) in self._softkeys
            for l in cv.img:
                cv.disk(l, c, t.GetWidth(pcbnew.F_Cu) / MM / 2, nid, soft)
            d = t.GetDrillValue() / MM
            cv.hdrw.ellipse([*px(c[0] - d / 2, c[1] - d / 2), *px(c[0] + d / 2, c[1] + d / 2)], fill=255)
        else:
            ln = b.GetLayerName(t.GetLayer())
            if ln in cv.img:
                a = (t.GetStart().x / MM, t.GetStart().y / MM)
                e = (t.GetEnd().x / MM, t.GetEnd().y / MM)
                cv.seg(ln, a, e, t.GetWidth() / MM, nid, self.tkey(net, ln, a, e) in self._softkeys)

    # -------------------------------------------------------------- adding copper
    def add_track(self, net, layer, a, b, w=0.2):
        if math.dist(a, b) < 1e-4:
            return
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(V(*a))
        t.SetEnd(V(*b))
        t.SetWidth(int(round(w * MM)))
        t.SetLayer(self.lid[layer])
        t.SetNet(self.board.FindNet(net))
        self.board.Add(t)
        self.added.append(t)
        soft = not getattr(self, '_fixed', False)
        if soft:
            self.reg.setdefault(net, []).append(self.tkey(net, layer, a, b))
        if layer in self.cv.img:
            self.cv.seg(layer, a, b, w, self.nid(net), soft and net not in self.protected)

    def add_via(self, net, c):
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(V(*c))
        v.SetWidth(int(VIA_D * MM))
        v.SetDrill(int(VIA_DRILL * MM))
        v.SetLayerPair(self.lid['F.Cu'], self.lid['B.Cu'])
        v.SetNet(self.board.FindNet(net))
        self.board.Add(v)
        self.added.append(v)
        self.own_vias.setdefault(net, []).append(tuple(c))
        soft = not getattr(self, '_fixed', False)
        if soft:
            self.reg.setdefault(net, []).append(self.vkey(net, c))
        for l in self.cv.img:
            self.cv.disk(l, c, VIA_D / 2, self.nid(net), soft and net not in self.protected)
        self.cv.hdrw.ellipse([*px(c[0] - VIA_DRILL / 2, c[1] - VIA_DRILL / 2), *px(c[0] + VIA_DRILL / 2, c[1] + VIA_DRILL / 2)], fill=255)

    def save(self, path=None):
        pcbnew.SaveBoard(path or self.path, self.board)

    # -------------------------------------------------------------- free-space maps
    def maps(self, net, win, width=0.2, soft=False):
        """Return (free[layer], via_ok, own[layer]) boolean arrays for a window (ix0, iy0, ix1, iy1)."""
        ix0, iy0, ix1, iy1 = win
        P = 24                                     # 1.2 mm of context around the window
        jx0, jy0, jx1, jy1 = max(0, ix0 - P), max(0, iy0 - P), min(W, ix1 + P), min(H, iy1 + P)
        cs = (slice(iy0 - jy0, iy0 - jy0 + (iy1 - iy0)), slice(ix0 - jx0, ix0 - jx0 + (ix1 - ix0)))
        n = self.nid(net)
        free, own = {}, {}
        dist = {}

        def edt(mask):
            if not mask.any():
                return np.full(mask.shape, 1e6)
            return ndimage.distance_transform_edt(~mask) * RES

        self._softinfo = {}
        for l in ('F.Cu', 'B.Cu', 'In2.Cu'):
            a = self.cv.arr(l)[jy0:jy1, jx0:jx1]
            other = (a != 0) & (a != n)
            if soft:
                sa = self.cv.sarr(l)[jy0:jy1, jx0:jx1]
                smask = (sa != 0) & (sa != n)
                other = other & ~smask
                if smask.any():
                    d, idx = ndimage.distance_transform_edt(~smask, return_indices=True)
                    self._softinfo[l] = (d[cs] * RES, sa[idx[0], idx[1]][cs])
                else:
                    self._softinfo[l] = None
            dist[l] = edt(other)[cs]
            if True:
                free[l] = dist[l] >= (CLR + width / 2 + RES + 0.02)
                mine = a == n
                # own copper may be re-used only where a track of this width stays inside it
                core = ndimage.distance_transform_edt(mine) * RES >= (width / 2 - 1e-6) if mine.any() else mine
                own[l] = core[cs]
        need = CLR + VIA_D / 2 + RES + 0.02
        via_ok = (dist['F.Cu'] >= need) & (dist['B.Cu'] >= need) & (dist['In2.Cu'] >= need)
        # keep vias off SMD pads (any net) and away from other holes
        for l in SIGNAL_LAYERS:
            p = np.array(self.cv.pads[l], dtype=np.uint8)[jy0:jy1, jx0:jx1] > 0
            via_ok &= edt(p)[cs] >= (VIA_D / 2 + 0.1 + RES)
        hl = np.array(self.cv.holes, dtype=np.uint8)[jy0:jy1, jx0:jx1] > 0
        via_ok &= edt(hl)[cs] >= (VIA_DRILL / 2 + 0.25 + RES)
        return free, via_ok, own

    # -------------------------------------------------------------- A*
    def route(self, net, a, b, width=0.2, via_cost=3.0, margin=6.0, layers_pref=None, allow_via=True, max_nodes=3_000_000,
              penal=None, soft=False, soft_cost=25.0, inner=False):
        """a, b: (x, y, [layers]). Returns True when a connection was added."""
        (ax, ay, al), (bx, by, bl) = a, b
        wx0, wy0 = min(ax, bx) - margin, min(ay, by) - margin
        wx1, wy1 = max(ax, bx) + margin, max(ay, by) + margin
        ix0, iy0 = max(0, int((wx0 - X0) / RES)), max(0, int((wy0 - Y0) / RES))
        ix1, iy1 = min(W, int((wx1 - X0) / RES) + 1), min(H, int((wy1 - Y0) / RES) + 1)
        free, via_ok, own = self.maps(net, (ix0, iy0, ix1, iy1), width, soft=soft)
        if not allow_via:
            via_ok = np.zeros_like(via_ok)
        hh, ww = via_ok.shape
        L = list(SIGNAL_LAYERS) + (['In2.Cu'] if inner else [])
        self._L = L
        ok = [free[l] | own[l] for l in L]
        if inner:
            gy, gx = np.mgrid[0:hh, 0:ww]
            wxx, wyy = X0 + (gx + ix0) * RES, Y0 + (gy + iy0) * RES
            allowed = np.zeros((hh, ww), dtype=bool)
            for bx0, by0, bx1, by1 in INNER_BOXES:
                allowed |= (wxx >= bx0) & (wxx <= bx1) & (wyy >= by0) & (wyy <= by1)
            k = L.index('In2.Cu')
            ok[k] = ok[k] & allowed
        extra = None
        vextra = None
        need_t = CLR + width / 2 + RES + 0.02
        need_v = CLR + VIA_D / 2 + RES + 0.02
        if soft:
            # copper added by this router is passable at a price; the caller rips it up afterwards
            pc = soft_cost / RES
            fac = np.ones(max(self.nets.values()) + 2)
            for nm, f in getattr(self, 'softfac', {}).items():
                if nm in self.nets:
                    fac[self.nets[nm]] = f
            extra = []
            vextra = np.zeros((hh, ww))
            for l in L:
                info = self._softinfo.get(l)
                extra.append(np.where(info[0] < need_t, pc * fac[np.minimum(info[1], len(fac) - 1)], 0.0) if info is not None else np.zeros((hh, ww)))
            for l in ('F.Cu', 'B.Cu', 'In2.Cu'):
                info = self._softinfo.get(l)
                if info is not None:
                    vextra = np.maximum(vextra, np.where(info[0] < need_v, pc * fac[np.minimum(info[1], len(fac) - 1)], 0.0))
            if penal is not None:
                pe = penal(ix0, iy0, ix1, iy1)
                extra = [e + p for e, p in zip(extra, pe)]
        elif penal is not None:
            extra = penal(ix0, iy0, ix1, iy1)

        def cell(x, y):
            return int(round((x - X0) / RES)) - ix0, int(round((y - Y0) / RES)) - iy0

        # a via of this net that is already there may be used to change layer (no new via is added)
        ownvia = np.zeros((hh, ww), dtype=bool)
        for vx, vy in self.own_vias.get(net, []):
            cx, cy = cell(vx, vy)
            if 0 <= cy < hh and 0 <= cx < ww:
                ownvia[cy, cx] = True
        self._ownvia = ownvia

        def seeds(x, y, layers):
            cx, cy = cell(x, y)
            out = []
            for li, l in enumerate(L):
                if l not in layers:
                    continue
                # own-net cells around the anchor (pad interior / track end)
                r = 4
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        yy, xx = cy + dy, cx + dx
                        if 0 <= yy < hh and 0 <= xx < ww and own[l][yy, xx] and dx * dx + dy * dy <= r * r:
                            out.append((li, yy, xx))
                if not out and 0 <= cy < hh and 0 <= cx < ww:
                    out.append((li, cy, cx))
            return out

        src = seeds(ax, ay, al)
        dst = set(seeds(bx, by, bl))
        if not src or not dst:
            return False
        tcx, tcy = cell(bx, by)
        INF = 1e18
        g = [np.full((hh, ww), INF, dtype=np.float64) for _ in L]
        par = {}
        pq = []
        for s in src:
            g[s[0]][s[1], s[2]] = 0.0
            heapq.heappush(pq, (0.0, 0.0, s))
        D1, D2 = 1.0, math.sqrt(2)
        vc = via_cost / RES
        lp = [(1.7 if l == 'In2.Cu' else 1.0) if (layers_pref is None or l in layers_pref) else 2.5 for l in L]
        found = None
        n = 0
        while pq:
            f, gc, cur = heapq.heappop(pq)
            li, y, x = cur
            if gc > g[li][y, x]:
                continue
            if cur in dst:
                found = cur
                break
            n += 1
            if n > max_nodes:
                break
            okl = ok[li]
            for dy, dx, c in ((0, 1, D1), (0, -1, D1), (1, 0, D1), (-1, 0, D1), (1, 1, D2), (1, -1, D2), (-1, 1, D2), (-1, -1, D2)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < hh and 0 <= xx < ww and okl[yy, xx]:
                    ng = gc + c * lp[li] + (extra[li][yy, xx] if extra is not None else 0.0)
                    if ng < g[li][yy, xx]:
                        g[li][yy, xx] = ng
                        par[(li, yy, xx)] = cur
                        ddx, ddy = abs(xx - tcx), abs(yy - tcy)
                        heapq.heappush(pq, (ng + (max(ddx, ddy) + 0.4142 * min(ddx, ddy)), ng, (li, yy, xx)))
            ov = ownvia[y, x]
            if via_ok[y, x] or ov:
                for lj in range(len(L)):
                    if lj == li or not (ok[lj][y, x] or ov):
                        continue
                    ng = gc + (6.0 if ov else vc + (vextra[y, x] if vextra is not None else 0.0))
                    if ng < g[lj][y, x]:
                        g[lj][y, x] = ng
                        par[(lj, y, x)] = cur
                        ddx, ddy = abs(x - tcx), abs(y - tcy)
                        heapq.heappush(pq, (ng + (max(ddx, ddy) + 0.4142 * min(ddx, ddy)), ng, (lj, y, x)))
        if found is None:
            return False
        # back-trace
        path = [found]
        while path[-1] in par:
            path.append(par[path[-1]])
        path.reverse()
        if soft:
            inv = {v: k for k, v in self.nets.items()}
            hit = set()
            for i, (li, y, x) in enumerate(path):
                info = self._softinfo.get(L[li])
                if info is not None and info[0][y, x] < need_t:
                    hit.add(inv.get(int(info[1][y, x])))
                if i + 1 < len(path) and path[i + 1][0] != li and not ownvia[y, x]:
                    for l in ('F.Cu', 'B.Cu', 'In2.Cu'):
                        info = self._softinfo.get(l)
                        if info is not None and info[0][y, x] < need_v:
                            hit.add(inv.get(int(info[1][y, x])))
            hit.discard(None)
            hit.discard(net)
            return hit
        self._emit(net, path, ix0, iy0, width)
        return True

    def _emit(self, net, path, ix0, iy0, width):
        L = getattr(self, '_L', None) or list(SIGNAL_LAYERS)

        def world(c):
            return (round(X0 + (c[2] + ix0) * RES, 4), round(Y0 + (c[1] + iy0) * RES, 4))

        i = 0
        while i < len(path) - 1:
            li = path[i][0]
            if path[i + 1][0] != li:
                wpt = world(path[i])
                if not any(math.dist(wpt, v) < 0.06 for v in self.own_vias.get(net, [])):
                    self.add_via(net, wpt)
                i += 1
                continue
            j = i + 1
            d = (path[j][1] - path[i][1], path[j][2] - path[i][2])
            while j + 1 < len(path) and path[j + 1][0] == li and (path[j + 1][1] - path[j][1], path[j + 1][2] - path[j][2]) == d:
                j += 1
            self.add_track(net, L[li], world(path[i]), world(path[j]), width)
            i = j

    # -------------------------------------------------------------- plane stubs
    def stub_via(self, net, x, y, layer, width=0.25, max_len=4.0, min_len=0.0, avoid=None):
        """Short track from an SMD pad to a new via (for nets that live on a plane)."""
        m = max_len + 1.0
        ix0, iy0 = max(0, int((x - m - X0) / RES)), max(0, int((y - m - Y0) / RES))
        ix1, iy1 = min(W, int((x + m - X0) / RES) + 1), min(H, int((y + m - Y0) / RES) + 1)
        free, via_ok, own = self.maps(net, (ix0, iy0, ix1, iy1), width)
        ok = free[layer] | own[layer]
        hh, ww = ok.shape
        cx, cy = int(round((x - X0) / RES)) - ix0, int(round((y - Y0) / RES)) - iy0
        if avoid is not None:
            via_ok = via_ok & ~avoid(ix0, iy0, ix1, iy1)
        g = np.full((hh, ww), 1e18)
        par = {}
        pq = []
        r = 3
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                yy, xx = cy + dy, cx + dx
                if 0 <= yy < hh and 0 <= xx < ww and own[layer][yy, xx]:
                    g[yy, xx] = 0
                    heapq.heappush(pq, (0.0, yy, xx))
        if not pq:
            return False
        D2 = math.sqrt(2)
        while pq:
            gc, yy0, xx0 = heapq.heappop(pq)
            if gc > g[yy0, xx0]:
                continue
            if via_ok[yy0, xx0] and gc * RES >= min_len:
                path = [(yy0, xx0)]
                while path[-1] in par:
                    path.append(par[path[-1]])
                path.reverse()
                li = list(SIGNAL_LAYERS).index(layer)
                self._L = list(SIGNAL_LAYERS)
                self._emit(net, [(li, p[0], p[1]) for p in path], ix0, iy0, width)
                self.add_via(net, (round(X0 + (xx0 + ix0) * RES, 4), round(Y0 + (yy0 + iy0) * RES, 4)))
                return True
            if gc * RES > max_len:
                break
            for dy, dx, c in ((0, 1, 1), (0, -1, 1), (1, 0, 1), (-1, 0, 1), (1, 1, D2), (1, -1, D2), (-1, 1, D2), (-1, -1, D2)):
                yy, xx = yy0 + dy, xx0 + dx
                if 0 <= yy < hh and 0 <= xx < ww and ok[yy, xx] and gc + c < g[yy, xx]:
                    g[yy, xx] = gc + c
                    par[(yy, xx)] = (yy0, xx0)
                    heapq.heappush(pq, (gc + c, yy, xx))
        return False


# ------------------------------------------------------------------ DRC helpers
def run_drc(board_path, report, refill=True):
    cmd = ['kicad-cli', 'pcb', 'drc', '--severity-all', '--format', 'report', '-o', report]
    if refill:
        cmd += ['--refill-zones', '--save-board']
    subprocess.run(cmd + [board_path], capture_output=True, text=True)
    return open(report).read()


ITEM = re.compile(r'@\(([\d.]+) mm, ([\d.]+) mm\): (.*)')


def parse_unconnected(text):
    out = []
    blocks = re.split(r'\n(?=\[)', text)
    for b in blocks:
        if not b.startswith('[unconnected_items]'):
            continue
        items = []
        for line in b.split('\n'):
            m = ITEM.search(line)
            if m:
                x, y, desc = float(m.group(1)), float(m.group(2)), m.group(3)
                net = re.search(r'\[([^\]]*)\]', desc)
                layers = ['F.Cu', 'B.Cu']
                ml = re.search(r' on ([FB]\.Cu)', desc)
                if desc.startswith('PTH') or desc.startswith('Via'):
                    layers = ['F.Cu', 'B.Cu']
                elif ml:
                    layers = [ml.group(1)]
                items.append({'x': x, 'y': y, 'desc': desc, 'net': net.group(1) if net else '', 'layers': layers,
                              'kind': desc.split(' ')[0]})
        if len(items) == 2:
            out.append(items)
    return out


if __name__ == '__main__':
    r = Router(sys.argv[1])
    print('nets', len(r.nets))

#!/usr/bin/env python3
"""Helpers for the scripted board edits of revision 4 (mech7.py, mech8.py): footprints of new schematic symbols,
tracks, vias, nets.

A footprint placed by script must carry what "Update PCB from Schematic" would give it, or the parity check of the
DRC complains: the link to its symbol (path), sheet name and file, library id, value, description, and the nets of
its pads. All of that is read from the netlist (`kicad-cli sch export netlist --format kicadsexpr`).
"""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'schematic'))
import sx  # noqa: E402

MM = 1e6
V = lambda x, y: pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
P = lambda v: (round(v.x / MM, 4), round(v.y / MM, 4))
short = lambda n: n.split('/')[-1]
PRJ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
STOCK = '/usr/share/kicad/footprints'


def _kids(n, name):
    return [x for x in n if isinstance(x, list) and x and x[0] == name]


def _val(n, name, default=''):
    k = _kids(n, name)
    return k[0][1] if k and len(k[0]) > 1 else default


def load_netlist(path):
    """ref -> dict(value, footprint, path, sheetname, sheetfile, description, datasheet, pins {number: net})"""
    root = sx.to_plain(sx.parse(open(path, encoding='utf-8').read()))
    comps = {}
    for c in _kids(_kids(root, 'components')[0], 'comp'):
        props = {_val(p, 'name'): _val(p, 'value') for p in _kids(c, 'property')}
        sp = _kids(c, 'sheetpath')[0]
        ts = _kids(c, 'tstamps')[0][1]
        lib = _kids(c, 'libsource')[0]
        comps[_val(c, 'ref')] = {'value': _val(c, 'value'), 'footprint': _val(c, 'footprint'), 'path': _val(sp, 'tstamps') + ts,
                                 'sheetname': props.get('Sheetname', ''), 'sheetfile': props.get('Sheetfile', ''),
                                 'description': _val(lib, 'description') or _val(c, 'description'), 'datasheet': _val(c, 'datasheet'),
                                 'pins': {}}
    for n in _kids(_kids(root, 'nets')[0], 'net'):
        for node in _kids(n, 'node'):
            comps[_val(node, 'ref')]['pins'][_val(node, 'pin')] = _val(n, 'name')
    return comps


def net(board, name):
    """the net with this full name, made if the board does not have it yet"""
    n = board.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
    return n


def full_name(board, shortname):
    hits = [n for n in (str(k) for k in board.GetNetInfo().NetsByName().keys()) if short(n) == shortname]
    assert len(hits) == 1, (shortname, hits)
    return hits[0]


def lib_dir(nick):
    local = os.path.join(PRJ, 'lib', 'footprints', nick + '.pretty')
    return local if os.path.isdir(local) else os.path.join(STOCK, nick + '.pretty')


def place(board, comps, ref, x, y, rot=0.0, side='F', ref_at=None, ref_size=0.8, ref_rot=None, hide_ref=False):
    """Add the footprint of schematic symbol `ref` at (x, y) mm, rotated `rot` degrees, on the front or the back.
    ref_at: position of the reference text relative to the footprint centre (board axes, mm)."""
    c = comps[ref]
    nick, name = c['footprint'].split(':')
    fp = pcbnew.FootprintLoad(lib_dir(nick), name)
    assert fp is not None, c['footprint']
    fp.SetFPIDAsString(c['footprint'])
    fp.SetReference(ref)
    fp.SetValue(c['value'])
    fp.SetPath(pcbnew.KIID_PATH(c['path']))
    fp.SetSheetname(c['sheetname'])
    fp.SetSheetfile(c['sheetfile'])
    board.Add(fp)
    fp.SetPosition(V(x, y))
    if side == 'B':
        fp.Flip(V(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(rot)
    if c['description']:
        fp.SetField('Description', c['description'])
        fp.GetField('Description').SetVisible(False)
    if c['datasheet'] not in ('', '~'):
        fp.GetField('Datasheet').SetText(c['datasheet'])
    for pad in fp.Pads():
        nm = c['pins'].get(pad.GetNumber())
        if nm is not None:
            pad.SetNet(net(board, nm))
    r = fp.Reference()
    r.SetVisible(not hide_ref)
    r.SetTextSize(pcbnew.VECTOR2I(int(ref_size * MM), int(ref_size * MM)))
    r.SetTextThickness(int(0.12 * MM))
    if ref_at is not None:
        r.SetPosition(V(x + ref_at[0], y + ref_at[1]))
    if ref_rot is not None:
        r.SetTextAngleDegrees(ref_rot)
    fp.Value().SetVisible(False)
    return fp


def pads(fp):
    return {p.GetNumber(): P(p.GetPosition()) for p in fp.Pads()}


def seg(board, netname, pts, w=0.2, layer='F.Cu', allow_any_angle=False):
    n = board.FindNet(netname)
    assert n is not None, netname
    for p, q in zip(pts, pts[1:]):
        dx, dy = abs(q[0] - p[0]), abs(q[1] - p[1])
        assert allow_any_angle or dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-3, ('not on 45 degrees', netname, p, q)
        s = pcbnew.PCB_TRACK(board)
        s.SetNet(n)
        s.SetLayer(board.GetLayerID(layer))
        s.SetStart(V(*p))
        s.SetEnd(V(*q))
        s.SetWidth(int(round(w * MM)))
        board.Add(s)


def via(board, netname, c, size=0.6, drill=0.3):
    n = board.FindNet(netname)
    assert n is not None, netname
    v = pcbnew.PCB_VIA(board)
    v.SetNet(n)
    v.SetPosition(V(*c))
    v.SetWidth(pcbnew.F_Cu, int(size * MM))
    v.SetDrill(int(drill * MM))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(v)


def on_line(p, a, e, tol=0.02):
    dx, dy = e[0] - a[0], e[1] - a[1]
    L2 = dx * dx + dy * dy
    u = 0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return ((p[0] - a[0] - u * dx) ** 2 + (p[1] - a[1] - u * dy) ** 2) ** 0.5 < tol


_PENDING = []          # board.Remove() makes later pcbnew.FootprintLoad() calls fail, so removals wait for flush()


def rip(board, netname, layer, poly, expect=None):
    """Mark for removal the track pieces of `netname` on `layer` that lie on the polyline `poly` (see flush)."""
    gone = []
    for t in list(board.GetTracks()):
        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != netname or board.GetLayerName(t.GetLayer()) != layer:
            continue
        if any(t is x for x in _PENDING):
            continue
        a, e = P(t.GetStart()), P(t.GetEnd())
        if any(on_line(a, p, q) and on_line(e, p, q) for p, q in zip(poly, poly[1:])):
            gone.append(t)
    if expect is not None:
        assert len(gone) == expect, (netname, layer, poly, len(gone), expect)
    _PENDING.extend(gone)
    return len(gone)


def rip_via(board, netname, c):
    for t in list(board.GetTracks()):
        if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == netname and P(t.GetPosition()) == (round(c[0], 4), round(c[1], 4)):
            _PENDING.append(t)
            return
    raise AssertionError(('no via', netname, c))


def remove_footprint(board, ref):
    fp = board.FindFootprintByReference(ref)
    assert fp is not None, ref
    _PENDING.append(fp)


def flush(board):
    """Carry out the removals. Call once, after the last place()."""
    n = len(_PENDING)
    for t in _PENDING:
        board.Remove(t)
    del _PENDING[:]
    return n


def rename_tracks(board, old, new, layer=None, box=None):
    """Give the copper of net `old` (optionally only on `layer` and inside box x0, y0, x1, y1) to net `new`."""
    n = net(board, new)
    k = 0
    for t in board.GetTracks():
        if t.GetNetname() != old:
            continue
        if layer is not None and t.Type() != pcbnew.PCB_VIA_T and board.GetLayerName(t.GetLayer()) != layer:
            continue
        pts = [P(t.GetPosition())] if t.Type() == pcbnew.PCB_VIA_T else [P(t.GetStart()), P(t.GetEnd())]
        if box is not None and not all(box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3] for p in pts):
            continue
        t.SetNet(n)
        k += 1
    return k


def text(board, s, x, y, layer='F.SilkS', size=0.8, thick=0.12, rot=0.0, mirror=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetLayer(board.GetLayerID(layer))
    t.SetPosition(V(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(int(size * MM), int(size * MM)))
    t.SetTextThickness(int(thick * MM))
    t.SetTextAngleDegrees(rot)
    t.SetMirrored(mirror)
    board.Add(t)
    return t

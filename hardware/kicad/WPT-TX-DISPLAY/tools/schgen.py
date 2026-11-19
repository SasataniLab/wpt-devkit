#!/usr/bin/env python3
"""Write a KiCad 10 schematic from a script: symbols from the stock or the project libraries, wires, labels.

The schematic of this board is small enough to be written as a list of placed parts and connections (gen_sch.py).
Doing it by script keeps it reproducible and lets the board script read the same netlist. What this module does:

  Sheet(project, title)            a sheet in memory
  sheet.place(lib_id, ref, value, x, y, rot, fields)   -> {pin number: (x, y)} in sheet coordinates
  sheet.wire(p, q, ...)            wire segments along the points (each piece must be horizontal or vertical)
  sheet.label(name, p, rot)        local net label at a wire end or pin end
  sheet.power(lib_id, p)           power symbol (power:GND, power:+3V3, power:PWR_FLAG) with its pin on p
  sheet.nc(p)                      no-connect flag
  sheet.junction(p), sheet.text(s, p)
  sheet.write(path)

Symbols are copied from the library files into the sheet's lib_symbols section, as eeschema does. Only symbols
that do not extend another symbol are supported (a derived symbol would have to be flattened exactly as KiCad
does it, or ERC reports a library mismatch).
"""
import os
import random
import re
import uuid

STOCK = '/usr/share/kicad/symbols'
GRID = 1.27
_rng = random.Random('WPT-TX-DISPLAY')


def _uuid():
    """identifiers from a fixed sequence: running the script again gives the same file (and a readable diff)"""
    return uuid.UUID(int=_rng.getrandbits(128), version=4)


def _block_at(s, j):
    d = 0
    for k in range(j, len(s)):
        if s[k] == '(':
            d += 1
        elif s[k] == ')':
            d -= 1
            if d == 0:
                return s[j:k + 1]
    raise ValueError('unbalanced')


def fmt(v):
    return ('%.4f' % v).rstrip('0').rstrip('.') if abs(v) > 1e-9 else '0'


def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


class LibSymbol:
    def __init__(self, lib_id, text):
        self.lib_id, self.text = lib_id, text
        assert '(extends ' not in text, lib_id + ' extends another symbol'
        self.pins = {}                                   # number -> (x, y, name, type)
        for m in re.finditer(r'\(pin (\w+) (\w+)\s*\(at (-?[\d.]+) (-?[\d.]+) (\d+)\)\s*\(length [\d.]+\)(?:\s*\(hide yes\))?'
                             r'\s*\(name "((?:[^"\\]|\\.)*)".*?\(number "([^"]*)"', text, re.S):
            self.pins[m.group(7)] = (float(m.group(3)), float(m.group(4)), m.group(6), m.group(1))
        self.props = dict(re.findall(r'\(property "([^"]+)" "((?:[^"\\]|\\.)*)"', text))
        self.power = '(power' in text.split('(property', 1)[0]


def load_symbol(lib_id, local_dir=None):
    lib, name = lib_id.split(':')
    path = os.path.join(local_dir, lib + '.kicad_sym') if local_dir and os.path.exists(os.path.join(local_dir, lib + '.kicad_sym')) \
        else os.path.join(STOCK, lib + '.kicad_sym')
    t = open(path, encoding='utf-8').read()
    i = t.index('\n\t(symbol "%s"\n' % name) + 2
    return LibSymbol(lib_id, _block_at(t, i))


# sheet coordinates of a symbol-space point for the four orientations (KiCad's transforms)
ROT = {0: lambda x, y: (x, -y), 90: lambda x, y: (-y, -x), 180: lambda x, y: (-x, y), 270: lambda x, y: (y, x)}


class Sheet:
    def __init__(self, project, title, date, rev, paper='A4', local_dir=None, comment=''):
        self.project, self.title, self.date, self.rev, self.paper, self.comment = project, title, date, rev, paper, comment
        self.local_dir = local_dir
        self.uuid = str(_uuid())
        self.libs, self.items = {}, []
        self.npwr = 0
        self.refs = set()

    def lib(self, lib_id):
        if lib_id not in self.libs:
            self.libs[lib_id] = load_symbol(lib_id, self.local_dir)
        return self.libs[lib_id]

    # ---- parts
    def place(self, lib_id, ref, value, x, y, rot=0, fields=None, ref_at=None, val_at=None, in_bom=True, on_board=True, hide_value=False,
              mirror=False, in_pos=None, hide_ref=False, val_just='left', val_angle=0, dnp=False):
        """mirror: flip the symbol left-right (KiCad's "mirror y"), only with rot 0"""
        s = self.lib(lib_id)
        assert not (mirror and rot), 'mirror is only implemented for rot 0'
        assert ref not in self.refs, ref
        self.refs.add(ref)
        fields = dict(fields or {})
        props = [('Reference', ref, ref_at or (x + 2.54, y - 1.27), hide_ref, 'left'),
                 ('Value', value, val_at or (x + 2.54, y + 1.27), hide_value, val_just),
                 ('Footprint', fields.pop('Footprint', s.props.get('Footprint', '')), (x, y), True, None),
                 ('Datasheet', fields.pop('Datasheet', s.props.get('Datasheet', '') or '~'), (x, y), True, None),
                 ('Description', fields.pop('Description', s.props.get('Description', '')), (x, y), True, None)]
        props += [(k, v, (x, y), True, None) for k, v in fields.items()]
        out = ['\t(symbol', '\t\t(lib_id "%s")' % lib_id, '\t\t(at %s %s %d)' % (fmt(x), fmt(y), rot)]
        if mirror:
            out.append('\t\t(mirror y)')
        if in_pos is None:
            in_pos = on_board
        out += ['\t\t(unit 1)', '\t\t(body_style 1)',
                '\t\t(exclude_from_sim no)', '\t\t(in_bom %s)' % ('yes' if in_bom else 'no'), '\t\t(on_board %s)' % ('yes' if on_board else 'no'),
                '\t\t(in_pos_files %s)' % ('yes' if in_pos else 'no'), '\t\t(dnp %s)' % ('yes' if dnp else 'no'), '\t\t(uuid "%s")' % _uuid()]
        for name, val, at, hide, just in props:
            ang = val_angle if name == 'Value' else 0      # a field turns with its symbol: 90 on a symbol lying on its side reads level
            out += ['\t\t(property "%s" "%s"' % (name, esc(val)), '\t\t\t(at %s %s %d)' % (fmt(at[0]), fmt(at[1]), ang)]
            if hide:
                out.append('\t\t\t(hide yes)')
            out += ['\t\t\t(show_name no)', '\t\t\t(do_not_autoplace no)', '\t\t\t(effects', '\t\t\t\t(font', '\t\t\t\t\t(size 1.27 1.27)', '\t\t\t\t)']
            if just and just != 'center':
                out.append('\t\t\t\t(justify %s)' % just)
            out += ['\t\t\t)', '\t\t)']
        for num in s.pins:
            out += ['\t\t(pin "%s"' % num, '\t\t\t(uuid "%s")' % _uuid(), '\t\t)']
        out += ['\t\t(instances', '\t\t\t(project "%s"' % self.project, '\t\t\t\t(path "/%s"' % self.uuid, '\t\t\t\t\t(reference "%s")' % ref,
                '\t\t\t\t\t(unit 1)', '\t\t\t\t)', '\t\t\t)', '\t\t)', '\t)']
        self.items.append('\n'.join(out))
        pins = {}
        for num, (px, py, _, _) in s.pins.items():
            dx, dy = ROT[rot](-px if mirror else px, py)
            pins[num] = (round(x + dx, 4), round(y + dy, 4))
        return pins

    def power(self, lib_id, p, side='auto'):
        """A power symbol whose pin sits on p; its reference is hidden, its value shown.
        side: where the symbol points. 'auto' = down for GND, up for supplies and flags; 'right' = lying on its side."""
        self.npwr += 1
        name = lib_id.split(':')[1]
        ref = ('#FLG%02d' if name == 'PWR_FLAG' else '#PWR%02d') % self.npwr
        if side == 'right':
            rot = 90 if name == 'GND' else 270
            # a symbol turned by 90 degrees turns the justification of its fields with it: "right" reads from the anchor rightwards
            return self.place(lib_id, ref, name, p[0], p[1], rot, ref_at=(p[0] + 2.54, p[1]), val_at=(p[0] + 3.81, p[1]),
                              in_bom=False, hide_ref=True, val_just='right' if name == 'GND' else 'left', val_angle=90)
        dy = 3.81 if name == 'GND' else -3.81
        return self.place(lib_id, ref, name, p[0], p[1], 0, ref_at=(p[0], p[1] - dy), val_at=(p[0], p[1] + dy),
                          in_bom=False, hide_ref=True, val_just='center')

    # ---- connections
    def wire(self, *pts):
        for a, b in zip(pts, pts[1:]):
            assert abs(a[0] - b[0]) < 1e-6 or abs(a[1] - b[1]) < 1e-6, ('wire not orthogonal', a, b)
            if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
                continue
            self.items.append('\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)'
                              % (fmt(a[0]), fmt(a[1]), fmt(b[0]), fmt(b[1]), _uuid()))

    def label(self, name, p, rot=0, just=None):
        just = just or {0: 'left bottom', 180: 'right bottom', 90: 'left bottom', 270: 'right bottom'}[rot]
        self.items.append('\t(label "%s"\n\t\t(at %s %s %d)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n\t)'
                          % (esc(name), fmt(p[0]), fmt(p[1]), rot, just, _uuid()))

    def nc(self, p):
        self.items.append('\t(no_connect\n\t\t(at %s %s)\n\t\t(uuid "%s")\n\t)' % (fmt(p[0]), fmt(p[1]), _uuid()))

    def junction(self, p):
        self.items.append('\t(junction\n\t\t(at %s %s)\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "%s")\n\t)' % (fmt(p[0]), fmt(p[1]), _uuid()))

    def text(self, s, p, size=1.27):
        self.items.append('\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at %s %s 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size %s %s)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)'
                          % (esc(s).replace('\n', '\\n'), fmt(p[0]), fmt(p[1]), fmt(size), fmt(size), _uuid()))

    # ---- file
    def write(self, path):
        libs = []
        for lib_id, s in sorted(self.libs.items()):
            name = lib_id.split(':')[1]
            emb = '\n'.join('\t' + l for l in ('\t' + s.text).split('\n')).replace('(symbol "%s"\n' % name, '(symbol "%s"\n' % lib_id, 1)
            libs.append(emb)
        head = ['(kicad_sch', '\t(version 20260306)', '\t(generator "eeschema")', '\t(generator_version "10.0")', '\t(uuid "%s")' % self.uuid,
                '\t(paper "%s")' % self.paper, '\t(title_block', '\t\t(title "%s")' % esc(self.title), '\t\t(date "%s")' % self.date,
                '\t\t(rev "%s")' % esc(self.rev)]
        if self.comment:
            head.append('\t\t(comment 1 "%s")' % esc(self.comment))
        head += ['\t)', '\t(lib_symbols', '\n'.join(libs), '\t)']
        tail = ['\t(sheet_instances', '\t\t(path "/"', '\t\t\t(page "1")', '\t\t)', '\t)', '\t(embedded_fonts no)', ')', '']
        text = '\n'.join(head + self.items + tail)
        assert text.count('(') == text.count(')')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)

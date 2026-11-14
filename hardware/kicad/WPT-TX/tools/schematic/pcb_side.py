#!/usr/bin/env python3
"""Bring the board's per-footprint data in line with the schematic (no geometry is touched).

usage: pcb_side.py BOARD_IN BOARD_OUT NETLIST [--values]

NETLIST is `kicad-cli sch export netlist --format kicadsexpr` of the schematic,
i.e. the same data "Update PCB from Schematic" consumes.

For every footprint that has a schematic symbol it sets:
  * the DNP attribute (base state),
  * hidden "Manufacturer" / "Manufacturer Part Number" / "Assembly Note" fields where the symbol has them
    (added when absent on the footprint), and the datasheet link where the symbol has one,
  * the per-variant DNP overrides carried by the netlist (HRTIM),
  * with --values, the Value field (fixes value drift that predates this work).
It also registers the variant names and descriptions on the board.
Nothing is moved, added or removed; symbols without a footprint are only reported.
"""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
import sx  # noqa: E402

FIELDS = ('Manufacturer', 'Manufacturer Part Number', 'Assembly Note')


def kids(n, name):
    return [x for x in n if isinstance(x, list) and x and x[0] == name]


def val(n, name, default=''):
    k = kids(n, name)
    return k[0][1] if k and len(k[0]) > 1 else default


def load_netlist(path):
    root = sx.to_plain(sx.parse(open(path, encoding='utf-8').read()))
    comps = {}
    for c in kids(kids(root, 'components')[0], 'comp'):
        fields = {}
        for fl in kids(c, 'fields'):
            for f in kids(fl, 'field'):
                fields[val(f, 'name')] = f[2] if len(f) > 2 and isinstance(f[2], str) else ''
        props = {val(p, 'name'): val(p, 'value') for p in kids(c, 'property')}
        variants = {}
        for vs in kids(c, 'variants'):
            for v in kids(vs, 'variant'):
                vp = {val(p, 'name'): val(p, 'value') for p in kids(v, 'property')}
                variants[val(v, 'name')] = vp
        comps[val(c, 'ref')] = {'value': val(c, 'value'), 'footprint': val(c, 'footprint'),
                                'fields': fields, 'dnp': 'dnp' in props, 'variants': variants}
    design_variants = {}
    for vs in kids(root, 'variants'):
        for v in kids(vs, 'variant'):
            design_variants[val(v, 'name')] = val(v, 'description')
    return comps, design_variants


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    fix_values = '--values' in sys.argv
    board_in, board_out, netlist = args
    comps, design_variants = load_netlist(netlist)
    board = pcbnew.LoadBoard(board_in)
    for name, descr in sorted(design_variants.items()):
        if not board.HasVariant(name):
            board.AddVariant(name)
        board.SetVariantDescription(name, descr)
    log = {'board variants': sorted(design_variants), 'dnp': [], 'field': [], 'value': [], 'variant': [],
           'no footprint on board': [], 'footprint id differs': []}
    by_ref = {}
    for fp in board.GetFootprints():
        by_ref.setdefault(fp.GetReference(), []).append(fp)
    for ref, c in sorted(comps.items()):
        fps = by_ref.get(ref, [])
        if len(fps) != 1:
            log['no footprint on board'].append(f"{ref} ({len(fps)} footprints)")
            continue
        fp = fps[0]
        if fp.GetFPID().GetUniStringLibId() != c['footprint']:
            log['footprint id differs'].append(f"{ref}: board {fp.GetFPID().GetUniStringLibId()} / schematic {c['footprint']}")
        if fp.IsDNP() != c['dnp']:
            fp.SetDNP(c['dnp'])
            log['dnp'].append(f"{ref}={'DNP' if c['dnp'] else 'fitted'}")
        if fp.GetValue() != c['value']:
            if fix_values:
                log['value'].append(f"{ref}: {fp.GetValue()} -> {c['value']}")
                fp.SetValue(c['value'])
            else:
                log['value'].append(f"{ref}: board {fp.GetValue()} / schematic {c['value']} (not changed)")
        for fname in FIELDS + ('Datasheet',):
            if fname not in c['fields']:
                continue
            text = c['fields'][fname]
            if fname == 'Datasheet' and text in ('', '~'):     # only real links are carried over
                continue
            if fp.HasField(fname):
                f = fp.GetField(fname)
                if f.GetText() != text:
                    log['field'].append(f"{ref}.{fname}: {f.GetText()!r} -> {text!r}")
                    f.SetText(text)
            else:
                f = pcbnew.PCB_FIELD(fp, pcbnew.FIELD_T_USER, fname)
                f.SetText(text)
                f.SetVisible(False)
                f.SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
                f.SetPosition(fp.GetPosition())
                fp.Add(f)
                log['field'].append(f"{ref}.{fname}: added {text!r}")
        for vname, vp in sorted(c['variants'].items()):
            if 'dnp' in vp:
                v = fp.GetVariant(vname) if fp.HasVariant(vname) else fp.AddVariant(vname)
                v.SetDNP(vp['dnp'] == '1')
                log['variant'].append(f"{ref}: {vname} {'DNP' if vp['dnp'] == '1' else 'fitted'}")
    pcbnew.SaveBoard(board_out, board)
    for k, v in log.items():
        print(f"{k}: {len(v)}")
        for x in v:
            print('   ' + x)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Query a KiCad s-expression netlist.

usage:
  netq.py NETLIST comp REF [REF...]     # pins of a component -> net -> other nodes
  netq.py NETLIST net NAME [NAME...]    # nodes on a net (substring match with ~NAME)
  netq.py NETLIST find REGEX            # components whose ref/value/footprint match
  netq.py NETLIST dump OUT.json         # normalised dump for diffing
"""
import json
import re
import sys


def parse(text):
    """Minimal s-expression parser -> nested lists of str."""
    i, n = 0, len(text)
    stack = [[]]
    while i < n:
        c = text[i]
        if c == '(':
            stack.append([])
            i += 1
        elif c == ')':
            done = stack.pop()
            stack[-1].append(done)
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while text[j] != '"':
                if text[j] == '\\':
                    j += 1
                buf.append(text[j])
                j += 1
            stack[-1].append(''.join(buf))
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()':
                j += 1
            stack[-1].append(text[i:j])
            i = j
    return stack[0][0]


def kids(node, name):
    return [x for x in node if isinstance(x, list) and x and x[0] == name]


def kid(node, name, default=None):
    k = kids(node, name)
    return k[0] if k else default


def val(node, name, default=''):
    k = kid(node, name)
    return k[1] if k and len(k) > 1 else default


def load(path):
    root = parse(open(path, encoding='utf-8').read())
    comps = {}
    for c in kids(kid(root, 'components'), 'comp'):
        ref = val(c, 'ref')
        props = {p[1][1]: p[2][1] if len(p) > 2 and len(p[2]) > 1 else ''
                 for p in kids(c, 'property')
                 if isinstance(p[1], list)}
        sp = kid(c, 'sheetpath')
        comps[ref] = {
            'value': val(c, 'value'),
            'footprint': val(c, 'footprint'),
            'sheet': val(sp, 'names') if sp else '',
            'dnp': 'dnp' in props or any(k.lower() == 'dnp' for k in props),
            'props': props,
        }
    nets = {}
    for nt in kids(kid(root, 'nets'), 'net'):
        name = val(nt, 'name')
        nodes = []
        for nd in kids(nt, 'node'):
            nodes.append((val(nd, 'ref'), val(nd, 'pin'), val(nd, 'pinfunction'), val(nd, 'pintype')))
        nets[name] = nodes
    return comps, nets


def main():
    path, cmd, args = sys.argv[1], sys.argv[2], sys.argv[3:]
    comps, nets = load(path)
    pin2net = {}
    for name, nodes in nets.items():
        for ref, pin, fn, _ in nodes:
            pin2net[(ref, pin)] = (name, fn)

    def tag(ref):
        c = comps.get(ref, {})
        return f"{ref}[{c.get('value', '?')}{' DNP' if c.get('dnp') else ''}]"

    if cmd == 'comp':
        for ref in args:
            c = comps[ref]
            print(f"## {ref}  value={c['value']}  fp={c['footprint']}  sheet={c['sheet']}  dnp={c['dnp']}")
            pins = sorted((k[1] for k in pin2net if k[0] == ref),
                          key=lambda p: (len(p), p) if not p.isdigit() else (0, f"{int(p):04d}"))
            for p in pins:
                net, fn = pin2net[(ref, p)]
                others = [f"{tag(r)}.{q}" for r, q, _, _ in nets[net] if not (r == ref and q == p)]
                shown = ', '.join(others[:8]) + (f" ...(+{len(others) - 8})" if len(others) > 8 else '')
                print(f"  {p:>3} {fn:<34} {net:<34} {shown}")
    elif cmd == 'net':
        for a in args:
            names = [k for k in nets if (a[1:] in k if a.startswith('~') else k == a)]
            for name in names:
                print(f"## {name}: " + ', '.join(f"{tag(r)}.{q}({fn})" for r, q, fn, _ in nets[name]))
            if not names:
                print(f"## {a}: (no such net)")
    elif cmd == 'find':
        rx = re.compile(args[0], re.I)
        for ref in sorted(comps):
            c = comps[ref]
            if rx.search(ref) or rx.search(c['value']) or rx.search(c['footprint']):
                print(f"{ref:<8} {c['value']:<28} {c['footprint']:<60} {c['sheet']} {'DNP' if c['dnp'] else ''}")
    elif cmd == 'dump':
        out = {
            'comps': {r: {k: c[k] for k in ('value', 'footprint', 'sheet', 'dnp')} for r, c in comps.items()},
            'nets': {n: sorted(f"{r}.{p}" for r, p, _, _ in nodes) for n, nodes in nets.items()},
        }
        json.dump(out, open(args[0], 'w'), indent=1, sort_keys=True)
        print(f"{len(comps)} components, {len(nets)} nets -> {args[0]}")


if __name__ == '__main__':
    main()

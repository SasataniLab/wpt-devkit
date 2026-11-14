"""Span-preserving s-expression parser for KiCad files.

Nodes keep the character offsets of their source text so that edits can be
applied as plain text splices (minimal diff, formatting untouched).
"""


class Atom:
    __slots__ = ('raw', 'start', 'end', 'quoted')

    def __init__(self, raw, start, end, quoted):
        self.raw = raw          # source text including quotes
        self.start = start
        self.end = end
        self.quoted = quoted

    @property
    def val(self):
        if not self.quoted:
            return self.raw
        s = self.raw[1:-1]
        out = []
        i = 0
        while i < len(s):
            c = s[i]
            if c == '\\' and i + 1 < len(s):
                n = s[i + 1]
                out.append({'n': '\n', 't': '\t', 'r': '\r'}.get(n, n))
                i += 2
            else:
                out.append(c)
                i += 1
        return ''.join(out)

    def __repr__(self):
        return f"Atom({self.raw})"


class Node:
    __slots__ = ('items', 'start', 'end')

    def __init__(self, start):
        self.items = []
        self.start = start
        self.end = None

    @property
    def name(self):
        if self.items and isinstance(self.items[0], Atom):
            return self.items[0].raw
        return None

    def kids(self, name=None):
        return [x for x in self.items if isinstance(x, Node) and (name is None or x.name == name)]

    def kid(self, name):
        for x in self.items:
            if isinstance(x, Node) and x.name == name:
                return x
        return None

    def atoms(self):
        return [x for x in self.items[1:] if isinstance(x, Atom)]

    def a(self, i=0, default=None):
        """i-th atom value after the node name."""
        at = self.atoms()
        return at[i].val if i < len(at) else default

    def val(self, name, default=None):
        k = self.kid(name)
        if k is None:
            return default
        return k.a(0, default)

    def walk(self):
        yield self
        for x in self.items:
            if isinstance(x, Node):
                yield from x.walk()

    def text(self, src):
        return src[self.start:self.end]

    def __repr__(self):
        return f"Node({self.name}, {len(self.items)} items)"


def parse(text):
    i, n = 0, len(text)
    root = Node(0)
    stack = [root]
    while i < n:
        c = text[i]
        if c == '(':
            nd = Node(i)
            stack[-1].items.append(nd)
            stack.append(nd)
            i += 1
        elif c == ')':
            nd = stack.pop()
            i += 1
            nd.end = i
        elif c == '"':
            j = i + 1
            while text[j] != '"':
                if text[j] == '\\':
                    j += 1
                j += 1
            stack[-1].items.append(Atom(text[i:j + 1], i, j + 1, True))
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()':
                j += 1
            stack[-1].items.append(Atom(text[i:j], i, j, False))
            i = j
    assert len(stack) == 1, 'unbalanced parens'
    return root.items[0]


def quote(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def apply_edits(text, edits):
    """edits: list of (start, end, replacement); must not overlap."""
    edits = sorted(edits, key=lambda e: (e[0], e[1]))
    for a, b in zip(edits, edits[1:]):
        assert a[1] <= b[0], f'overlapping edits {a[:2]} {b[:2]}'
    out = []
    pos = 0
    for s, e, r in edits:
        out.append(text[pos:s])
        out.append(r)
        pos = e
    out.append(text[pos:])
    return ''.join(out)


def line_start(text, pos):
    """Offset of the beginning of the line containing pos."""
    return text.rfind('\n', 0, pos) + 1


def indent_of(text, pos):
    ls = line_start(text, pos)
    j = ls
    while j < len(text) and text[j] in ' \t':
        j += 1
    return text[ls:j]


def to_plain(node):
    """Nested python lists of str (quotes dropped) for comparisons."""
    if isinstance(node, Atom):
        return node.val
    return [to_plain(x) for x in node.items]

"""Minimal s-expression reader/writer for KiCad files (pure Python, no deps)."""


class Sym(str):
    """Bare (unquoted) atom."""
    __slots__ = ()


def parse(text):
    pos = 0
    n = len(text)
    stack = [[]]
    while pos < n:
        c = text[pos]
        if c in ' \t\r\n':
            pos += 1
        elif c == '(':
            new = []
            stack[-1].append(new)
            stack.append(new)
            pos += 1
        elif c == ')':
            stack.pop()
            pos += 1
        elif c == '"':
            pos += 1
            buf = []
            while True:
                ch = text[pos]
                if ch == '\\':
                    nx = text[pos + 1]
                    buf.append({'n': '\n', 't': '\t', 'r': '\r'}.get(nx, nx))
                    pos += 2
                elif ch == '"':
                    pos += 1
                    break
                else:
                    buf.append(ch)
                    pos += 1
            stack[-1].append(''.join(buf))
        else:
            start = pos
            while pos < n and text[pos] not in ' \t\r\n()':
                pos += 1
            stack[-1].append(Sym(text[start:pos]))
    return stack[0][0]


def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def dump(node, indent=0):
    out = []
    _dump(node, indent, out)
    return ''.join(out)


def _atom(a):
    if isinstance(a, Sym):
        return str(a)
    if isinstance(a, str):
        return q(a)
    if isinstance(a, float):
        s = ('%.6f' % a).rstrip('0').rstrip('.')
        return s if s not in ('-0', '') else '0'
    return str(a)


def _dump(node, indent, out):
    pad = '\t' * indent
    if not isinstance(node, list):
        out.append(pad + _atom(node) + '\n')
        return
    if all(not isinstance(x, list) for x in node):
        out.append(pad + '(' + ' '.join(_atom(x) for x in node) + ')\n')
        return
    # head atoms on first line, then children
    i = 0
    head = []
    while i < len(node) and not isinstance(node[i], list):
        head.append(_atom(node[i]))
        i += 1
    out.append(pad + '(' + ' '.join(head) + '\n')
    for x in node[i:]:
        _dump(x, indent + 1, out)
    out.append(pad + ')\n')


def find(node, name):
    for x in node:
        if isinstance(x, list) and x and x[0] == name:
            return x
    return None


def findall(node, name):
    return [x for x in node if isinstance(x, list) and x and x[0] == name]

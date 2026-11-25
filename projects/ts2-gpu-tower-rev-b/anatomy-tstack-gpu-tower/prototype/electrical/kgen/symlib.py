"""Load symbols from the installed KiCad symbol libraries, flattening `extends`."""
import copy
import os
from sexpr import parse, find, findall, Sym

SYMDIR = "/usr/share/kicad/symbols"
_cache = {}
EXTRA = {}   # project-local libraries: {libname: path to .kicad_sym}


def _lib(lib):
    if lib not in _cache:
        p = EXTRA.get(lib) or os.path.join(SYMDIR, lib + '.kicad_sym')
        if os.path.isdir(p):
            syms = {}
            for fn in os.listdir(p):
                if fn.endswith('.kicad_sym'):
                    with open(os.path.join(p, fn), encoding='utf-8') as f:
                        t = parse(f.read())
                    for s in findall(t, 'symbol'):
                        syms[s[1]] = s
            _cache[lib] = syms
        else:
            with open(p, encoding='utf-8') as f:
                t = parse(f.read())
            _cache[lib] = {s[1]: s for s in findall(t, 'symbol')}
    return _cache[lib]


def names(lib):
    return list(_lib(lib).keys())


def load(lib_id):
    """Return a flattened symbol node named 'Lib:Name' ready for lib_symbols."""
    lib, name = lib_id.split(':')
    syms = _lib(lib)
    s = copy.deepcopy(syms[name])
    ext = find(s, 'extends')
    if ext is not None:
        parent = copy.deepcopy(syms[ext[1]])
        pext = find(parent, 'extends')
        assert pext is None, 'multi-level extends not handled'
        # child properties override parent properties
        cprops = {p[1]: p for p in findall(s, 'property')}
        out = []
        for item in parent:
            if isinstance(item, list) and item[0] == 'property':
                if item[1] in cprops:
                    out.append(cprops.pop(item[1]))
                else:
                    out.append(item)
            elif isinstance(item, list) and item[0] == 'symbol':
                item[1] = name + item[1][len(ext[1]):]
                out.append(item)
            else:
                out.append(item)
        # leftover child props: insert before first sub-symbol
        idx = next((i for i, x in enumerate(out) if isinstance(x, list) and x[0] == 'symbol'), len(out))
        for p in cprops.values():
            out.insert(idx, p)
            idx += 1
        s = out
    s[1] = lib_id
    return s


def pins(symnode):
    """List of dicts: number, name, x, y, angle, type, hide, unit."""
    res = []
    for sub in findall(symnode, 'symbol'):
        # sub name: Name_<unit>_<style>
        parts = sub[1].rsplit('_', 2)
        unit = int(parts[1])
        for p in findall(sub, 'pin'):
            at = find(p, 'at')
            hide = False
            h = find(p, 'hide')
            if h is not None and (len(h) < 2 or h[1] == 'yes'):
                hide = True
            if Sym('hide') in [x for x in p if not isinstance(x, list)]:
                hide = True
            res.append(dict(number=find(p, 'number')[1], name=find(p, 'name')[1],
                            x=float(at[1]), y=float(at[2]), angle=int(float(at[3])) if len(at) > 3 else 0,
                            type=str(p[1]), hide=hide, unit=unit,
                            length=float(find(p, 'length')[1])))
    return res


if __name__ == '__main__':
    import sys
    for lid in sys.argv[1:]:
        if lid.endswith(':?'):
            print(names(lid[:-2]))
            continue
        s = load(lid)
        print('==', lid, 'ext' if find(_lib(lid.split(':')[0])[lid.split(':')[1]], 'extends') else '')
        for p in pins(s):
            print('  %-5s %-14s (%7.2f,%7.2f) a=%3d %s%s u%d' % (p['number'], p['name'], p['x'], p['y'], p['angle'], p['type'], ' HIDE' if p['hide'] else '', p['unit']))

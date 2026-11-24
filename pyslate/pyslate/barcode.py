"""Pyslate's own Code 128 barcodes, drawn as SVG. No outside libraries.

Code 128 is what carriers and handheld scanners read: every USB/Bluetooth scanner types
it back as text followed by Enter. Digit runs use code set C (two digits per symbol) so
tracking numbers stay short; everything else uses code set B (printable ASCII).
"""

from __future__ import annotations

# Bar/space widths for symbol values 0..106 (106 = stop, which has a final 2-wide bar).
PATTERNS = (
    "212222 222122 222221 121223 121322 131222 122213 122312 132212 221213 "
    "221312 231212 112232 122132 122231 113222 123122 123221 223211 221132 "
    "221231 213212 223112 312131 311222 321122 321221 312212 322112 322211 "
    "212123 212321 232121 111323 131123 131321 112313 132113 132311 211313 "
    "231113 231311 112133 112331 132131 113123 113321 133121 313121 211331 "
    "231131 213113 213311 213131 311123 311321 331121 312113 312311 332111 "
    "314111 221411 431111 111224 111422 121124 121421 141122 141221 112214 "
    "112412 122114 122411 142112 142211 241211 221114 413111 241112 134111 "
    "111242 121142 121241 114212 124112 124211 411212 421112 421211 212141 "
    "214121 412121 111143 111341 131141 114113 114311 411113 411311 113141 "
    "114131 311141 411131 211412 211214 211232 2331112"
).split()
START_B, START_C, CODE_B, CODE_C, STOP = 104, 105, 100, 99, 106


class BarcodeError(ValueError):
    pass


def _digit_run(text: str, i: int) -> int:
    n = 0
    while i + n < len(text) and text[i + n].isdigit():
        n += 1
    return n


def encode(text: str) -> list[int]:
    """Symbol values for `text`, including start, checksum and stop."""
    if not text:
        raise BarcodeError("Nothing to encode")
    if any(not (32 <= ord(ch) <= 126) for ch in text):
        raise BarcodeError("Code 128 labels take plain printable characters only")
    values: list[int] = []
    i = 0
    mode = None
    while i < len(text):
        run = _digit_run(text, i)
        # Set C pays off for 4+ digits (or a whole numeric string of 2+); keep runs even.
        use_c = run >= 4 or (run >= 2 and run == len(text) - i and mode in (None, "C") and run % 2 == 0)
        if use_c:
            run -= run % 2
            if mode is None:
                values.append(START_C)
            elif mode != "C":
                values.append(CODE_C)
            mode = "C"
            for k in range(i, i + run, 2):
                values.append(int(text[k:k + 2]))
            i += run
        else:
            if mode is None:
                values.append(START_B)
            elif mode != "B":
                values.append(CODE_B)
            mode = "B"
            values.append(ord(text[i]) - 32)
            i += 1
    check = values[0] + sum(pos * v for pos, v in enumerate(values[1:], start=1))
    values.append(check % 103)
    values.append(STOP)
    return values


def modules(text: str) -> list[tuple[bool, int]]:
    """(is_bar, width) runs in modules, without the quiet zones."""
    out = []
    for v in encode(text):
        for k, w in enumerate(PATTERNS[v]):
            out.append((k % 2 == 0, int(w)))
    return out


def svg(text: str, height: float = 60, module: float = 2, quiet: int = 10, label: bool = True,
        font_size: float = 14) -> str:
    """A Code 128 barcode as an SVG string, sized in user units (1 module = `module`)."""
    runs = modules(text)
    total = sum(w for _, w in runs) + 2 * quiet
    x = quiet
    rects = []
    for is_bar, w in runs:
        if is_bar:
            rects.append(f'<rect x="{x * module:g}" y="0" width="{w * module:g}" height="{height:g}"/>')
        x += w
    text_h = font_size * 1.4 if label else 0
    width = total * module
    caption = (f'<text x="{width / 2:g}" y="{height + font_size * 1.15:g}" text-anchor="middle" '
               f'font-family="ui-monospace, Menlo, Consolas, monospace" font-size="{font_size:g}">{_xml(text)}</text>'
               if label else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:g} {height + text_h:g}" '
            f'class="barcode" role="img" aria-label="Barcode {_xml(text)}" preserveAspectRatio="xMidYMid meet">'
            f'<rect width="100%" height="100%" fill="#fff"/><g fill="#000">{"".join(rects)}</g>{caption}</svg>')


def _xml(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ---- Pyslate's own label codes --------------------------------------------------------

PREFIX = "PYS"


def box_code(order_number: int, box: int, boxes: int) -> str:
    """The code on every box: order, this box, how many boxes. e.g. PYS-1004-01-02."""
    return f"{PREFIX}-{order_number}-{box:02d}-{boxes:02d}"


def parse_code(code: str) -> dict | None:
    """Read a scanned code: a box code, "PYS-1004", "#1004" or a bare order number."""
    raw = code.strip().upper().replace(" ", "")
    if raw.startswith(PREFIX):
        parts = [p for p in raw[len(PREFIX):].split("-") if p]
        if parts and parts[0].isdigit():
            out = {"order": int(parts[0])}
            if len(parts) >= 3 and parts[1].isdigit() and parts[2].isdigit():
                out.update(box=int(parts[1]), boxes=int(parts[2]))
            return out
        return None
    raw = raw.lstrip("#")
    if raw.isdigit() and len(raw) <= 9:
        return {"order": int(raw)}
    return None

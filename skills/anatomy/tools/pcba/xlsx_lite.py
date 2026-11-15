"""Write a small .xlsx workbook with the standard library only (no openpyxl needed).

Sheets are lists of rows; the first row of each sheet is a bold, frozen header unless the
sheet sets header=False. Numbers stay numbers. Good enough for a BOM an assembler opens in Excel.
"""
import zipfile
from xml.sax.saxutils import escape


def _col(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def _cell(ref, v, style):
    st = ' s="%d"' % style if style else ""
    if isinstance(v, bool):
        v = "yes" if v else "no"
    if isinstance(v, (int, float)):
        return '<c r="%s"%s><v>%s</v></c>' % (ref, st, repr(v) if isinstance(v, float) else v)
    txt = escape("" if v is None else str(v))
    return '<c r="%s" t="inlineStr"%s><is><t xml:space="preserve">%s</t></is></c>' % (ref, st, txt)


def write_xlsx(path, sheets):
    """sheets: list of dicts {name, rows, header=True, widths=None, wrap_cols=()}"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        n = len(sheets)
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   + "".join('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' % (i + 1) for i in range(n))
                   + "</Types>")
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                   "</Relationships>")
        z.writestr("xl/workbook.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + "".join('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (escape(s["name"][:31]), i + 1, i + 1) for i, s in enumerate(sheets))
                   + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet%d.xml"/>' % (i + 1, i + 1) for i in range(n))
                   + '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>' % (n + 1)
                   + "</Relationships>")
        # style 1 = bold header with fill, style 2 = wrapped text
        z.writestr("xl/styles.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                   '<fonts count="2"><font><sz val="10"/><name val="Calibri"/></font><font><b/><sz val="10"/><name val="Calibri"/></font></fonts>'
                   '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
                   '<fill><patternFill patternType="solid"><fgColor rgb="FFD9E1F2"/></patternFill></fill></fills>'
                   '<borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs>'
                   '<cellXfs count="3"><xf/><xf fontId="1" fillId="2" applyFont="1" applyFill="1"/>'
                   '<xf applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf></cellXfs>'
                   "</styleSheet>")
        for i, s in enumerate(sheets):
            rows, hdr = s["rows"], s.get("header", True)
            wrap = set(s.get("wrap_cols", ()))
            widths = s.get("widths")
            if not widths and rows:
                ncol = max(len(r) for r in rows)
                widths = [min(60, max(8, max(len(str(r[c])) if c < len(r) and r[c] is not None else 0 for r in rows) + 2)) for c in range(ncol)]
            xml = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">']
            if hdr:
                xml.append('<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>')
            if widths:
                xml.append("<cols>" + "".join('<col min="%d" max="%d" width="%s" customWidth="1"/>' % (c + 1, c + 1, w) for c, w in enumerate(widths)) + "</cols>")
            xml.append("<sheetData>")
            for r, row in enumerate(rows):
                cells = []
                for c, v in enumerate(row):
                    style = 1 if (hdr and r == 0) else (2 if c in wrap else 0)
                    cells.append(_cell("%s%d" % (_col(c), r + 1), v, style))
                xml.append('<row r="%d">%s</row>' % (r + 1, "".join(cells)))
            xml.append("</sheetData>")
            if hdr and rows:
                xml.append('<autoFilter ref="A1:%s%d"/>' % (_col(len(rows[0]) - 1), len(rows)))
            xml.append("</worksheet>")
            z.writestr("xl/worksheets/sheet%d.xml" % (i + 1), "".join(xml))

#!/usr/bin/env python3
"""Render the Engineering and Manufacturing Summary (prototype-to-production brief).

Reads   <project>/production/production.json   (schema: references/production-brief.md)
Writes  <project>/production/production-brief.html   self-contained, prints cleanly to PDF
        <project>/production/production-brief.pdf    when Chromium, Chrome or Edge is available
        <project>/production/production-brief.md     plain-text version for diffing
        <project>/production/cost-model.csv          every cost line at every volume tier
        <project>/production/brief-check.md          the honesty and completeness check

Usage:  python make_brief.py <project-dir | production.json> [--no-pdf]
Exit 1 if the check fails (a figure without a basis, a non-assumed figure without a source,
a section missing). Standard library only; PDF via playwright if installed, else a headless
Chrome/Edge found on the machine.
"""
import csv, html, json, math, os, shutil, subprocess, sys, tempfile
from datetime import date
from pathlib import Path

BASES = ("measured", "observed", "quoted", "documented", "estimate", "assumed")
NEEDS_SOURCE = ("quoted", "documented")
REQUIRED = ("executive_summary", "problem", "product", "status", "cost_model", "dfm", "supply_chain",
            "compliance", "partners", "risks", "stages", "ip", "assumptions", "sources")
# Categorical slots (fixed order, validated palette; see the dataviz reference palette).
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]

E = lambda s: html.escape(str(s if s is not None else ""))


# ------------------------------------------------------------------ units
def dual(v, u):
    """Format a value in SI with its US customary equivalent: 183 mm [7.20 in]."""
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        if u == "mm":
            return " × ".join(f"{x:g}" for x in v) + " mm [" + " × ".join(f"{x / 25.4:.2f}" for x in v) + " in]"
        return " × ".join(dual(x, u) for x in v)
    conv = {
        "mm": (lambda x: x / 25.4, "in", 2), "m": (lambda x: x * 3.28084, "ft", 2),
        "kg": (lambda x: x * 2.20462, "lb", 1), "g": (lambda x: x / 28.3495, "oz", 1),
        "°C": (lambda x: x * 9 / 5 + 32, "°F", 0), "K": (lambda x: x * 9 / 5, "°F (difference)", 0),
        "L": (lambda x: x * 0.264172, "US gal", 2), "cm³": (lambda x: x * 0.0610237, "in³", 1),
        "N·m": (lambda x: x * 0.737562, "lbf·ft", 1), "N": (lambda x: x * 0.224809, "lbf", 1),
        "m²": (lambda x: x * 10.7639, "ft²", 2), "Wh/kg": (lambda x: x / 2.20462, "Wh/lb", 0),
    }
    if u in conv:
        f, uu, d = conv[u]
        return f"{v:g} {u} [{f(v):,.{d}f} {uu}]"
    return f"{v:g} {u}".strip()


def money(x, cur="USD", dec=None):
    if x is None:
        return "—"
    sym = {"USD": "$", "EUR": "€", "GBP": "£"}.get(cur, "")
    if dec is None:
        dec = 2 if abs(x) < 100 else 0
    return f"{sym}{x:,.{dec}f}" if sym else f"{x:,.{dec}f} {cur}"


def rng(lo, hi, cur="USD"):
    if lo is None and hi is None:
        return "—"
    if hi is None or lo == hi:
        return money(lo, cur)
    return f"{money(lo, cur)}–{money(hi, cur)}"


def tag(b):
    b = (b or "").lower()
    return f'<span class="tag t-{E(b)}">{E(b or "untagged")}</span>'


def srcs(ids, S):
    if not ids:
        return ""
    ids = ids if isinstance(ids, list) else [ids]
    out = []
    for i in ids:
        s = S.get(i)
        out.append(f'<a class="src" href="#{E(i)}" title="{E(s["title"]) if s else "unknown source"}">{E(i)}</a>')
    return " ".join(out)


# ------------------------------------------------------------------ cost model
def tier_keys(cm):
    return [str(t) for t in cm.get("tiers", [1, 100, 1000, 10000])]


def line_cost(line, t):
    uc = line.get("unit_cost", {})
    v = uc.get(t)
    if v is None:
        return None
    return float(v) * float(line.get("qty_per_unit", 1))


def cost_tables(cm):
    tiers = tier_keys(cm)
    cats = []
    for c in cm.get("categories", []):
        tot = {t: sum((line_cost(l, t) or 0) for l in c.get("lines", [])) for t in tiers}
        cats.append((c["name"], tot))
    total = {t: sum(c[1][t] for c in cats) for t in tiers}
    return tiers, cats, total


def nre_per_unit(cm, tiers):
    """Spread NRE (tooling, certification) over the tier's volume, for information only."""
    out = {}
    for t in tiers:
        n = int(t)
        lo = sum(x.get("cost_low", 0) for x in cm.get("nre", []) if int(x.get("from_tier", 1)) <= n)
        hi = sum(x.get("cost_high", x.get("cost_low", 0)) for x in cm.get("nre", []) if int(x.get("from_tier", 1)) <= n)
        out[t] = (lo / n, hi / n)
    return out


# ------------------------------------------------------------------ charts (inline SVG, light print surface)
def chart_unit_cost(tiers, cats, total, cur):
    W, H, L, R, T, B = 760, 300, 70, 230, 18, 44
    pw, ph = W - L - R, H - T - B
    mx = max(total.values()) or 1
    step = 10 ** math.floor(math.log10(mx))
    for m in (1, 2, 2.5, 5, 10):
        if mx / (step * m) <= 6:
            step *= m
            break
    top = math.ceil(mx / step) * step
    y = lambda v: T + ph - ph * v / top
    bw = pw / len(tiers) * 0.46
    g = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="Unit cost by volume tier, stacked by cost category">']
    v = 0
    while v <= top + 1e-9:
        g.append(f'<line x1="{L}" x2="{L + pw}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="grid"/>'
                 f'<text x="{L - 8}" y="{y(v) + 4:.1f}" class="ax" text-anchor="end">{money(v, cur, 0)}</text>')
        v += step
    for i, t in enumerate(tiers):
        cx = L + pw / len(tiers) * (i + 0.5)
        acc = 0
        for k, (name, tot) in enumerate(cats):
            val = tot[t]
            if val <= 0:
                continue
            y0, y1 = y(acc), y(acc + val)
            h = max(0.0, y0 - y1 - 2)  # 2 px surface gap between stacked segments
            g.append(f'<rect x="{cx - bw / 2:.1f}" y="{y1 + 2:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="2" fill="{SERIES[k % 8]}">'
                     f'<title>{E(name)} at {int(t):,} units: {money(val, cur)} per unit</title></rect>')
            acc += val
        g.append(f'<text x="{cx:.1f}" y="{y(acc) - 6:.1f}" class="val" text-anchor="middle">{money(total[t], cur, 0)}</text>')
        g.append(f'<text x="{cx:.1f}" y="{T + ph + 18}" class="ax" text-anchor="middle">{int(t):,} unit{"s" if int(t) > 1 else ""}</text>')
    g.append(f'<text x="{L + pw / 2}" y="{H - 6}" class="ax" text-anchor="middle">Volume tier (units per production run)</text>')
    for k, (name, _) in enumerate(cats):
        ly = T + 6 + k * 20
        g.append(f'<rect x="{L + pw + 18}" y="{ly}" width="11" height="11" rx="2" fill="{SERIES[k % 8]}"/>'
                 f'<text x="{L + pw + 35}" y="{ly + 10}" class="lg">{E(name)}</text>')
    g.append("</svg>")
    return "".join(g)


def chart_timeline(stages, cur):
    W, L, R, rowh, T = 760, 300, 20, 30, 10
    H = T + rowh * len(stages) + 34
    total = sum(s.get("months_high", s.get("months_low", 0)) for s in stages) or 1
    pw = W - L - R
    x = lambda m: L + pw * m / total
    g = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="Stage timeline in months">']
    for m in range(0, int(math.ceil(total)) + 1, 3):
        g.append(f'<line x1="{x(m):.1f}" x2="{x(m):.1f}" y1="{T}" y2="{T + rowh * len(stages)}" class="grid"/>'
                 f'<text x="{x(m):.1f}" y="{T + rowh * len(stages) + 16}" class="ax" text-anchor="middle">{m}</text>')
    start_lo = start_hi = 0
    for i, s in enumerate(stages):
        lo, hi = s.get("months_low", 0), s.get("months_high", s.get("months_low", 0))
        yy = T + i * rowh + 6
        g.append(f'<text x="{L - 8}" y="{yy + 13}" class="lg" text-anchor="end">{E(s["id"])} {E(s["name"])}</text>')
        g.append(f'<rect x="{x(start_lo):.1f}" y="{yy}" width="{max(2, x(start_lo + lo) - x(start_lo)):.1f}" height="18" rx="3" fill="{SERIES[0]}">'
                 f'<title>{E(s["name"])}: {lo}–{hi} months, {rng(s.get("capital_low"), s.get("capital_high"), cur)}</title></rect>')
        if hi > lo:
            g.append(f'<rect x="{x(start_lo + lo):.1f}" y="{yy}" width="{x(start_lo + hi) - x(start_lo + lo):.1f}" height="18" rx="3" class="slack">'
                     f'<title>Possible overrun: up to {hi} months</title></rect>')
        start_lo += lo
        start_hi += hi
    g.append(f'<text x="{L + pw / 2}" y="{H - 2}" class="ax" text-anchor="middle">Months from start (solid: plan, hatched: possible overrun)</text></svg>')
    return "".join(g)


# ------------------------------------------------------------------ check
def check(P):
    errs, warns = [], []
    for k in REQUIRED:
        if not P.get(k):
            errs.append(f"section `{k}` is missing or empty")
    S = {s["id"] for s in P.get("sources", [])}

    def walk(o, path):
        if isinstance(o, dict):
            if "basis" in o:
                b = o["basis"]
                bs = b.values() if isinstance(b, dict) else [b]
                for x in bs:
                    if x not in BASES:
                        errs.append(f"{path}: basis `{x}` is not one of {', '.join(BASES)}")
                    if x in NEEDS_SOURCE and not o.get("source"):
                        errs.append(f"{path}: `{x}` figure has no source")
            for s in (o.get("source") if isinstance(o.get("source"), list) else [o.get("source")] if o.get("source") else []):
                if s not in S:
                    errs.append(f"{path}: source `{s}` is not in the sources list")
            for k, v in o.items():
                walk(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")

    walk(P, "$")
    cm = P.get("cost_model", {})
    tiers = tier_keys(cm)
    for c in cm.get("categories", []):
        for l in c.get("lines", []):
            if "basis" not in l:
                errs.append(f"cost line `{l.get('item')}` has no basis")
            for t in tiers:
                if l.get("unit_cost", {}).get(t) is None:
                    warns.append(f"cost line `{l.get('item')}` has no figure at {t} units")
    for x in cm.get("nre", []):
        if "basis" not in x:
            errs.append(f"NRE `{x.get('item')}` has no basis")
    for x in P.get("compliance", []):
        if "basis" not in x and x.get("cost_low") is not None:
            errs.append(f"compliance `{x.get('standard')}` cost has no basis")
    for s in P.get("stages", []):
        if "basis" not in s:
            errs.append(f"stage `{s.get('id')}` capital has no basis")
    st = P.get("status", {})
    if not st.get("on_paper"):
        warns.append("status.on_paper is empty: say plainly what has not been built or tested")
    return errs, warns


# ------------------------------------------------------------------ html
CSS = """
:root{--ink:#0b0b0b;--ink2:#52514e;--ink3:#7a7974;--line:#dedcd6;--soft:#f4f3ef;--surface:#fcfcfb;--accent:#2a78d6;
--good:#0a7d32;--warn:#a65f00;--bad:#b42318}
*{box-sizing:border-box}html{background:var(--surface)}
body{margin:0;background:var(--surface);color:var(--ink);font:14px/1.5 "Segoe UI",system-ui,-apple-system,Roboto,Arial,sans-serif}
main{max-width:980px;margin:0 auto;padding:28px 16px 60px}
h1{font-size:30px;line-height:1.15;margin:6px 0 4px}h2{font-size:20px;margin:34px 0 10px;padding-top:12px;border-top:2px solid var(--ink)}
h3{font-size:15px;margin:18px 0 6px}p{margin:6px 0 10px}small,.muted{color:var(--ink2)}
.cover{border-bottom:1px solid var(--line);padding-bottom:16px;margin-bottom:8px}
.kicker{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink2)}
.meta{display:flex;flex-wrap:wrap;gap:6px 22px;font-size:13px;color:var(--ink2);margin-top:8px}
.notice{border:1px solid var(--line);border-left:4px solid var(--warn);background:var(--soft);padding:10px 14px;border-radius:6px;margin:14px 0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:14px 0}
.kpi{border:1px solid var(--line);border-radius:8px;padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:20px;line-height:1.2}.kpi span{font-size:12px;color:var(--ink2)}
table{width:100%;border-collapse:collapse;margin:8px 0 14px;font-size:13px}
th,td{text-align:left;vertical-align:top;padding:6px 8px;border-bottom:1px solid var(--line)}
th{font-size:12px;color:var(--ink2);font-weight:600;background:var(--soft)}
td.id{white-space:nowrap}td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tr.tot td{font-weight:700;border-top:2px solid var(--ink)}
.wrap{overflow-x:auto}
.tag{display:inline-block;font-size:10.5px;line-height:1;padding:3px 5px;border-radius:4px;border:1px solid var(--line);color:var(--ink2);white-space:nowrap;vertical-align:1px}
.t-measured,.t-observed{border-color:#9fd3b0;color:var(--good)}.t-quoted,.t-documented{border-color:#a9c7ee;color:#1d5fae}
.t-estimate{border-color:#f0c98a;color:var(--warn)}.t-assumed{border-color:#e9b4b0;color:var(--bad)}
a.src{font-size:11px;color:var(--accent);text-decoration:none;vertical-align:1px}
.chart{width:100%;height:auto;display:block;margin:6px 0 4px}
.chart .grid{stroke:#e6e4de;stroke-width:1}.chart .ax{font-size:11px;fill:var(--ink2)}.chart .val{font-size:12px;font-weight:700;fill:var(--ink)}
.chart .lg{font-size:12px;fill:var(--ink)}.chart .slack{fill:url(#none);fill:#2a78d633;stroke:#2a78d6;stroke-dasharray:3 2}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;border:1px solid var(--line)}
.ok{color:var(--good)}.no{color:var(--bad)}
ol.toc{columns:2;font-size:13px;padding-left:18px}ol.toc a{color:var(--ink);text-decoration:none}
.legend{font-size:12px;color:var(--ink2)}
footer{margin-top:40px;font-size:12px;color:var(--ink2);border-top:1px solid var(--line);padding-top:10px}
@media (max-width:700px){.two{grid-template-columns:1fr}ol.toc{columns:1}h1{font-size:24px}}
@media print{@page{size:Letter;margin:14mm 13mm}html,body{background:#fff}body{font-size:10.5pt}main{max-width:none;padding:0}
h2{break-after:avoid}h2.page{break-before:page;border-top:0;padding-top:0}h3{break-after:avoid}table,.chart,.kpi{break-inside:avoid}
a{color:inherit}.noprint{display:none}}
"""


def table(head, rows, num=(), nowrap=()):
    cls = lambda i: " ".join(c for c, on in (("n", i in num), ("id", i in nowrap and i not in num)) if on)
    h = "".join(f'<th class="{"n" if i in num else ""}">{E(c)}</th>' for i, c in enumerate(head))
    b = "".join("<tr>" + "".join(f'<td class="{cls(i)}">{c}</td>' for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f'<div class="wrap"><table><tr>{h}</tr>{b}</table></div>'


def render_html(P):
    cur = P.get("currency", "USD")
    S = {s["id"]: s for s in P.get("sources", [])}
    cm = P["cost_model"]
    tiers, cats, total = cost_tables(cm)
    nre = nre_per_unit(cm, tiers)
    ex = P["executive_summary"]
    out = []
    a = out.append
    sections = [("summary", "Executive summary"), ("problem", "Problem and market"), ("product", "Product and specifications"),
                ("status", "Design and verification status"), ("cost", "Cost at volume"), ("dfm", "Design changes for volume (DFM/DFA)"),
                ("supply", "Supply chain"), ("compliance", "Certification and compliance"), ("partners", "Manufacturing partners and processes"),
                ("risks", "Risks"), ("plan", "Stages, timeline and capital"), ("ip", "IP and legal notes"),
                ("assumptions", "Assumptions and open questions"), ("sources", "Sources")]
    a(f'<header class="cover"><div class="kicker">Engineering and Manufacturing Summary · prototype to production</div>'
      f'<h1>{E(P["title"])}</h1><p class="muted">{E(ex.get("one_liner", ""))}</p>'
      f'<div class="meta"><span>Revision {E(P.get("revision", ""))}</span><span>Dated {E(P.get("date", ""))}</span>'
      f'<span>Prepared by {E(P.get("prepared_by", "Anatomy"))}</span><span>Currency {E(cur)}{(" · " + E(P["fx"]["note"])) if P.get("fx") else ""}</span></div></header>')
    a(f'<div class="notice"><b>How to read this document.</b> {E(P.get("audience_note", ""))} Every figure carries a tag: '
      f'{tag("measured")} or {tag("observed")} seen on this project, {tag("quoted")} a written price or quote, {tag("documented")} a published source, '
      f'{tag("estimate")} a reasoned estimate with its method stated, {tag("assumed")} a placeholder that must be replaced before it is relied on. '
      f'Source IDs (S-1 …) link to the list at the end. This is not an offer of securities, a quotation, or legal advice.</div>')
    a('<ol class="toc noprint">' + "".join(f'<li><a href="#{k}">{E(n)}</a></li>' for k, n in sections) + "</ol>")

    # 1 summary
    a('<h2 id="summary">1. Executive summary</h2>')
    for p in ex.get("paragraphs", []):
        a(f"<p>{E(p)}</p>")
    if ex.get("key_numbers"):
        a('<div class="kpis">' + "".join(f'<div class="kpi"><b>{E(k["value"])}</b><span>{E(k["label"])} {tag(k.get("basis"))} {srcs(k.get("source"), S)}</span></div>' for k in ex["key_numbers"]) + "</div>")
    if ex.get("asks"):
        a("<h3>What this project is looking for</h3><ul>" + "".join(f"<li>{E(x)}</li>" for x in ex["asks"]) + "</ul>")

    # 2 problem
    pr = P["problem"]
    a('<h2 id="problem">2. Problem and market</h2>')
    for p in pr.get("paragraphs", [pr.get("text", "")]):
        a(f"<p>{E(p)}</p>")
    if pr.get("evidence"):
        a(table(["Claim", "Basis", "Source"], [[E(x["claim"]), tag(x.get("basis")), srcs(x.get("source"), S)] for x in pr["evidence"]]))
    if pr.get("not_known"):
        a("<h3>Not yet established</h3><ul>" + "".join(f"<li>{E(x)}</li>" for x in pr["not_known"]) + "</ul>")

    # 3 product
    pd = P["product"]
    a('<h2 id="product">3. Product and specifications</h2>')
    a(f'<p>{E(pd.get("description", ""))}</p>')
    a(table(["Specification", "Value", "Basis", "Source"],
            [[E(s["name"]), E(dual(s.get("v"), s.get("u", "")) if "v" in s else s.get("value", "")), tag(s.get("basis")), srcs(s.get("source"), S)] for s in pd.get("specs", [])]))

    # 4 status
    st = P["status"]
    a('<h2 id="status">4. Design and verification status</h2>')
    for k in ("trl", "mrl"):
        if st.get(k):
            nm = "Technology readiness (TRL)" if k == "trl" else "Manufacturing readiness (MRL)"
            a(f'<p><b>{nm}: {E(st[k]["level"])}</b> {tag(st[k].get("basis", "estimate"))} {E(st[k].get("why", ""))}</p>')
    a('<div class="two"><div><h3 class="ok">Verified (done and checked)</h3>' +
      table(["Item", "How it was checked"], [[E(x["item"]), E(x.get("how", "")) + " " + tag(x.get("basis", "observed"))] for x in st.get("verified", [])]) +
      '</div><div><h3 class="no">On paper only (not built or not tested)</h3>' +
      table(["Item", "Closed in"], [[E(x["item"]) + (f'<div class="muted">{E(x["why"])}</div>' if x.get("why") else ""), E(x.get("closes_in", ""))] for x in st.get("on_paper", [])]) +
      "</div></div>")

    # 5 cost
    a('<h2 id="cost" class="page">5. Cost at volume</h2>')
    a(f'<p>{E(cm.get("intro", ""))}</p>')
    a(chart_unit_cost(tiers, cats, total, cur))
    a('<p class="legend">Per-unit cost of goods (parts, sub-assemblies, labour and end-of-line test) at each volume tier. Hover a bar segment for its value. '
      'One-time costs (tooling, certification) are not in the bars; they are listed below and spread per unit in the last row.</p>')
    rows = [[E(n)] + [money(tot[t], cur) for t in tiers] for n, tot in cats]
    rows.append([f"<b>Unit cost of goods</b>"] + [f"<b>{money(total[t], cur)}</b>" for t in tiers])
    rows.append(['<span class="muted">One-time costs spread over the run (low–high)</span>'] + [f'<span class="muted">{rng(*nre[t], cur)}</span>' for t in tiers])
    a(table(["Category"] + [f"{int(t):,} unit{'s' if int(t) > 1 else ''}" for t in tiers], rows, num=tuple(range(1, len(tiers) + 1))))
    if cm.get("price_context"):
        a("<h3>Price context</h3>" + table(["Reference", "Price", "Basis", "Source"],
                                           [[E(x["item"]), E(x.get("price", "")), tag(x.get("basis")), srcs(x.get("source"), S)] for x in cm["price_context"]]))
    a("<h3>Cost lines</h3>")
    lr = []
    for c in cm.get("categories", []):
        for l in c.get("lines", []):
            b = l.get("basis")
            btxt = " ".join(f"{tag(v)}<small>@{k}</small>" for k, v in b.items()) if isinstance(b, dict) else tag(b)
            lr.append([f'<b>{E(l["item"])}</b><div class="muted">{E(l.get("note", ""))}</div>', E(l.get("qty_per_unit", 1))] +
                      [money(l.get("unit_cost", {}).get(t), cur) for t in tiers] + [btxt + " " + srcs(l.get("source"), S)])
    a(table(["Item", "Qty"] + [f"{int(t):,}" for t in tiers] + ["Basis"], lr, num=tuple(range(1, len(tiers) + 2))))
    if cm.get("nre"):
        a("<h3>One-time costs (NRE)</h3>" + table(["Item", "Needed from", "Cost", "Basis", "Source"],
              [[E(x["item"]) + (f'<div class="muted">{E(x["note"])}</div>' if x.get("note") else ""), f'{int(x.get("from_tier", 1)):,} units',
                rng(x.get("cost_low"), x.get("cost_high"), cur), tag(x.get("basis")), srcs(x.get("source"), S)] for x in cm["nre"]], num=(2,)))

    # 6 DFM
    a('<h2 id="dfm">6. Design changes for volume (DFM/DFA)</h2>')
    a(table(["Part or area", "Prototype", "Production", "Change needed", "Tooling", "From", "Basis"],
            [[f'<b>{E(x["part"])}</b>', E(x.get("prototype", "")), E(x.get("production", "")), E(x.get("change", "")),
              rng(x.get("tooling_low"), x.get("tooling_high"), cur), f'{int(x.get("from_tier", 1)):,}', tag(x.get("basis")) + " " + srcs(x.get("source"), S)] for x in P["dfm"]], num=(4, 5)))

    # 7 supply
    a('<h2 id="supply">7. Supply chain</h2>')
    a(table(["Item", "Prototype source", "Volume source and alternates", "Lead time", "Risk"],
            [[f'<b>{E(x["item"])}</b>', E(x.get("prototype", "")), E(x.get("volume", "")) + (f'<div class="muted">Alternates: {E(", ".join(x["alternates"]))}</div>' if x.get("alternates") else ""),
              E(x.get("lead_time", "")), E(x.get("risk", ""))] for x in P["supply_chain"]]))

    # 8 compliance
    a('<h2 id="compliance">8. Certification and compliance</h2>')
    a(table(["Standard or rule", "Needed for", "Required and status", "Cost", "Time", "Basis"],
            [[f'<b>{E(x["standard"])}</b><div class="muted">{E(x.get("scope", ""))}</div>', E(x.get("markets", "")),
              E(x.get("required", "")) + f'<div class="muted">{E(x.get("status", ""))}</div>',
              rng(x.get("cost_low"), x.get("cost_high"), cur), E(x.get("time", "")), tag(x.get("basis")) + " " + srcs(x.get("source"), S)] for x in P["compliance"]], num=(3,)))

    # 9 partners
    a('<h2 id="partners">9. Manufacturing partners and processes</h2>')
    a(table(["Process", "Prototype", "Pilot and volume candidates", "Notes"],
            [[f'<b>{E(x["process"])}</b>', E(x.get("prototype", "")), E(", ".join(x.get("candidates", []))), E(x.get("note", ""))] for x in P["partners"]]))
    if P.get("partners_note"):
        a(f'<p class="muted">{E(P["partners_note"])}</p>')

    # 10 risks
    a('<h2 id="risks">10. Risks</h2>')
    a(table(["Risk", "Likelihood", "Impact", "Mitigation", "Retired in"],
            [[f'<b>{E(x["risk"])}</b>', E(x.get("likelihood", "")), E(x.get("impact", "")), E(x.get("mitigation", "")), E(x.get("stage", ""))] for x in P["risks"]]))

    # 11 plan
    stg = P["stages"]
    a('<h2 id="plan" class="page">11. Stages, timeline and capital</h2>')
    a(chart_timeline(stg, cur))
    a(table(["Stage", "Goal and exit criteria", "Units", "Months", "Capital", "Basis"],
            [[f'<b>{E(s["id"])} {E(s["name"])}</b>', E(s.get("goal", "")) + ("<ul>" + "".join(f"<li>{E(c)}</li>" for c in s.get("exit", [])) + "</ul>" if s.get("exit") else "") +
              (f'<div class="muted">Includes: {E("; ".join(s["includes"]))}</div>' if s.get("includes") else ""),
              E(s.get("units", "")), f'{s.get("months_low", "")}–{s.get("months_high", "")}', rng(s.get("capital_low"), s.get("capital_high"), cur), tag(s.get("basis"))] for s in stg],
            num=(2, 3, 4)))
    clo = sum(s.get("capital_low", 0) for s in stg)
    chi = sum(s.get("capital_high", 0) for s in stg)
    mlo = sum(s.get("months_low", 0) for s in stg)
    mhi = sum(s.get("months_high", 0) for s in stg)
    a(f'<p><b>Total to first volume production: {rng(clo, chi, cur)} over {mlo}–{mhi} months</b> {tag("estimate")}. '
      f'{E(P.get("capital_note", ""))}</p>')

    # 12 IP
    a('<h2 id="ip">12. IP and legal notes</h2><p class="muted">Not legal advice. Points to take to a qualified attorney.</p>')
    a(table(["Topic", "Note"], [[f'<b>{E(x["topic"])}</b>', E(x["note"])] for x in P["ip"]]))

    # 13 assumptions
    a('<h2 id="assumptions">13. Assumptions and open questions</h2>')
    a(table(["ID", "Assumption"], [[E(x["id"]), E(x["text"])] for x in P["assumptions"]], nowrap=(0,)))
    if P.get("open_questions"):
        a("<h3>Open questions</h3><ol>" + "".join(f"<li>{E(q)}</li>" for q in P["open_questions"]) + "</ol>")

    # 14 sources
    a('<h2 id="sources">14. Sources</h2>')
    a(table(["ID", "Source", "Accessed"], [[f'<span id="{E(s["id"])}">{E(s["id"])}</span>',
            (f'<a href="{E(s["url"])}">{E(s["title"])}</a>' if s.get("url") else E(s["title"])) + (f'<div class="muted">{E(s["note"])}</div>' if s.get("note") else ""),
            E(s.get("accessed", ""))] for s in P["sources"]], nowrap=(0, 2)))
    a(f'<footer>Generated by the Anatomy skill (tools/production/make_brief.py) from production/production.json on {date.today().isoformat()}. '
      f'Re-run it after any design, price or plan change; the figures above are only as current as their sources.</footer>')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(P.get("short_title", P["title"]))}</title><style>{CSS}</style></head><body><main>{"".join(out)}</main></body></html>')


# ------------------------------------------------------------------ markdown + csv
def render_md(P):
    cur = P.get("currency", "USD")
    cm = P["cost_model"]
    tiers, cats, total = cost_tables(cm)
    L = [f"# {P['title']}", "", f"Engineering and Manufacturing Summary, revision {P.get('revision', '')}, {P.get('date', '')}", "",
         "Tags: measured/observed, quoted, documented, estimate, assumed. Full tables, charts and sources are in production-brief.html.", "",
         "## Executive summary", ""] + [p + "\n" for p in P["executive_summary"].get("paragraphs", [])]
    L += ["## Unit cost of goods by tier", "", "| Category | " + " | ".join(f"{int(t):,}" for t in tiers) + " |", "|---|" + "---:|" * len(tiers)]
    for n, tot in cats:
        L.append(f"| {n} | " + " | ".join(money(tot[t], cur) for t in tiers) + " |")
    L.append("| **Total** | " + " | ".join(f"**{money(total[t], cur)}**" for t in tiers) + " |")
    L += ["", "## Verification status", "", "Verified:"] + [f"- {x['item']}: {x.get('how', '')}" for x in P["status"].get("verified", [])]
    L += ["", "On paper only:"] + [f"- {x['item']} (closes in {x.get('closes_in', '?')})" for x in P["status"].get("on_paper", [])]
    L += ["", "## Stages", "", "| Stage | Months | Capital | Basis |", "|---|---|---|---|"]
    for s in P["stages"]:
        L.append(f"| {s['id']} {s['name']} | {s.get('months_low')}–{s.get('months_high')} | {rng(s.get('capital_low'), s.get('capital_high'), cur)} | {s.get('basis')} |")
    L += ["", "## Compliance", ""] + [f"- **{x['standard']}** ({x.get('required', '')}): {x.get('status', '')}; {rng(x.get('cost_low'), x.get('cost_high'), cur)}, {x.get('time', '')} [{x.get('basis', '')}]" for x in P["compliance"]]
    L += ["", "## Risks", ""] + [f"- {x['risk']}: {x.get('mitigation', '')}" for x in P["risks"]]
    L += ["", "## Sources", ""] + [f"- {s['id']}: {s['title']} {s.get('url', '')}" for s in P["sources"]]
    return "\n".join(L) + "\n"


def write_csv(P, path):
    cm = P["cost_model"]
    tiers = tier_keys(cm)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["category", "item", "qty_per_unit"] + [f"unit_cost_{t}" for t in tiers] + [f"line_cost_{t}" for t in tiers] + ["basis", "source", "note"])
        for c in cm.get("categories", []):
            for l in c.get("lines", []):
                b = l.get("basis")
                w.writerow([c["name"], l["item"], l.get("qty_per_unit", 1)] + [l.get("unit_cost", {}).get(t, "") for t in tiers] +
                           [("" if line_cost(l, t) is None else round(line_cost(l, t), 2)) for t in tiers] +
                           [json.dumps(b) if isinstance(b, dict) else b, ";".join(l["source"]) if isinstance(l.get("source"), list) else l.get("source", ""), l.get("note", "")])


# ------------------------------------------------------------------ pdf
def find_browser():
    cands = [os.environ.get("ANATOMY_BROWSER", ""), "/opt/pw-browsers/chromium",
             r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
             r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]
    for c in cands:
        if c and Path(c).is_file():
            return c
    for n in ("chromium", "chromium-browser", "google-chrome", "msedge", "chrome"):
        p = shutil.which(n)
        if p:
            return p
    return None


def to_pdf(html_path, pdf_path):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.goto(Path(html_path).resolve().as_uri())
            pg.pdf(path=str(pdf_path), format="Letter", print_background=True,
                   margin={"top": "14mm", "bottom": "16mm", "left": "13mm", "right": "13mm"},
                   display_header_footer=True, header_template="<span></span>",
                   footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#777">'
                                   '<span class="title"></span> · page <span class="pageNumber"></span> of <span class="totalPages"></span></div>')
            b.close()
        return "playwright"
    except Exception:
        pass
    if shutil.which("node"):
        # Node playwright (pre-installed on some machines); same page settings as above.
        js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();"
              "await p.goto(process.argv[1]);await p.pdf({path:process.argv[2],format:'Letter',printBackground:true,"
              "margin:{top:'14mm',bottom:'16mm',left:'13mm',right:'13mm'},displayHeaderFooter:true,headerTemplate:'<span></span>',"
              "footerTemplate:'<div style=\"font-size:8px;width:100%;text-align:center;color:#777\"><span class=\"title\"></span> \u00b7 page "
              "<span class=\"pageNumber\"></span> of <span class=\"totalPages\"></span></div>'});await b.close();})()"
              ".catch(e=>{console.error(e);process.exit(1)})")
        try:
            r = subprocess.run(["node", "-e", js, Path(html_path).resolve().as_uri(), str(Path(pdf_path).resolve())],
                               capture_output=True, timeout=120)
            if r.returncode == 0 and Path(pdf_path).is_file():
                return "playwright"
        except Exception:
            pass
    br = find_browser()
    if not br:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        try:
            subprocess.run([br, "--headless", "--no-sandbox", "--disable-gpu", f"--user-data-dir={tmp}", "--no-pdf-header-footer",
                            f"--print-to-pdf={Path(pdf_path).resolve()}", Path(html_path).resolve().as_uri()],
                           capture_output=True, timeout=120)
        except subprocess.TimeoutExpired:
            return None
    return br if Path(pdf_path).is_file() else None


# ------------------------------------------------------------------ main
def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    src = Path(argv[0])
    pj = src if src.suffix == ".json" else src / "production" / "production.json"
    if not pj.is_file():
        print(f"not found: {pj}")
        return 2
    P = json.loads(pj.read_text(encoding="utf-8"))
    out = pj.parent
    errs, warns = check(P)
    rep = [f"# Production brief check", "", f"Source: `{pj.name}`, revision {P.get('revision', '')}", "",
           f"Result: **{'PASS' if not errs else 'FAIL'}** ({len(errs)} errors, {len(warns)} warnings)", ""]
    rep += ["## Errors", ""] + [f"- {e}" for e in errs] + [""] if errs else []
    rep += ["## Warnings", ""] + [f"- {w}" for w in warns] + [""] if warns else []
    tags = {}

    def count(o):
        if isinstance(o, dict):
            b = o.get("basis")
            for x in (b.values() if isinstance(b, dict) else [b] if b else []):
                tags[x] = tags.get(x, 0) + 1
            for v in o.values():
                count(v)
        elif isinstance(o, list):
            for v in o:
                count(v)

    count(P)
    rep += ["## Figures by basis", ""] + [f"- {k}: {v}" for k, v in sorted(tags.items(), key=lambda kv: BASES.index(kv[0]) if kv[0] in BASES else 99)]
    if errs:
        (out / "brief-check.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
        print("\n".join(rep))
        return 1
    html_path = out / "production-brief.html"
    html_path.write_text(render_html(P), encoding="utf-8")
    (out / "production-brief.md").write_text(render_md(P), encoding="utf-8")
    write_csv(P, out / "cost-model.csv")
    pdf = None
    if "--no-pdf" not in argv:
        pdf = to_pdf(html_path, out / "production-brief.pdf")
    rep += ["", "## Outputs", "", "- production-brief.html", "- production-brief.md", "- cost-model.csv",
            f"- production-brief.pdf ({'rendered with ' + Path(pdf).name if pdf and pdf != 'playwright' else 'rendered with playwright' if pdf else 'NOT rendered: no Chromium, Chrome or Edge found; open the HTML and print to PDF'})"]
    (out / "brief-check.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print("\n".join(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

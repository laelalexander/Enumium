"""Plant-floor web UI and JSON API for the MES. Standard library only.

Run:  python3 -m dhmes.server --db plant.db --site ../../data/site.json --port 8080
      python3 -m dhmes.server --blender P1-301 --db p1.db          (Phase 1 prototype with the bin ring)
Panel PCs (WS-207) and the weigh terminals open http://<mes-server>:8080 in a browser.

API (POST JSON, each body carries "by": operator badge):
  /api/receive        {ingredient, supplier, supplier_lot, kg, expires, coa_ok}
  /api/lot/release    {lot}
  /api/batch          {formula, target_kg}
  /api/dispense       {batch, ingredient, lot, actual_kg, scale}
  /api/blend_complete {batch, bag_kg, md_rejects}
  /api/qc             {batch, tracer_pct:[...], micro_ok}
  /api/run            {sku, bag, line, units}
  /api/label_check    {run, upc, lot}
  /api/weights        {run, gross_g:[...]}
  /api/run/end        {run, good, rej_weight, rej_vision}
  /api/pallet         {run, cases}
  /api/bin/assign     {bin, ingredient, capacity_kg}          (Phase 1)
  /api/bin/refill     {bin, lot, kg}                          (Phase 1, operator scans the bag lot)
  /api/bin/empty      {bin}                                   (Phase 1, low-level switch confirmed)
  /api/dose           {batch, bin, actual_kg}                 (Phase 1, posted by the dosing PLC)
GET: /api/bins, /api/bin/<id>, /api/batch/<id>/doselist, /api/batch/<id>/picklist, /api/batch/<id>/plc, /api/batch/<id>/record,
     /api/run/<id>/plc, /api/run/<id>/hb133, /api/run/<id>/case_label,
     /api/trace/back/<lot>, /api/trace/forward/<rm lot>, /api/sequence?f=a,b,c
"""
from __future__ import annotations

import argparse
import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .core import MES, MESError

CSS = """body{font:15px system-ui,sans-serif;margin:0;background:#f5f6f7;color:#1b1f23}
header{background:#3e2723;color:#fff;padding:12px 20px;font-size:20px}main{padding:16px 20px;display:grid;gap:16px;
grid-template-columns:repeat(auto-fit,minmax(420px,1fr))}section{background:#fff;border:1px solid #dde;border-radius:8px;padding:12px}
h2{font-size:16px;margin:0 0 8px}table{border-collapse:collapse;width:100%;font-size:13px}td,th{border-bottom:1px solid #eee;
padding:4px 6px;text-align:left}.RELEASED{color:#1b5e20;font-weight:600}.QC_HOLD,.QUARANTINE,.WAIT_LABEL_CHECK{color:#e65100;font-weight:600}
.REJECTED{color:#b71c1c;font-weight:700}"""


def table(rows, cols):
    head = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
    body = "".join("<tr>" + "".join(f'<td class="{html.escape(str(r.get(c, "")))}">{html.escape(str(r.get(c, "")))}</td>' for c in cols) + "</tr>" for r in rows)
    return f"<table><tr>{head}</tr>{body}</table>"


def make_handler(mes: MES):
    class H(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="application/json"):
            data = body.encode() if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _json(self, obj, code=200):
            self._send(code, json.dumps(obj, indent=1, default=str))

        def log_message(self, *a):
            pass

        def do_GET(self):
            u = urlparse(self.path)
            p = [x for x in u.path.split("/") if x]
            try:
                if not p:
                    return self._send(200, self.dashboard(), "text/html; charset=utf-8")
                if p == ["api", "bins"]:
                    return self._json([mes.bin(r["id"]) for r in mes.q("SELECT id FROM bin ORDER BY id")])
                if p[:2] == ["api", "bin"] and len(p) == 3:
                    return self._json(mes.bin(p[2]))
                if p[:2] == ["api", "batch"] and len(p) == 4:
                    fn = {"doselist": mes.dose_list, "picklist": mes.pick_list, "plc": mes.plc_download, "record": mes.batch_record}[p[3]]
                    return self._json(fn(p[2]))
                if p[:2] == ["api", "run"] and len(p) == 4:
                    if p[3] == "case_label":
                        return self._send(200, mes.case_label(p[2]), "text/plain")
                    fn = {"plc": lambda r: mes.plc_job(r, 80), "hb133": mes.hb133_check}[p[3]]
                    return self._json(fn(p[2]))
                if p[:2] == ["api", "trace"] and len(p) == 4:
                    return self._json(mes.trace_back(p[3]) if p[2] == "back" else mes.trace_forward(p[3]))
                if p == ["api", "sequence"]:
                    return self._json(mes.allergen_sequence(parse_qs(u.query).get("f", [""])[0].split(",")))
                return self._json({"error": "not found"}, 404)
            except (MESError, KeyError) as e:
                return self._json({"error": str(e)}, 400)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            b = json.loads(self.rfile.read(n) or b"{}")
            by = b.get("by")
            if not by:
                return self._json({"error": "every action needs an operator badge in 'by'"}, 400)
            r = {
                "/api/receive": lambda: mes.receive(b["ingredient"], b["supplier"], b["supplier_lot"], b["kg"], b.get("expires"), b["coa_ok"], by),
                "/api/lot/release": lambda: mes.release_lot(b["lot"], by),
                "/api/batch": lambda: mes.create_batch(b["formula"], b["target_kg"], by),
                "/api/dispense": lambda: mes.dispense(b["batch"], b["ingredient"], b["lot"], b["actual_kg"], b.get("scale", "WS-201"), by),
                "/api/blend_complete": lambda: mes.blend_complete(b["batch"], b["bag_kg"], b["md_rejects"], by),
                "/api/qc": lambda: mes.qc_result(b["batch"], b["tracer_pct"], b["micro_ok"], by),
                "/api/run": lambda: mes.start_run(b["sku"], b["bag"], b["line"], b["units"], by),
                "/api/label_check": lambda: mes.label_check(b["run"], b["upc"], b["lot"], by),
                "/api/weights": lambda: mes.record_weights(b["run"], b["gross_g"]),
                "/api/run/end": lambda: mes.end_run(b["run"], b["good"], b["rej_weight"], b["rej_vision"], by),
                "/api/pallet": lambda: mes.build_pallet(b["run"], b["cases"], by),
                "/api/bin/assign": lambda: mes.assign_bin(b["bin"], b["ingredient"], b["capacity_kg"], by),
                "/api/bin/refill": lambda: mes.refill_bin(b["bin"], b["lot"], b["kg"], by),
                "/api/bin/empty": lambda: mes.bin_empty(b["bin"], by),
                "/api/dose": lambda: mes.record_dose(b["batch"], b["bin"], b["actual_kg"], by),
            }.get(urlparse(self.path).path)
            if not r:
                return self._json({"error": "not found"}, 404)
            try:
                return self._json({"ok": True, "result": r()})
            except (MESError, KeyError) as e:
                return self._json({"ok": False, "error": str(e)}, 400)

        def dashboard(self):
            lots = mes.q("SELECT id, ingredient, supplier_lot, kg_left, expires, status FROM lot ORDER BY received DESC LIMIT 30")
            batches = mes.q("SELECT id, formula, target_kg, status, cv_pct, md_rejects, bag FROM batch ORDER BY created DESC LIMIT 30")
            runs = mes.q("SELECT id, sku, batch, line, status, good, rej_weight, rej_vision FROM pack_run ORDER BY started DESC LIMIT 30")
            audit = mes.q("SELECT at, by, kind, ref FROM audit ORDER BY seq DESC LIMIT 25")
            bins = mes.q("SELECT b.id, b.ingredient, ROUND(b.kg, 1) AS kg, b.capacity_kg, ROUND(100 * b.kg / b.capacity_kg) AS pct_full, "
                         "(SELECT COUNT(DISTINCT lot) FROM bin_lot l WHERE l.bin=b.id AND l.cycle=b.cycle) AS lots_in_bin, b.emptied "
                         "FROM bin b ORDER BY b.id")
            bin_sec = (f'<section><h2>Ingredient bins ({mes.blender})</h2>'
                       f'{table(bins, ["id", "ingredient", "kg", "capacity_kg", "pct_full", "lots_in_bin", "emptied"])}</section>') if bins else ""
            return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="10"><title>Down Home Creole MES</title><style>{CSS}</style></head><body>
<header>Down Home Creole · Plant MES</header><main>
<section><h2>Blend batches</h2>{table(batches, ["id", "formula", "target_kg", "status", "cv_pct", "md_rejects", "bag"])}</section>
<section><h2>Pack runs</h2>{table(runs, ["id", "sku", "batch", "line", "status", "good", "rej_weight", "rej_vision"])}</section>
{bin_sec}<section><h2>Ingredient lots</h2>{table(lots, ["id", "ingredient", "supplier_lot", "kg_left", "expires", "status"])}</section>
<section><h2>Audit trail</h2>{table(audit, ["at", "by", "kind", "ref"])}</section></main></body></html>"""

    return H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="plant.db")
    ap.add_argument("--site", default=str(Path(__file__).resolve().parents[3] / "data" / "site.json"))
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--blender", default="RB-303", help="RB-303 (Growth plant) or P1-301 (Phase 1 prototype with bins)")
    a = ap.parse_args()
    mes = MES(a.db, blender=a.blender)
    if not mes.q("SELECT id FROM formula LIMIT 1"):
        mes.load_site(json.loads(Path(a.site).read_text()))
    print(f"MES on http://0.0.0.0:{a.port}")
    ThreadingHTTPServer(("0.0.0.0", a.port), make_handler(mes)).serve_forever()


if __name__ == "__main__":
    main()

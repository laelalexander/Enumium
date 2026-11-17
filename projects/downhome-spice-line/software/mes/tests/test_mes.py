"""End-to-end MES tests: receive -> dispense -> blend -> QC -> pack -> pallet -> trace.
Run from software/mes:  python3 -m unittest -v
"""
import datetime as dt
import json
import threading
import unittest
import urllib.request
from pathlib import Path

from dhmes import MES, MESError, gs1
from dhmes.server import ThreadingHTTPServer, make_handler

SITE = json.loads((Path(__file__).resolve().parents[3] / "data" / "site.json").read_text())


def stocked(mes, formula):
    lots = {}
    for l in mes.formula(formula)["lines"]:
        lots[l["ingredient"]] = mes.receive(l["ingredient"], "ACME", "S-1", 2000, "2099-01-01", True, "rcv1")
    return lots


def dispense_all(mes, bid, lots):
    for p in mes.pick_list(bid):
        mes.dispense(bid, p["ingredient"], lots[p["ingredient"]], p["target_kg"], "WS-201", "op1")


class GS1(unittest.TestCase):
    def test_check_digits(self):
        self.assertEqual(gs1.check_digit("03600029145"), "2")          # known UPC 036000291452
        self.assertEqual(gs1.check_digit("10614141123456789"), "7")  # GS1 General Specifications SSCC example 106141411234567897
        self.assertEqual(len(gs1.sscc(1)), 18)
        self.assertEqual(gs1.gtin14("036000291452"), "10036000291459")

    def test_lot_and_best_by(self):
        self.assertEqual(gs1.lot_code(dt.date(2027, 3, 8), 3), "DH27067-B03")
        self.assertEqual(gs1.best_by(dt.date(2027, 3, 8)), dt.date(2029, 3, 8))
        self.assertEqual(gs1.best_by(dt.date(2028, 2, 29)), dt.date(2030, 2, 28))

    def test_zpl_has_fnc1_after_lot_only_between_fields(self):
        z = gs1.case_label_zpl("X", "s", "10036000291459", "DH27067-B03", dt.date(2029, 3, 8), 12, "4 oz")
        self.assertIn(">;>8011003600029145915290308" + "10DH27067-B03", z)
        self.assertNotIn("B03>8", z)


class Flow(unittest.TestCase):
    def setUp(self):
        self.m = MES()
        self.m.load_site(SITE)

    def test_capacity_rule(self):
        cap = self.m.max_batch_kg("f-orig")
        self.assertEqual(cap, int(36 * 28.3168 * 0.548))
        with self.assertRaises(MESError):
            self.m.create_batch("f-orig", cap + 1, "op1")
        with self.assertRaises(MESError):
            self.m.create_batch("f-orig", 50, "op1")

    def test_wrong_lot_quarantine_and_tolerance(self):
        lots = stocked(self.m, "f-orig")
        bid = self.m.create_batch("f-orig", 500, "op1")
        with self.assertRaises(MESError):   # paprika lot used for garlic
            self.m.dispense(bid, "garlic", lots["paprika"], 55, "WS-201", "op1")
        q = self.m.receive("garlic", "ACME", "S-2", 100, "2099-01-01", False, "rcv1")
        with self.assertRaises(MESError):   # quarantined
            self.m.dispense(bid, "garlic", q, 55, "WS-201", "op1")
        with self.assertRaises(MESError):   # out of tolerance
            self.m.dispense(bid, "garlic", lots["garlic"], 56, "WS-201", "op1")

    def test_full_flow_and_trace(self):
        lots = stocked(self.m, "f-orig")
        bid = self.m.create_batch("f-orig", 500, "op1")
        minors = [p for p in self.m.pick_list(bid) if p["kind"] == "minor"]
        self.assertTrue(all("PM-210" in p["route"] for p in minors))
        dispense_all(self.m, bid, lots)
        dl = self.m.plc_download(bid)
        self.assertEqual(dl["SaltKg"], 190.0)
        bag = self.m.blend_complete(bid, 497.5, 0, "op2")
        with self.assertRaises(MESError):   # not released yet
            self.m.start_run("s-orig-4s", bag, "A", 1000, "op3")
        status, cv = self.m.qc_result(bid, [38.1, 37.9, 38.3, 37.6, 38.0, 38.4, 37.8, 38.2, 37.7, 38.0], True, "qc1")
        self.assertEqual(status, "RELEASED")
        self.assertLess(cv, 5)
        with self.assertRaises(MESError):   # wrong formula for SKU
            self.m.start_run("s-fire-4s", bag, "A", 1000, "op3")
        rid = self.m.start_run("s-orig-4s", bag, "A", 1000, "op3")
        sku = self.m.one("SELECT * FROM sku WHERE id='s-orig-4s'")
        with self.assertRaises(MESError):
            self.m.label_check(rid, "000000000000", bid, "op3")
        self.m.label_check(rid, sku["upc"], bid, "op3")
        job = self.m.plc_job(rid, 80)
        self.assertTrue(job["Valid"])
        self.assertAlmostEqual(job["TargetG"], round(sku["net_g"] * 1.015, 1))
        self.m.record_weights(rid, [sku["tare_g"] + sku["net_g"] + d for d in (0.5, 1.2, 1.8, 0.9, 1.4)])
        self.assertTrue(self.m.hb133_check(rid)["passed"])
        self.m.end_run(rid, 1000, 4, 1, "op3")
        code, zpl = self.m.build_pallet(rid, 83, "op4")
        self.assertIn(code, zpl)
        self.m.ship(code, "Customer DC 1", "ship1")
        back = self.m.trace_back(bid)
        self.assertEqual(len(back["ingredients"]), len(self.m.formula("f-orig")["lines"]))
        fwd = self.m.trace_forward(lots["paprika"])
        self.assertEqual(fwd[0]["pallets"][0]["shipped_to"], "Customer DC 1")
        self.assertTrue(self.m.batch_record(bid)["audit"])

    def test_wheat_only_station_b_and_sequence(self):
        lots = stocked(self.m, "f-batter")
        bid = self.m.create_batch("f-batter", 500, "op1")
        dispense_all(self.m, bid, lots)
        bag = self.m.blend_complete(bid, 498, 0, "op2")
        self.m.qc_result(bid, [10.0, 10.1, 9.9, 10.0, 10.2, 9.8, 10.0, 10.1, 9.9, 10.0], True, "qc1")
        with self.assertRaises(MESError):
            self.m.start_run("s-batter-16b", bag, "A", 100, "op3")
        self.m.start_run("s-batter-16b", bag, "B", 100, "op3")
        seq = self.m.allergen_sequence(["f-batter", "f-fire", "f-orig", "f-ncpm"])
        self.assertEqual(seq[:2], ["f-orig", "f-fire"])
        self.assertEqual(set(seq[2:]), {"f-batter", "f-ncpm"})

    def test_failed_cv_rejects(self):
        lots = stocked(self.m, "f-orig")
        bid = self.m.create_batch("f-orig", 500, "op1")
        dispense_all(self.m, bid, lots)
        self.m.blend_complete(bid, 497, 0, "op2")
        status, cv = self.m.qc_result(bid, [30, 45, 38, 33, 41, 36, 44, 31, 39, 42], True, "qc1")
        self.assertEqual(status, "REJECTED")


class Api(unittest.TestCase):
    def test_http(self):
        m = MES(); m.load_site(SITE)
        srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(m))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        req = urllib.request.Request(base + "/api/batch", data=json.dumps({"formula": "f-orig", "target_kg": 500, "by": "op1"}).encode(),
                                     headers={"Content-Type": "application/json"})
        bid = json.loads(urllib.request.urlopen(req).read())["result"]
        pl = json.loads(urllib.request.urlopen(f"{base}/api/batch/{bid}/picklist").read())
        self.assertEqual(pl[0]["ingredient"], "salt")
        self.assertIn("Plant MES", urllib.request.urlopen(base + "/").read().decode())
        srv.shutdown(); srv.server_close()


if __name__ == "__main__":
    unittest.main()

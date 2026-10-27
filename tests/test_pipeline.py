import json
import sqlite3
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from pipeline.__main__ import run
from pipeline.clean import Rejected, clean, normalize_region, parse_date, parse_money
from pipeline.transform import by_key, by_month, summary

ROW = {"order_id": "ORD-1", "date": "2026-03-05", "customer": " Customer 1 ", "region": " nairobi ",
       "product": "Landing page", "qty": "2", "unit_price": "15,000", "currency": "KES"}


class CleanTests(unittest.TestCase):
    def test_parses_all_date_formats(self):
        for raw in ["2026-03-05", "05/03/2026", "Mar 05 2026"]:
            self.assertEqual(parse_date(raw), date(2026, 3, 5))
        with self.assertRaises(Rejected):
            parse_date("not a date")

    def test_normalizes_regions(self):
        self.assertEqual({normalize_region(r) for r in ["nairobi", " NAIROBI ", "Nairbi"]}, {"Nairobi"})

    def test_converts_money(self):
        self.assertEqual(parse_money("15,000", "KES"), Decimal("15000"))
        self.assertEqual(parse_money("100", "usd"), Decimal("12900"))
        for raw, cur in [("-5", "KES"), ("abc", "KES"), ("5", "EUR")]:
            with self.assertRaises(Rejected):
                parse_money(raw, cur)

    def test_clean_keeps_reasons_and_dedupes(self):
        rows = [ROW, dict(ROW), dict(ROW, order_id="ORD-2", qty=""), dict(ROW, order_id="ORD-3", date="??")]
        sales, rejected = clean(rows)
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales[0].revenue_kes, Decimal("30000"))
        self.assertEqual(sales[0].customer, "Customer 1")
        self.assertEqual(sorted(r for _, r in rejected), ["duplicate order_id", "missing qty", "unparseable date '??'"])


class TransformTests(unittest.TestCase):
    def setUp(self):
        self.sales, _ = clean([ROW, dict(ROW, order_id="ORD-2", date="2026-04-01", region="Mombasa", qty="1"),
                               dict(ROW, order_id="ORD-3", date="2026-04-02", customer="Customer 1", qty="1")])

    def test_aggregations(self):
        self.assertEqual(by_month(self.sales), {"2026-03": Decimal("30000"), "2026-04": Decimal("30000")})
        self.assertEqual(by_key(self.sales, "region")[0], ("Nairobi", Decimal("45000")))
        s = summary(self.sales)
        self.assertEqual((s["orders"], s["revenue_kes"], s["customers"], s["repeat_customers"]), (3, 60000, 1, 1))


class EndToEndTests(unittest.TestCase):
    def test_full_run_on_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            stats = run(Path("data/sales_raw.csv"), tmp / "s.db", tmp / "out")
            report = json.loads((tmp / "out" / "report.json").read_text())
            self.assertEqual(report["summary"], stats)
            self.assertEqual(stats["orders"] + report["rejected"]["count"], 615)
            self.assertIn("duplicate order_id", report["rejected"]["reasons"])
            self.assertTrue((tmp / "out" / "index.html").read_text().startswith("<!doctype html>"))
            with sqlite3.connect(tmp / "s.db") as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0], stats["orders"])
            run(Path("data/sales_raw.csv"), tmp / "s.db", tmp / "out")  # idempotent reload
            with sqlite3.connect(tmp / "s.db") as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0], stats["orders"])


if __name__ == "__main__":
    unittest.main()

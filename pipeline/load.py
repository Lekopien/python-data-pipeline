"""Loads clean sales into SQLite (idempotent: re-running replaces the same orders)."""
import sqlite3
from pathlib import Path

from .clean import Sale

SCHEMA = """
CREATE TABLE IF NOT EXISTS sales (
  order_id TEXT PRIMARY KEY,
  day TEXT NOT NULL,
  customer TEXT NOT NULL,
  region TEXT NOT NULL,
  product TEXT NOT NULL,
  qty INTEGER NOT NULL CHECK (qty > 0),
  unit_price_kes INTEGER NOT NULL CHECK (unit_price_kes > 0)
);
CREATE INDEX IF NOT EXISTS idx_sales_day ON sales(day);
"""


def load(sales: list[Sale], path: str | Path) -> int:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT OR REPLACE INTO sales VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(s.order_id, s.day.isoformat(), s.customer, s.region, s.product, s.qty, int(s.unit_price_kes)) for s in sales],
        )
        return conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]

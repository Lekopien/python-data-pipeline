"""python -m pipeline [input.csv] [--db sales.db] [--out report/]"""
import argparse
import csv
import logging
import time
from pathlib import Path

from .clean import clean
from .extract import read_csv
from .load import load
from .report import write_report
from .transform import by_key, by_month, summary

log = logging.getLogger("pipeline")


def run(src: Path, db: Path, out: Path) -> dict:
    t0 = time.perf_counter()
    sales, rejected = clean(read_csv(src))
    log.info("extracted+cleaned: %d good, %d rejected", len(sales), len(rejected))

    stored = load(sales, db)
    log.info("loaded: %d rows in %s", stored, db)

    out.mkdir(parents=True, exist_ok=True)
    with (out / "rejected.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["reason", "row"])
        w.writerows([why, dict(row)] for row, why in rejected)

    stats = summary(sales)
    write_report(out, stats, by_month(sales), by_key(sales, "region"), by_key(sales, "product"), rejected)
    log.info("report written to %s in %.2fs", out, time.perf_counter() - t0)
    return stats


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("src", nargs="?", default="data/sales_raw.csv", type=Path)
    p.add_argument("--db", default="sales.db", type=Path)
    p.add_argument("--out", default="report", type=Path)
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print(run(a.src, a.db, a.out))


if __name__ == "__main__":
    main()

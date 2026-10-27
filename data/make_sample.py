"""Generates a deliberately messy sales export: mixed date formats, currencies,
duplicates, blanks and typos, the way real spreadsheets arrive."""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
PRODUCTS = {"Landing page": 15000, "Business website": 45000, "Online store": 90000,
            "SEO package": 8000, "Maintenance (monthly)": 5000, "Speed audit": 8000}
REGIONS = ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret"]
TYPOS = {"Nairobi": ["nairobi", " Nairobi ", "NAIROBI", "Nairbi"], "Mombasa": ["mombasa", "Mombasa "]}


def fmt_date(d: date) -> str:
    return random.choice([d.isoformat(), d.strftime("%d/%m/%Y"), d.strftime("%b %d %Y")])


def main(out: Path = Path(__file__).with_name("sales_raw.csv"), n: int = 600) -> None:
    rows = []
    start = date(2026, 1, 1)
    for i in range(n):
        product = random.choice(list(PRODUCTS))
        region = random.choice(REGIONS)
        region = random.choice(TYPOS.get(region, [region]) + [region] * 4)
        qty = random.choice([1, 1, 1, 2, 3])
        price_kes = PRODUCTS[product]
        currency = random.choices(["KES", "USD"], [5, 1])[0]
        price = price_kes if currency == "KES" else round(price_kes / 129, 2)
        rows.append({
            "order_id": f"ORD-{1000 + i}",
            "date": fmt_date(start + timedelta(days=random.randint(0, 272))),
            "customer": f"Customer {random.randint(1, 180)}",
            "region": region,
            "product": product,
            "qty": qty,
            "unit_price": f"{price:,}" if random.random() < 0.2 else price,
            "currency": currency,
        })
    rows += random.sample(rows, 15)                    # exact duplicates
    for r in random.sample(rows, 8):
        r["qty"] = ""                                  # missing quantities
    for r in random.sample(rows, 4):
        r["date"] = "not a date"                       # unparseable dates
    for r in random.sample(rows, 3):
        r["unit_price"] = "-500"                       # negative prices
    random.shuffle(rows)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()

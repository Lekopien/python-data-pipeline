"""Validation and cleaning. Every rejected row is kept with a reason, never silently dropped."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%b %d %Y")
FX_TO_KES = {"KES": Decimal("1"), "USD": Decimal("129")}
REGION_FIXES = {"nairbi": "Nairobi"}


@dataclass(frozen=True)
class Sale:
    order_id: str
    day: date
    customer: str
    region: str
    product: str
    qty: int
    unit_price_kes: Decimal

    @property
    def revenue_kes(self) -> Decimal:
        return self.unit_price_kes * self.qty


class Rejected(ValueError):
    pass


def parse_date(raw: str) -> date:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    raise Rejected(f"unparseable date {raw!r}")


def normalize_region(raw: str) -> str:
    key = raw.strip().lower()
    return REGION_FIXES.get(key, key.title())


def parse_money(raw: str, currency: str) -> Decimal:
    try:
        amount = Decimal(raw.replace(",", "").strip())
    except InvalidOperation:
        raise Rejected(f"bad price {raw!r}") from None
    if amount <= 0:
        raise Rejected(f"non-positive price {raw!r}")
    rate = FX_TO_KES.get(currency.strip().upper())
    if rate is None:
        raise Rejected(f"unknown currency {currency!r}")
    return (amount * rate).quantize(Decimal("1"))


def parse_qty(raw: str) -> int:
    if not raw.strip():
        raise Rejected("missing qty")
    qty = int(raw)
    if qty <= 0:
        raise Rejected(f"non-positive qty {qty}")
    return qty


def clean_row(row: dict[str, str]) -> Sale:
    return Sale(
        order_id=row["order_id"].strip(),
        day=parse_date(row["date"]),
        customer=row["customer"].strip(),
        region=normalize_region(row["region"]),
        product=row["product"].strip(),
        qty=parse_qty(row["qty"]),
        unit_price_kes=parse_money(row["unit_price"], row["currency"]),
    )


def clean(rows) -> tuple[list[Sale], list[tuple[dict, str]]]:
    """Returns (good sales, rejected rows with reasons). Duplicate order ids keep the first."""
    sales, rejected, seen = [], [], set()
    for row in rows:
        try:
            sale = clean_row(row)
        except (Rejected, ValueError, KeyError) as e:
            rejected.append((row, str(e)))
            continue
        if sale.order_id in seen:
            rejected.append((row, "duplicate order_id"))
            continue
        seen.add(sale.order_id)
        sales.append(sale)
    return sales, rejected

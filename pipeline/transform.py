"""Aggregations over clean sales."""
from collections import Counter, defaultdict
from decimal import Decimal

from .clean import Sale


def by_month(sales: list[Sale]) -> dict[str, Decimal]:
    out: dict[str, Decimal] = defaultdict(Decimal)
    for s in sales:
        out[s.day.strftime("%Y-%m")] += s.revenue_kes
    return dict(sorted(out.items()))


def by_key(sales: list[Sale], key: str) -> list[tuple[str, Decimal]]:
    out: dict[str, Decimal] = defaultdict(Decimal)
    for s in sales:
        out[getattr(s, key)] += s.revenue_kes
    return sorted(out.items(), key=lambda kv: kv[1], reverse=True)


def summary(sales: list[Sale]) -> dict:
    total = sum((s.revenue_kes for s in sales), Decimal())
    orders = len(sales)
    customers = Counter(s.customer for s in sales)
    return {
        "orders": orders,
        "revenue_kes": int(total),
        "avg_order_kes": int(total / orders) if orders else 0,
        "customers": len(customers),
        "repeat_customers": sum(1 for c in customers.values() if c > 1),
    }

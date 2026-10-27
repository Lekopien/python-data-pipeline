"""Writes the report: JSON for machines, and a self-contained HTML page with SVG charts."""
import html
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path


def kes(v) -> str:
    return f"KES {int(v):,}"


def bar_chart(items: list[tuple[str, Decimal]], width: int = 640, bar_h: int = 26) -> str:
    """Horizontal bar chart as inline SVG, no plotting library needed."""
    top = max((v for _, v in items), default=1) or 1
    label_w, gap = 170, 8
    height = len(items) * (bar_h + gap)
    rows = []
    for i, (label, value) in enumerate(items):
        y = i * (bar_h + gap)
        w = float(value / top) * (width - label_w - 110)
        rows.append(
            f'<text x="{label_w - 10}" y="{y + bar_h * 0.68}" text-anchor="end" class="lbl">{html.escape(label)}</text>'
            f'<rect x="{label_w}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="5" class="bar"/>'
            f'<text x="{label_w + w + 8:.1f}" y="{y + bar_h * 0.68}" class="val">{kes(value)}</text>'
        )
    return f'<svg viewBox="0 0 {width} {height}" role="img" width="100%">{"".join(rows)}</svg>'


def line_chart(series: dict[str, Decimal], width: int = 640, height: int = 220) -> str:
    """Monthly revenue as an SVG line with points."""
    months, values = list(series), [float(v) for v in series.values()]
    if not values:
        return ""
    pad, top = 40, max(values) * 1.1
    step = (width - 2 * pad) / max(len(values) - 1, 1)
    pts = [(pad + i * step, height - pad - v / top * (height - 2 * pad)) for i, v in enumerate(values)]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" class="dot"><title>{m}: {kes(v)}</title></circle>'
                   for (x, y), m, v in zip(pts, months, values))
    labels = "".join(f'<text x="{x:.1f}" y="{height - 12}" text-anchor="middle" class="lbl">{m[5:]}</text>'
                     for (x, _), m in zip(pts, months))
    return (f'<svg viewBox="0 0 {width} {height}" role="img" width="100%">'
            f'<line x1="{pad}" y1="{height - pad}" x2="{width - pad}" y2="{height - pad}" class="axis"/>'
            f'<path d="{path}" class="line"/>{dots}{labels}</svg>')


def write_report(out_dir: Path, summary: dict, months, regions, products, rejected) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    reasons: dict[str, int] = {}
    for _, why in rejected:
        key = why.split(" '")[0].split(" -")[0]
        reasons[key] = reasons.get(key, 0) + 1

    data = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "revenue_by_month": {k: int(v) for k, v in months.items()},
        "revenue_by_region": {k: int(v) for k, v in regions},
        "revenue_by_product": {k: int(v) for k, v in products},
        "rejected": {"count": len(rejected), "reasons": reasons},
    }
    (out_dir / "report.json").write_text(json.dumps(data, indent=2))

    cards = "".join(f'<div class="kpi"><span>{html.escape(label)}</span><b>{value}</b></div>' for label, value in [
        ("Revenue", kes(summary["revenue_kes"])), ("Orders", f'{summary["orders"]:,}'),
        ("Avg order", kes(summary["avg_order_kes"])), ("Customers", summary["customers"]),
        ("Rows rejected", len(rejected))])
    reason_rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{v}</td></tr>" for k, v in sorted(reasons.items(), key=lambda kv: -kv[1]))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sales report</title><style>
:root{{--bg:#fff;--fg:#141821;--muted:#5b6475;--line:#e3e6ee;--accent:#7c5cff;--panel:#f7f8fb}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0b0d12;--fg:#e8ebf2;--muted:#9aa3b5;--line:#232937;--panel:#141821}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}}main{{max-width:900px;margin:0 auto;padding:24px 16px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}.kpi{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px}}
.kpi span{{display:block;color:var(--muted);font-size:13px}}.kpi b{{font-size:20px}}h2{{margin-top:32px;font-size:18px}}
.bar{{fill:var(--accent)}}.lbl,.val{{fill:var(--muted);font-size:13px}}.line{{fill:none;stroke:var(--accent);stroke-width:3}}.dot{{fill:var(--accent)}}.axis{{stroke:var(--line)}}
table{{border-collapse:collapse}}td{{padding:4px 14px 4px 0;border-bottom:1px solid var(--line)}}small{{color:var(--muted)}}
</style></head><body><main>
<h1>Sales report 2026</h1><small>Generated {data["generated_at"]} by python-data-pipeline</small>
<div class="kpis" style="margin-top:16px">{cards}</div>
<h2>Revenue by month</h2>{line_chart(months)}
<h2>Revenue by product</h2>{bar_chart(products)}
<h2>Revenue by region</h2>{bar_chart(regions)}
<h2>Data quality: rejected rows</h2><table>{reason_rows}</table>
</main></body></html>"""
    (out_dir / "index.html").write_text(page)

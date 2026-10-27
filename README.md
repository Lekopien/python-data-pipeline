# Python Data Pipeline

[![pipeline](https://github.com/Lekopien/python-data-pipeline/actions/workflows/pipeline.yml/badge.svg)](https://github.com/Lekopien/python-data-pipeline/actions/workflows/pipeline.yml)

**Live report: https://data.lekopien.com**

An ETL pipeline that turns a messy sales spreadsheet into clean data, a SQLite table and a visual report, using **only the Python standard library**. It's built the way data work should be: streaming input, explicit validation, rejected rows kept with reasons, exact money arithmetic, idempotent loads and tests.

```
data/sales_raw.csv ─► extract ─► clean & validate ─► transform ─► load (SQLite)
                                       │                  └────► report (HTML + SVG, JSON)
                                       └─► rejected.csv (row + reason)
```

## What the cleaning handles

The sample file (`data/make_sample.py`) is deliberately dirty, like real exports:

| Problem | Fix |
| --- | --- |
| Three date formats (`2026-03-05`, `05/03/2026`, `Mar 05 2026`) | Tries each format; unparseable dates are rejected |
| Region typos and spacing (`NAIROBI`, ` nairobi `, `Nairbi`) | Normalised and corrected |
| Prices in KES and USD, some with thousands separators | Converted to KES with `Decimal` |
| Duplicate orders | First occurrence kept, the rest rejected |
| Missing quantities, negative prices | Rejected with a reason |

## Run it

```bash
python3 -m pipeline                       # reads data/sales_raw.csv
python3 -m pipeline my.csv --db out.db --out report/
python3 -m unittest -v
```

```
INFO extracted+cleaned: 585 good, 30 rejected
INFO loaded: 585 rows in sales.db
INFO report written to report in 0.03s
{'orders': 585, 'revenue_kes': 24204024, 'avg_order_kes': 41374, 'customers': 171, 'repeat_customers': 144}
```

Outputs in `report/`: `index.html` (KPIs plus SVG line and bar charts, light and dark), `report.json`, and `rejected.csv`.

## Code tour

| Module | Role |
| --- | --- |
| `pipeline/extract.py` | Streams CSV rows with a generator |
| `pipeline/clean.py` | Typed `Sale` dataclass, parsers, dedupe, rejection reasons |
| `pipeline/transform.py` | Revenue by month, region and product; summary KPIs |
| `pipeline/load.py` | Idempotent `INSERT OR REPLACE` into SQLite with constraints |
| `pipeline/report.py` | Hand-written SVG charts and the HTML/JSON report |
| `pipeline/__main__.py` | CLI and orchestration with logging and timing |

CI runs the tests, executes the pipeline and uploads the report as a build artifact.

## License

MIT

## Author

Built by **David Lekopien** ([@Lekopien](https://github.com/Lekopien)) · [lekopien.com](https://lekopien.com)

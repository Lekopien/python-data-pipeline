import csv
from pathlib import Path
from typing import Iterator


def read_csv(path: str | Path) -> Iterator[dict[str, str]]:
    """Streams rows as dicts so large files never sit in memory at once."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        yield from csv.DictReader(f)

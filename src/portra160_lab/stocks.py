"""Pinned SpektraFilm stock registry. Missing profiles fail closed."""
from __future__ import annotations
import json
from pathlib import Path

_CATALOG = Path(__file__).resolve().parents[2] / 'config' / 'film_catalog.json'


def all_stocks(path: Path | None = None) -> dict:
    source = Path(path) if path else _CATALOG
    return json.loads(source.read_text(encoding='utf-8'))['profiles']


def supported_stock(key: str, path: Path | None = None) -> dict:
    stocks = all_stocks(path)
    if key not in stocks:
        raise ValueError(f'Unknown film {key!r}. Choices: {", ".join(stocks)}')
    stock = stocks[key]
    if stock['status'] != 'upstream_profile_available' or not stock.get('film') or not stock.get('print'):
        raise ValueError(
            f'{stock["name"]}: no verified SpektraFilm film/print profile is available. '
            'A different stock must not be substituted.'
        )
    return stock

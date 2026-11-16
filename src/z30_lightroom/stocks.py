"""Goal-stock registry for the Z30 Lightroom work. Missing stocks fail closed."""
from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
STOCKS_FILE = CONFIG_DIR / "z30_goal_stocks.json"
PINNED_COMMIT = "3bb2c2d2801ff68b92019cf1dbcbb133d60832bc"


def load_registry(path: Path | None = None) -> dict:
    data = json.loads(Path(path or STOCKS_FILE).read_text(encoding="utf-8"))
    if data.get("source_commit") != PINNED_COMMIT:
        raise ValueError("Stock registry was checked against a different SpektraFilm commit")
    return data["stocks"]


def available_stock(key: str, path: Path | None = None) -> dict:
    stocks = load_registry(path)
    if key not in stocks:
        raise ValueError(f"Unknown stock {key!r}. Goal stocks: {', '.join(stocks)}")
    stock = stocks[key]
    if stock["status"] != "available" or not stock["film"] or not stock["print"]:
        raise ValueError(f"{stock['name']}: {stock['status']}. {stock['notes']}")
    return stock


def available_keys(path: Path | None = None) -> list[str]:
    return [k for k, v in load_registry(path).items() if v["status"] == "available"]

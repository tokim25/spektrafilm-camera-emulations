"""Release-gate status for every goal stock, read from evidence files only.

A file's existence never counts as a pass: each gate reads the recorded values
and checks them.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .stocks import load_registry

EVIDENCE = Path("results") / "z30"


def _json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _reference_gate(root: Path, stock: str) -> dict[str, Any]:
    hits = []
    for side in sorted((root / "references").glob(f"*/{stock}.json")):
        meta = _json(side) or {}
        scene_side = _json(Path(str(meta.get("input", ""))).with_suffix(".json")) or {}
        if (meta.get("spektrafilm") or {}).get("verified") and scene_side.get("camera_model") == "NIKON Z 30":
            hits.append(side.parent.name)
    return {"met": bool(hits), "scenes": hits,
            "reason": None if hits else "no reference rendered from a Z30 NEF with a verified pinned commit"}


def _look_gate(root: Path, stock: str) -> dict[str, Any]:
    rep = _json(root / "look_gate" / f"look_gate_{stock}.json")
    if not rep:
        return {"met": False, "reason": "no held-out Lightroom look-gate report"}
    lr = rep.get("lightroom") or {}
    if rep.get("evidence_source") != "lightroom_export" or not lr.get("version"):
        return {"met": False, "reason": "report is not from recorded Lightroom exports"}
    pooled = rep.get("pooled_heldout") or {}
    return {"met": bool(pooled.get("pass")), "pooled": {g: pooled.get(g) for g in ("all", "neutrals", "skin", "saturated")},
            "reason": None if pooled.get("pass") else "held-out results miss at least one threshold"}


def _install_gate(root: Path, stock: str) -> dict[str, Any]:
    rec = _json(root / "install" / f"{stock}.json")
    ok = bool(rec and rec.get("tester_is_author") is False and all(
        rec.get(k) is True for k in ("backup_done", "installed", "readback_matches", "uninstalled_restored")))
    return {"met": ok, "reason": None if ok else "no completed install record by a non-author tester"}


def _calibration_gate(root: Path) -> dict[str, Any]:
    rep = _json(root / "calibration" / "tungsten_dcp_report.json")
    ok = bool(rep and rep.get("heldout", {}).get("pass"))
    return {"met": ok, "scope": "tungsten only (no daylight chart captures)",
            "reason": None if ok else "no ColorChecker SG tungsten captures or DCP yet"}


def status(workspace: Path) -> dict[str, Any]:
    root = Path(workspace) / EVIDENCE
    calibration = _calibration_gate(root)
    stocks = {}
    for key, s in load_registry().items():
        if s["status"] != "available":
            stocks[key] = {"name": s["name"], "blocked": True, "reason": s["notes"]}
            continue
        gates = {"reference": _reference_gate(root, key), "look": _look_gate(root, key),
                 "install": _install_gate(root, key)}
        stocks[key] = {"name": s["name"], "blocked": False, "gates": gates,
                       "met": all(g["met"] for g in gates.values()) and calibration["met"]}
    return {"goal_met": all(v.get("met", False) for v in stocks.values()),
            "calibration_gate": calibration, "stocks": stocks}

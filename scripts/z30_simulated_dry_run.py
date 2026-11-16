"""Dry run of the Z30 fit/evaluate pipeline with a SIMULATED Lightroom stand-in.

Real Z30 NEFs and the real pinned SpektraFilm renderer are used. Lightroom is
replaced by a known stand-in (matrix, filmic tone curve, ProPhoto encoding and
a lens-correction-like warp), so this run proves the pipeline mechanics and how
well a fitted LUT generalises to an unseen scene. It is NOT Lightroom evidence
and never counts toward a gate: outputs go to results/z30/simulation/ with
evidence_source "simulated_standin".

Usage: python scripts/z30_simulated_dry_run.py [--stocks portra160 ...]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import tifffile

from z30_lightroom.colorimetry import prophoto_encode, prophoto_decode
from z30_lightroom.cube import apply_lut
from z30_lightroom.register import Registration, render_export
from z30_lightroom.stocks import available_keys
from z30_lightroom.workflow import fit_stock, evaluate_stock

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "results" / "z30" / "simulation"
STANDIN_ICC = b"SIMULATED STAND-IN, NOT AN ICC PROFILE: ProPhoto"
TRAIN = {"pixls_garden_14bit": "NIKON_Z30_14BIT.NEF", "pixls_garden_12bit": "NIKON_Z30_12BIT.NEF"}
HELDOUT = {"pixls_toy_0029": "_DSC0029.NEF", "pixls_toy_0028": "_DSC0028.NEF"}


def standin_render(scene_linear: np.ndarray) -> np.ndarray:
    m = np.array([[1.05, -0.03, -0.02], [0.02, 0.97, 0.01], [0.0, 0.04, 0.96]])
    x = np.clip(scene_linear @ m.T * 4.0, 0, None)  # +2 EV, like a typical default render
    return prophoto_encode(x * 1.6 / (1 + x * 1.6))


def standin_geometry(img: np.ndarray) -> np.ndarray:
    """Resample as if Lightroom applied a barrel-correction warp and a 1% crop."""
    h, w = img.shape[:2]
    reg = Registration(scale=0.99, rotation_deg=0.0, shift_x=1.5, shift_y=-1.0, k1=-0.015, k2=0.0,
                       ref_shape=(h, w), export_shape=(h, w))
    return render_export(img, reg)


def write_tiff(path: Path, enc: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (np.clip(enc, 0, 1) * 65535 + 0.5).astype(np.uint16)
    tifffile.imwrite(path, data, photometric="rgb", extratags=[(34675, 7, len(STANDIN_ICC), STANDIN_ICC, True)])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stocks", nargs="+", default=available_keys())
    a = ap.parse_args()
    work = ROOT / "results" / "z30"
    exports = SIM / "exports"
    scenes = []
    for split, group in (("train", TRAIN), ("heldout", HELDOUT)):
        for sid, nef in group.items():
            lin = np.load(work / "scenes" / f"{sid}.npy")
            ident = exports / "identity" / f"{sid}.tif"
            if not ident.exists():
                write_tiff(ident, standin_geometry(standin_render(lin)))
            scenes.append({"id": sid, "nef": str(ROOT / "data" / "raw" / "z30" / nef), "split": split,
                           "identity_export": str(ident), "stock_exports": {}})
    manifest = {"lightroom": {"app": "SIMULATED STAND-IN", "version": None}, "scenes": scenes}
    summary = {}
    for stock in a.stocks:
        meta = fit_stock_manifest(manifest, stock, work)
        from z30_lightroom.cube import read_cube
        lut = read_cube(SIM / "luts" / meta["cube"])
        for s in scenes:
            if s["split"] == "heldout":
                lin = np.load(work / "scenes" / f"{s['id']}.npy")
                out = exports / stock / f"{s['id']}.tif"
                write_tiff(out, standin_geometry(apply_lut(lut, standin_render(lin))))
                s["stock_exports"][stock] = str(out)
        mpath = SIM / "manifest.json"
        mpath.write_text(json.dumps(manifest, indent=2) + "\n")
        rep = evaluate_stock(mpath, stock, work, SIM / "look_gate")
        rep["evidence_source"] = "simulated_standin"
        rep["warning"] = "Simulated Lightroom stand-in. Not evidence for any gate."
        (SIM / "look_gate" / f"look_gate_{stock}.json").write_text(json.dumps(rep, indent=2) + "\n")
        p = rep["pooled_heldout"]
        summary[stock] = {g: {k: (round(p[g][k], 3) if isinstance(p[g].get(k), float) else p[g].get(k))
                              for k in ("n", "mean", "p95", "max", "pass")} for g in ("all", "neutrals", "skin", "saturated")}
        summary[stock]["pass"] = p["pass"]
        print(stock, json.dumps(summary[stock]))
    (SIM / "summary.json").write_text(json.dumps({"evidence_source": "simulated_standin",
                                                   "train": list(TRAIN), "heldout": list(HELDOUT),
                                                   "stocks": summary}, indent=2) + "\n")
    return 0


def fit_stock_manifest(manifest: dict, stock: str, work: Path) -> dict:
    mpath = SIM / "manifest.json"
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(json.dumps(manifest, indent=2) + "\n")
    return fit_stock(mpath, stock, work, SIM / "luts")


if __name__ == "__main__":
    raise SystemExit(main())

"""File-level workflow: scenes, Lightroom exports, fitting and gate reports.

A scene manifest (JSON) lists Z30 NEFs and their Lightroom exports:

{
  "lightroom": {"app": "Lightroom Classic", "version": "...", "camera_raw": "..."},
  "scenes": [
    {"id": "pb01", "nef": "data/raw/z30/nikon_z30_01.nef", "split": "train",
     "identity_export": "exports/identity/nikon_z30_01.tif",
     "stock_exports": {"portra160": "exports/portra160/nikon_z30_01.tif"}}
  ]
}

Training scenes need only the identity export. Held-out scenes need the
stock exports made with the fitted profiles. A scene is never both.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import numpy as np

from .colorimetry import prophoto_decode, prophoto_encode
from .cube import write_cube
from .evaluate import load_thresholds, pair_blocks, look_gate
from .cube import apply_lut
from .fit import build_prior_lut, fit_lut, select_inverse_model, mean_lab_error
from .reference import develop_nef, render_reference, render_stock, verify_spektrafilm_commit
from .register import Registration, register, warp_to_reference
from .stocks import available_stock

Z30_MODEL = "NIKON Z 30"


def nef_model(path: Path) -> str:
    import exifread
    with Path(path).open("rb") as f:
        tags = exifread.process_file(f, details=False, stop_tag="Model")
    return str(tags.get("Image Model", "")).strip()


def load_export(path: Path) -> np.ndarray:
    """A 16-bit ProPhoto RGB TIFF from Lightroom as encoded floats in [0, 1]."""
    import tifffile
    with tifffile.TiffFile(path) as tif:
        page = tif.pages[0]
        icc = page.tags.get(34675)
        if icc is None or b"ProPhoto" not in bytes(icc.value):
            raise ValueError(f"{path}: export must embed Adobe's ProPhoto RGB profile")
        img = page.asarray()
    if img.dtype != np.uint16 or img.ndim != 3 or img.shape[2] < 3:
        raise ValueError(f"{path}: export must be a 16-bit RGB TIFF")
    return img[..., :3].astype(np.float64) / 65535.0


def prepare_scene(nef: Path, work: Path, scene_id: str) -> Path:
    model = nef_model(nef)
    if model != Z30_MODEL:
        raise ValueError(f"{nef}: camera model is {model!r}, not {Z30_MODEL!r}")
    dest = Path(work) / "scenes" / f"{scene_id}.npy"
    if not dest.exists():
        develop_nef(nef, dest)
        side = json.loads(dest.with_suffix(".json").read_text())
        side["camera_model"] = model
        dest.with_suffix(".json").write_text(json.dumps(side, indent=2) + "\n")
    return dest


def reference_for(scene_npy: Path, stock: str, work: Path) -> np.ndarray:
    dest = Path(work) / "references" / scene_npy.stem / f"{stock}.npy"
    if not dest.exists():
        render_reference(scene_npy, dest, stock)
    return np.load(dest)


def registration_for(scene_npy: Path, export_path: Path, work: Path) -> Registration:
    from .reference import _sha256
    dest = Path(work) / "registration" / f"{scene_npy.stem}__{_sha256(Path(export_path))[:16]}.json"
    if dest.exists():
        return Registration.from_dict(json.loads(dest.read_text()))
    scene = np.load(scene_npy)
    reg = register(scene, prophoto_decode(load_export(export_path)))
    if reg.score < 0.5:
        raise RuntimeError(f"{scene_npy.stem}: registration score {reg.score:.2f} is too low to trust")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(reg.to_dict(), indent=2) + "\n")
    return reg


def scene_blocks(scene_npy: Path, export_path: Path, reg: Registration, reference: np.ndarray, cfg: dict,
                 edge_margin: int = 0):
    export = load_export(export_path)
    warped, valid = warp_to_reference(export, reg, reference.shape[:2])
    return pair_blocks(reference, warped, valid, cfg, scene_linear=np.load(scene_npy), edge_margin=edge_margin)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _select_smoothness(x, y, lin, grp, render, lut_size, grid=(1.0, 3.0, 10.0)):
    """Leave-one-scene-out choice of LUT smoothness, using training scenes only."""
    scenes = np.unique(grp)
    if scenes.size < 2:
        return 3.0, {"method": "default (fewer than 2 training scenes)", "smoothness": 3.0}
    errs = {sm: [] for sm in grid}
    for g in scenes:
        tr, te = grp != g, grp == g
        model, _ = select_inverse_model(x[tr], lin[tr], grp[tr])
        prior = build_prior_lut(model, render, prophoto_encode, n=lut_size)
        for sm in grid:
            errs[sm].append(mean_lab_error(y[te], apply_lut(fit_lut(x[tr], y[tr], prior, smoothness=sm), x[te])))
    scores = {sm: float(np.mean(v)) for sm, v in errs.items()}
    best = min(scores, key=scores.get)
    return best, {"method": "leave-one-scene-out", "smoothness": best, "scores": {f"{k:g}": v for k, v in scores.items()}}


def fit_stock(manifest_path: Path, stock: str, work: Path, out_dir: Path, lut_size: int = 33) -> dict[str, Any]:
    manifest = json.loads(Path(manifest_path).read_text())
    cfg = load_thresholds()
    available_stock(stock)
    xs, ys, scenes_lin, groups = [], [], [], []
    used = []
    for s in manifest["scenes"]:
        if s["split"] != "train":
            continue
        scene = prepare_scene(Path(s["nef"]), work, s["id"])
        reg = registration_for(scene, Path(s["identity_export"]), work)
        ref = reference_for(scene, stock, work)
        b = scene_blocks(scene, Path(s["identity_export"]), reg, ref, cfg, edge_margin=1)
        k = b["keep"]
        xs.append(b["export_enc"][k]); ys.append(prophoto_encode(b["ref_linear"][k]))
        scenes_lin.append(b["scene_linear"][k]); groups.append(np.full(int(k.sum()), len(used)))
        used.append({"id": s["id"], "blocks": int(k.sum()), "registration_score": reg.score})
    if not xs:
        raise ValueError("Manifest has no training scenes")
    x, y, lin, grp = np.vstack(xs), np.vstack(ys), np.vstack(scenes_lin), np.concatenate(groups)
    render = lambda img: render_stock(img, stock)
    model, inverse_info = select_inverse_model(x, lin, grp)
    smoothness, smooth_info = _select_smoothness(x, y, lin, grp, render, lut_size)
    prior = build_prior_lut(model, render, prophoto_encode, n=lut_size)
    lut = fit_lut(x, y, prior, smoothness=smoothness)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = available_stock(stock)["name"]
    cube = out_dir / f"Z30_{stock}_experimental.cube"
    write_cube(cube, lut, title=f"Z30 {name} experimental",
               comments=[f"Experimental fit of SpektraFilm {name} for Nikon Z30 in Lightroom.",
                         "Not validated until the look gate passes on held-out scenes.",
                         "Derived from SpektraFilm (GPL-3.0) by z30_lightroom; GPL-3.0."])
    meta = {"format": "z30-lut-fit-v1", "stock": stock, "created": _now(), "cube": cube.name,
            "lut_size": lut_size, "training_scenes": used, "training_blocks": int(x.shape[0]),
            "inverse_model_selection": inverse_info, "lut_smoothness_selection": smooth_info,
            "training_fit_mean_de00": mean_lab_error(y, apply_lut(lut, x)),
            "lightroom": manifest.get("lightroom"), "spektrafilm": verify_spektrafilm_commit(),
            "status": "experimental: not validated"}
    (out_dir / f"Z30_{stock}_fit.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def evaluate_stock(manifest_path: Path, stock: str, work: Path, out_dir: Path) -> dict[str, Any]:
    manifest = json.loads(Path(manifest_path).read_text())
    cfg = load_thresholds()
    available_stock(stock)
    ref_labs, cand = [], []
    per_scene = []
    for s in manifest["scenes"]:
        if s["split"] != "heldout" or stock not in s.get("stock_exports", {}):
            continue
        scene = prepare_scene(Path(s["nef"]), work, s["id"])
        reg = registration_for(scene, Path(s["identity_export"]), work)
        ref = reference_for(scene, stock, work)
        b = scene_blocks(scene, Path(s["stock_exports"][stock]), reg, ref, cfg)
        k = b["keep"]
        per_scene.append({"id": s["id"], "blocks": int(k.sum()),
                          "look_gate": look_gate(b["ref_lab"][k], b["export_enc"][k], cfg)})
        ref_labs.append(b["ref_lab"][k]); cand.append(b["export_enc"][k])
    if not ref_labs:
        raise ValueError(f"No held-out scenes with {stock} exports in the manifest")
    pooled = look_gate(np.vstack(ref_labs), np.vstack(cand), cfg)
    report = {"format": "z30-look-gate-v1", "stock": stock, "created": _now(),
              "evidence_source": "lightroom_export", "lightroom": manifest.get("lightroom"),
              "thresholds_version": cfg["version"], "pooled_heldout": pooled, "scenes": per_scene,
              "spektrafilm": verify_spektrafilm_commit()}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"look_gate_{stock}.json").write_text(json.dumps(report, indent=2) + "\n")
    return report

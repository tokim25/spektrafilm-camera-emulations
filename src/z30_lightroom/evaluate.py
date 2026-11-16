"""Block pairing, scene groups and acceptance-gate statistics."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from portra160_lab.color import delta_e_2000
from .colorimetry import prophoto_linear_to_lab, prophoto_decode, lab_chroma_hue
from .stocks import CONFIG_DIR

THRESHOLDS_FILE = CONFIG_DIR / "z30_acceptance_thresholds.json"
GROUPS = ("all", "neutrals", "skin", "saturated")


def load_thresholds(path: Path | None = None) -> dict:
    return json.loads(Path(path or THRESHOLDS_FILE).read_text(encoding="utf-8"))


def _blocks(img: np.ndarray, b: int) -> np.ndarray:
    h, w = (img.shape[0] // b) * b, (img.shape[1] // b) * b
    c = img.shape[2] if img.ndim == 3 else 1
    return img[:h, :w].reshape(h // b, b, w // b, b, c)


def pair_blocks(reference_linear: np.ndarray, export_enc: np.ndarray, valid: np.ndarray,
                cfg: dict, block: int = 4, scene_linear: np.ndarray | None = None,
                edge_margin: int = 0) -> dict[str, np.ndarray]:
    """Block means of reference and export plus the mask of blocks usable for measurement.

    `edge_margin` > 0 also drops blocks within that many blocks of an edge block.
    Fitting uses it to keep misregistered pairs out of training; gate evaluation
    keeps the frozen protocol (margin 0).
    """
    sg = cfg["scene_groups"]
    ref_lab = prophoto_linear_to_lab(reference_linear)
    lab_b = _blocks(ref_lab, block)
    spread = lab_b[..., 0].std(axis=(1, 3))
    out = {
        "ref_linear": _blocks(reference_linear, block).mean(axis=(1, 3)).reshape(-1, 3),
        "export_enc": _blocks(export_enc, block).mean(axis=(1, 3)).reshape(-1, 3),
    }
    out["ref_lab"] = prophoto_linear_to_lab(out["ref_linear"])
    ok_valid = _blocks(valid.astype(float)[..., None], block).min(axis=(1, 3))[..., 0].reshape(-1) > 0.5
    ok2d = spread <= sg["max_block_spread_L"]
    if edge_margin > 0:
        from scipy import ndimage
        ok2d = ndimage.minimum_filter(ok2d.astype(np.uint8), size=2 * edge_margin + 1, mode="nearest") > 0
    ok_spread = ok2d.reshape(-1)
    lo, hi = sg["L_range"]
    ok_L = (out["ref_lab"][:, 0] >= lo) & (out["ref_lab"][:, 0] <= hi)
    ok_clip = _blocks(export_enc, block).max(axis=(1, 3, 4)).reshape(-1) < 0.995
    out["keep"] = ok_valid & ok_spread & ok_L & ok_clip
    if scene_linear is not None:
        out["scene_linear"] = _blocks(scene_linear, block).mean(axis=(1, 3)).reshape(-1, 3)
    return out


def group_masks(ref_lab: np.ndarray, cfg: dict) -> dict[str, np.ndarray]:
    sg = cfg["scene_groups"]
    chroma, hue = lab_chroma_hue(ref_lab)
    L = ref_lab[:, 0]
    s = sg["skin"]
    return {
        "all": np.ones(len(L), bool),
        "neutrals": chroma <= sg["neutrals"]["chroma_max"],
        "skin": ((hue >= s["hue_deg"][0]) & (hue <= s["hue_deg"][1]) & (chroma >= s["chroma"][0])
                 & (chroma <= s["chroma"][1]) & (L >= s["L"][0]) & (L <= s["L"][1])),
        "saturated": chroma >= sg["saturated"]["chroma_min"],
    }


def gate_stats(de: np.ndarray, groups: dict[str, np.ndarray], limits: dict, min_p95: int) -> dict[str, Any]:
    """Mean / p95 / max per group against limits. A group with no samples cannot pass."""
    report: dict[str, Any] = {}
    passed = True
    for g in GROUPS:
        v = de[groups[g]]
        lim = limits[g]
        if v.size == 0:
            report[g] = {"n": 0, "pass": False, "reason": "no samples in this group"}
            passed = False
            continue
        stats = {"n": int(v.size), "mean": float(v.mean()), "max": float(v.max()),
                 "p95": float(np.percentile(v, 95)) if v.size >= min_p95 else None}
        checks = [stats["mean"] <= lim["mean"], stats["max"] <= lim["max"]]
        if stats["p95"] is not None:
            checks.append(stats["p95"] <= lim["p95"])
        stats["limits"] = lim
        stats["pass"] = bool(all(checks))
        passed &= stats["pass"]
        report[g] = stats
    report["pass"] = bool(passed)
    return report


def look_gate(ref_lab: np.ndarray, candidate_enc: np.ndarray, cfg: dict) -> dict[str, Any]:
    """ΔE00 of a Lightroom render (ProPhoto-encoded block means) against the reference blocks."""
    cand_lab = prophoto_linear_to_lab(prophoto_decode(candidate_enc))
    de = delta_e_2000(ref_lab, cand_lab)
    return gate_stats(de, group_masks(ref_lab, cfg), cfg["gates"]["look"], cfg["min_samples_for_p95"])

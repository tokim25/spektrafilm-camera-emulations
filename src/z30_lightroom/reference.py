"""Scene-linear Z30 development and SpektraFilm reference rendering.

The reference is SpektraFilm in lut_mode (deterministic per-pixel color, no
grain, halation or auto exposure). Grain and halation are deliberately out of
the color comparison, as the project's engineering standards require.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any

import numpy as np

from .stocks import PINNED_COMMIT, available_stock


def _sha256(path: Path) -> str:
    h = sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify_spektrafilm_commit() -> dict[str, Any]:
    """Check which SpektraFilm source is installed, from pip metadata or the editable checkout."""
    try:
        dist = importlib.metadata.distribution("spektrafilm")
    except importlib.metadata.PackageNotFoundError:
        return {"installed": False, "verified": False, "reason": "spektrafilm is not installed"}
    try:
        direct = json.loads(dist.read_text("direct_url.json") or "{}")
    except json.JSONDecodeError:
        direct = {}
    result: dict[str, Any] = {"installed": True, "version": dist.version, "expected_commit": PINNED_COMMIT}
    commit = (direct.get("vcs_info") or {}).get("commit_id")
    if commit:
        result.update(method="pip vcs metadata", commit=commit, verified=commit == PINNED_COMMIT)
        return result
    url = direct.get("url", "")
    if url.startswith("file://") and (direct.get("dir_info") or {}).get("editable"):
        src = url[len("file://"):]
        try:
            head = subprocess.run(["git", "-C", src, "rev-parse", "HEAD"], capture_output=True,
                                  text=True, check=True).stdout.strip()
            dirty = subprocess.run(["git", "-C", src, "status", "--porcelain", "--untracked-files=no"],
                                   capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            result.update(method="editable checkout", verified=False, reason=f"git check failed: {exc}")
            return result
        result.update(method="editable checkout git HEAD", checkout=src, commit=head,
                      tracked_changes=bool(dirty), verified=head == PINNED_COMMIT and not dirty)
        return result
    result.update(method="none", verified=False, reason="install has no commit information")
    return result


def block_mean(img: np.ndarray, factor: int) -> np.ndarray:
    """Average non-overlapping factor x factor blocks, dropping edge remainders."""
    h, w = (img.shape[0] // factor) * factor, (img.shape[1] // factor) * factor
    x = img[:h, :w].astype(np.float64)
    return x.reshape(h // factor, factor, w // factor, factor, -1).mean(axis=(1, 3))


def develop_nef(source: Path, dest: Path, factor: int = 4) -> dict[str, Any]:
    """Provisional LibRaw development to linear ProPhoto, block-averaged by `factor`."""
    from portra160_lab.raw_pipeline import prepare_raw  # reuse the audited ingestion path
    source, dest = Path(source), Path(dest)
    with tempfile.TemporaryDirectory() as tmp:
        full = Path(tmp) / "full.npy"
        side = prepare_raw(source, full)
        small = block_mean(np.load(full), factor).astype(np.float32)
    dest.parent.mkdir(parents=True, exist_ok=True)
    np.save(dest, small, allow_pickle=False)
    side = {k: v for k, v in side.items() if k not in ("out_path", "out_sha256")}
    side.update(out_path=str(dest), out_sha256=_sha256(dest), block_average_factor=factor,
                shape=list(small.shape))
    dest.with_suffix(".json").write_text(json.dumps(side, indent=2) + "\n", encoding="utf-8")
    return side


def render_stock(scene_linear: np.ndarray, stock_key: str) -> np.ndarray:
    """Render linear ProPhoto input through a goal stock; returns linear ProPhoto output."""
    stock = available_stock(stock_key)
    from spektrafilm import init_params, simulate
    params = init_params(film_profile=stock["film"], print_profile=stock["print"])
    params.io.input_color_space = "ProPhoto RGB"
    params.io.input_cctf_decoding = False
    params.io.output_color_space = "ProPhoto RGB"
    params.io.output_cctf_encoding = False
    params.io.scan_film = bool(stock["scan_film"])
    params.debug.lut_mode = True
    src = np.asarray(scene_linear, dtype=np.float32)
    if src.ndim != 3 or src.shape[2] != 3 or np.any(~np.isfinite(src)) or np.any(src < 0):
        raise ValueError("Input must be finite, non-negative HxWx3 linear ProPhoto RGB")
    out = np.asarray(simulate(src, params), dtype=np.float64)
    if out.shape != src.shape or np.any(~np.isfinite(out)):
        raise RuntimeError("SpektraFilm returned an unexpected shape or non-finite values")
    return out


def render_reference(source: Path, dest: Path, stock_key: str) -> dict[str, Any]:
    """Render a developed .npy through one stock and write the output plus a sidecar."""
    commit = verify_spektrafilm_commit()
    src = np.load(source, allow_pickle=False)
    out = render_stock(src, stock_key)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    np.save(dest, out.astype(np.float32), allow_pickle=False)
    stock = available_stock(stock_key)
    meta = {
        "format": "z30-spektrafilm-reference-v1",
        "stock": stock_key, "film": stock["film"], "print": stock["print"],
        "scan_film": stock["scan_film"], "mode": "lut_mode (color only)",
        "input": str(source), "input_sha256": _sha256(Path(source)),
        "output": str(dest), "output_sha256": _sha256(dest),
        "output_color_space": "ProPhoto RGB, linear",
        "spektrafilm": commit,
        "excluded_effects": ["grain", "halation", "auto exposure", "scanner corrections"],
    }
    dest.with_suffix(".json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta

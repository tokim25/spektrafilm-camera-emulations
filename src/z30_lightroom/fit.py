"""Fit a per-stock 3D LUT from Lightroom identity exports to SpektraFilm references.

The LUT is fitted end to end, so it needs no assumptions about Camera Raw's
internal pipeline beyond what the probe kit verifies: input is the identity
profile's ProPhoto-encoded export, output is the SpektraFilm reference in the
same encoding.

Two stages:

1. Prior. A smooth additive model estimates scene-linear light from the export.
   SpektraFilm then renders every lattice node through that estimate, so lattice
   regions the training scenes never reach still follow the film model rather
   than an arbitrary extrapolation.
2. Correction. A Laplacian-regularised least-squares offset on the lattice
   absorbs what the prior gets wrong where training data exists.
"""
from __future__ import annotations

from typing import Callable
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import lsqr

from .cube import identity_lut, apply_lut


def _hat(x: np.ndarray, knots: int) -> np.ndarray:
    centers = np.linspace(0.0, 1.0, knots)
    width = centers[1] - centers[0]
    return np.maximum(0.0, 1.0 - np.abs(np.clip(x, 0, 1)[:, None] - centers[None, :]) / width)


def fit_inverse_model(export_enc: np.ndarray, scene_linear: np.ndarray, knots: int = 24,
                      smooth: float = 1e-2, iterations: int = 30) -> dict:
    """Estimate scene light as M @ h(export): one shared per-channel curve h, then a 3x3 matrix.

    A raw converter renders roughly as matrix-then-tone-curve, so its inverse is
    roughly curve-then-matrix. Sharing h across channels lets every channel's data
    inform the whole curve, which keeps saturated colours that the training scenes
    barely reach on a sensible extrapolation. Fitted by alternating least squares.
    """
    x = np.asarray(export_enc, dtype=np.float64)
    s = np.asarray(scene_linear, dtype=np.float64)
    B = [_hat(x[:, c], knots) for c in range(3)]
    D2 = np.diff(np.eye(knots), 2, axis=0)
    a = np.linspace(0.0, 1.0, knots) ** 1.8 * max(1e-6, np.percentile(s, 99))
    M = np.eye(3)
    for _ in range(iterations):
        H = np.stack([b @ a for b in B], axis=1)
        M = np.linalg.lstsq(H, s, rcond=None)[0].T
        design = np.vstack([sum(M[j, c] * B[c] for c in range(3)) for j in range(3)])
        target = np.concatenate([s[:, j] for j in range(3)])
        lam = smooth * len(target)
        a = np.linalg.solve(design.T @ design + lam * D2.T @ D2 + 1e-9 * np.eye(knots), design.T @ target)
    return {"matrix": M, "curve": a, "knots": knots}


def apply_inverse_model(model: dict, export_enc: np.ndarray) -> np.ndarray:
    x = np.asarray(export_enc, dtype=np.float64)
    H = np.stack([_hat(x[:, c], model["knots"]) @ model["curve"] for c in range(3)], axis=1)
    return np.clip(H @ model["matrix"].T, 0.0, None)


def _laplacian(n: int) -> sparse.csr_matrix:
    """Second-difference operator along each lattice axis, stacked."""
    second =sparse.diags([np.ones(n - 2), -2 * np.ones(n - 2), np.ones(n - 2)], [0, 1, 2], shape=(n - 2, n))
    eye = sparse.identity(n)
    ops = [sparse.kron(sparse.kron(eye, eye), second),   # r (fastest)
           sparse.kron(sparse.kron(eye, second), eye),   # g
           sparse.kron(sparse.kron(second, eye), eye)]   # b
    return sparse.vstack(ops).tocsr()


def _interp_matrix(x: np.ndarray, n: int) -> sparse.csr_matrix:
    """Sparse trilinear weights from samples to lattice nodes (node index = (b*n+g)*n+r)."""
    p = np.clip(x, 0.0, 1.0) * (n - 1)
    i0 = np.minimum(np.floor(p).astype(int), n - 2)
    f = p - i0
    rows, cols, vals = [], [], []
    idx = np.arange(x.shape[0])
    for dr in (0, 1):
        for dg in (0, 1):
            for db in (0, 1):
                w = ((f[:, 0] if dr else 1 - f[:, 0]) * (f[:, 1] if dg else 1 - f[:, 1])
                     * (f[:, 2] if db else 1 - f[:, 2]))
                node = ((i0[:, 2] + db) * n + (i0[:, 1] + dg)) * n + (i0[:, 0] + dr)
                rows.append(idx); cols.append(node); vals.append(w)
    return sparse.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
                             shape=(x.shape[0], n ** 3))


def fit_lut(export_enc: np.ndarray, target_enc: np.ndarray, prior_lut: np.ndarray,
            smoothness: float = 3.0, huber: float = 0.02, robust_iterations: int = 3) -> np.ndarray:
    """Lattice offsets on top of `prior_lut` so that LUT(export) ~ target, smoothed by a Laplacian.

    Huber reweighting (threshold in encoded units) limits the pull of pairs that
    disagree with their neighbours, such as residual misregistration at edges.
    """
    n = prior_lut.shape[0]
    W = _interp_matrix(export_enc, n)
    L = _laplacian(n)
    resid = np.asarray(target_enc, dtype=np.float64) - apply_lut(prior_lut, export_enc)
    # scale the penalty with the sample count so smoothness means the same for any data size
    lam = smoothness * np.sqrt(max(1, export_enc.shape[0]) / n ** 3)
    offsets = np.zeros((n ** 3, 3))
    weights = np.ones(export_enc.shape[0])
    for _ in range(max(1, robust_iterations)):
        sw = np.sqrt(weights)
        A = sparse.vstack([sparse.diags(sw) @ W, lam * L]).tocsr()
        for c in range(3):
            b = np.concatenate([sw * resid[:, c], np.zeros(L.shape[0])])
            offsets[:, c] = lsqr(A, b, atol=1e-10, btol=1e-10, iter_lim=4000)[0]
        err = np.linalg.norm(W @ offsets - resid, axis=1)
        weights = np.where(err <= huber, 1.0, huber / np.maximum(err, 1e-12))
    out = prior_lut.reshape(-1, 3) + offsets
    return np.clip(out.reshape(n, n, n, 3), 0.0, 1.0)


def mean_lab_error(target_enc: np.ndarray, pred_enc: np.ndarray) -> float:
    from portra160_lab.color import delta_e_2000
    from .colorimetry import prophoto_decode, prophoto_linear_to_lab
    return float(delta_e_2000(prophoto_linear_to_lab(prophoto_decode(target_enc)),
                              prophoto_linear_to_lab(prophoto_decode(pred_enc))).mean())


def select_inverse_model(export_enc: np.ndarray, scene_linear: np.ndarray, groups: np.ndarray,
                         grid=((24, 1e-2), (40, 1e-2), (40, 1e-3), (40, 1e-4))) -> tuple[dict, dict]:
    """Pick knots/smoothing by leave-one-scene-out mean ΔE00 on scene light; training data only."""
    from portra160_lab.color import delta_e_2000
    from .colorimetry import prophoto_linear_to_lab
    scenes = np.unique(groups)
    if scenes.size < 2:
        k, s = grid[1]
        return fit_inverse_model(export_enc, scene_linear, knots=k, smooth=s), {"method": "default (fewer than 2 training scenes)", "knots": k, "smooth": s}
    scores = {}
    for k, s in grid:
        errs = []
        for g in scenes:
            tr, te = groups != g, groups == g
            m = fit_inverse_model(export_enc[tr], scene_linear[tr], knots=k, smooth=s)
            errs.append(delta_e_2000(prophoto_linear_to_lab(scene_linear[te]),
                                     prophoto_linear_to_lab(apply_inverse_model(m, export_enc[te]))).mean())
        scores[(k, s)] = float(np.mean(errs))
    k, s = min(scores, key=scores.get)
    info = {"method": "leave-one-scene-out", "knots": k, "smooth": s,
            "scores": {f"{kk}/{ss:g}": v for (kk, ss), v in scores.items()}}
    return fit_inverse_model(export_enc, scene_linear, knots=k, smooth=s), info


def build_prior_lut(coef: dict, render: Callable[[np.ndarray], np.ndarray],
                    encode: Callable[[np.ndarray], np.ndarray], n: int = 33) -> np.ndarray:
    """Render every lattice node: export encoding -> estimated scene light -> film -> encoding."""
    grid = identity_lut(n).reshape(-1, 3)
    scene = apply_inverse_model(coef, grid)
    film = render(scene.reshape(n * n, n, 3).astype(np.float32)).reshape(-1, 3)
    return encode(film).reshape(n, n, n, 3)

"""Align a Lightroom export to the LibRaw-developed reference grid.

Lightroom may apply built-in lens corrections and a small default crop that
LibRaw does not. The model maps reference pixel positions to export positions
with scale, rotation, translation and two radial distortion terms, fitted by
maximising the correlation of gradient magnitudes of log luminance. Gradients
make the score insensitive to the different tone curves of the two renders.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np
from scipy import ndimage, optimize


@dataclass
class Registration:
    scale: float
    rotation_deg: float
    shift_x: float
    shift_y: float
    k1: float
    k2: float
    ref_shape: tuple[int, int]
    export_shape: tuple[int, int]
    score: float = float("nan")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["ref_shape"], d["export_shape"] = list(self.ref_shape), list(self.export_shape)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Registration":
        d = dict(d)
        d["ref_shape"], d["export_shape"] = tuple(d["ref_shape"]), tuple(d["export_shape"])
        return cls(**d)


def _coords(reg: Registration, shape: tuple[int, int], ref_scale: float = 1.0):
    """Export-image (row, col) coordinates for every pixel of a reference grid of `shape`."""
    h, w = shape
    rh, rw = reg.ref_shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    # reference-pixel units, centred
    x = (xx + 0.5) * (rw / w) - rw / 2
    y = (yy + 0.5) * (rh / h) - rh / 2
    rad = np.hypot(rw, rh) / 2
    r2 = (x * x + y * y) / (rad * rad)
    d = 1 + reg.k1 * r2 + reg.k2 * r2 * r2
    x, y = x * d, y * d
    t = np.radians(reg.rotation_deg)
    xr = np.cos(t) * x - np.sin(t) * y
    yr = np.sin(t) * x + np.cos(t) * y
    eh, ew = reg.export_shape
    ex = reg.scale * xr + ew / 2 + reg.shift_x - 0.5
    ey = reg.scale * yr + eh / 2 + reg.shift_y - 0.5
    return ey * ref_scale, ex * ref_scale


def _points(reg: Registration, py: np.ndarray, px: np.ndarray):
    """Export (row, col) for reference pixel positions given in full-size reference pixels."""
    rh, rw = reg.ref_shape
    x, y = px + 0.5 - rw / 2, py + 0.5 - rh / 2
    rad = np.hypot(rw, rh) / 2
    r2 = (x * x + y * y) / (rad * rad)
    d = 1 + reg.k1 * r2 + reg.k2 * r2 * r2
    x, y = x * d, y * d
    t = np.radians(reg.rotation_deg)
    xr = np.cos(t) * x - np.sin(t) * y
    yr = np.sin(t) * x + np.cos(t) * y
    eh, ew = reg.export_shape
    return reg.scale * yr + eh / 2 + reg.shift_y - 0.5, reg.scale * xr + ew / 2 + reg.shift_x - 0.5


def warp_to_reference(export: np.ndarray, reg: Registration, shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    """Resample an HxWxC export onto a reference grid; returns (image, valid mask)."""
    ey, ex = _coords(reg, shape)
    eh, ew = export.shape[:2]
    valid = (ey >= 0) & (ey <= eh - 1) & (ex >= 0) & (ex <= ew - 1)
    out = np.stack([ndimage.map_coordinates(export[..., c].astype(np.float64), [ey, ex],
                                            order=1, mode="nearest") for c in range(export.shape[2])], axis=-1)
    return out, valid


def render_export(reference: np.ndarray, reg: Registration, iterations: int = 40) -> np.ndarray:
    """Synthesise an export that `reg` maps exactly back onto `reference` (tests and simulation).

    Each export pixel g shows the reference content at p with forward(p) = g; p is
    found by fixed-point iteration on the registration model itself.
    """
    eh, ew = reg.export_shape
    gy, gx = np.mgrid[0:eh, 0:ew].astype(np.float64)
    sy, sx = gy * reg.ref_shape[0] / eh, gx * reg.ref_shape[1] / ew
    for _ in range(iterations):
        fy, fx = _points(reg, sy, sx)
        sy, sx = sy + (gy - fy) / reg.scale, sx + (gx - fx) / reg.scale
    fy, fx = _points(reg, sy, sx)
    if max(np.abs(fy - gy).max(), np.abs(fx - gx).max()) > 1e-3:
        raise RuntimeError("inverse warp did not converge")
    return np.stack([ndimage.map_coordinates(reference[..., c].astype(np.float64), [sy, sx], order=1,
                                             mode="nearest") for c in range(reference.shape[2])], axis=-1)


def _edge_map(rgb: np.ndarray) -> np.ndarray:
    lum = np.log(np.clip(rgb.astype(np.float64).mean(axis=-1), 1e-4, None))
    g = np.hypot(ndimage.sobel(lum, 0), ndimage.sobel(lum, 1))
    return ndimage.gaussian_filter(g, 1.0)


def _shrink(img: np.ndarray, width: int) -> np.ndarray:
    f = max(1, img.shape[1] // width)
    h, w = (img.shape[0] // f) * f, (img.shape[1] // f) * f
    return img[:h, :w].reshape(h // f, f, w // f, f, -1).mean(axis=(1, 3))


def _optimize(reference_linear, export_linear, work_width, base, p0, coarse_search):
    """Maximise edge correlation at one working resolution, starting from parameters p0."""
    fr = max(1, reference_linear.shape[1] // work_width)
    fe = max(1, export_linear.shape[1] // work_width)
    ref_edges = _edge_map(_shrink(reference_linear, work_width))
    exp_edges = _edge_map(_shrink(export_linear, work_width))
    border = max(2, ref_edges.shape[1] // 40)
    a = ref_edges[border:-border, border:-border]
    a = (a - a.mean()) / (a.std() + 1e-12)
    # small-grid pixel i covers full-size pixels i*fr .. i*fr+fr-1; its centre is (i+0.5)*fr - 0.5
    rh, rw = ref_edges.shape[0] * fr, ref_edges.shape[1] * fr
    yy, xx = np.mgrid[0:ref_edges.shape[0], 0:ref_edges.shape[1]].astype(np.float64)

    def unpack(p):
        return Registration(scale=base.scale * np.exp(p[0]), rotation_deg=p[1], shift_x=p[2], shift_y=p[3],
                            k1=p[4], k2=p[5], ref_shape=base.ref_shape, export_shape=base.export_shape)

    def cost(p):
        ey, ex = _points(unpack(p), (yy + 0.5) * fr - 0.5, (xx + 0.5) * fr - 0.5)
        b = ndimage.map_coordinates(exp_edges, [(ey + 0.5) / fe - 0.5, (ex + 0.5) / fe - 0.5],
                                    order=1, mode="constant", cval=0.0)
        b = b[border:-border, border:-border]
        b = (b - b.mean()) / (b.std() + 1e-12)
        return -float((a * b).mean())

    start = p0
    if coarse_search:
        best = None
        for dx in np.arange(-6, 7, 2) * fe:
            for dy in np.arange(-6, 7, 2) * fe:
                q = p0 + np.array([0.0, 0.0, dx, dy, 0.0, 0.0])
                c = cost(q)
                if best is None or c < best[0]:
                    best = (c, q)
        start = best[1]
    res = optimize.minimize(cost, start, method="Powell", options={"xtol": 1e-4, "ftol": 1e-7, "maxfev": 4000})
    return res.x, -float(res.fun), unpack


def register(reference_linear: np.ndarray, export_linear: np.ndarray, work_width: int = 360) -> Registration:
    """Estimate the reference-to-export mapping, coarse to fine. Both inputs are linear-light RGB."""
    rh, rw = reference_linear.shape[:2]
    eh, ew = export_linear.shape[:2]
    base = Registration(scale=max(ew / rw, eh / rh), rotation_deg=0.0, shift_x=0.0, shift_y=0.0,
                        k1=0.0, k2=0.0, ref_shape=(rh, rw), export_shape=(eh, ew))
    p = np.zeros(6)
    widths = [work_width] + [w for w in (work_width * 2, rw) if w > work_width and w <= rw]
    for i, width in enumerate(dict.fromkeys(widths)):
        p, score, unpack = _optimize(reference_linear, export_linear, width, base, p, coarse_search=(i == 0))
    reg = unpack(p)
    reg.score = score
    return reg

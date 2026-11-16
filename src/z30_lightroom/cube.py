"""Adobe/IRIDAS .cube 3D LUT reading, writing and trilinear application.

Layout follows the Adobe Cube LUT Specification 1.0: one RGB triple per line,
red index varying fastest, then green, then blue.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np


def identity_lut(n: int) -> np.ndarray:
    """Array of shape (n, n, n, 3) indexed [b, g, r] holding the grid's own RGB."""
    axis = np.linspace(0.0, 1.0, n)
    b, g, r = np.meshgrid(axis, axis, axis, indexing="ij")
    return np.stack([r, g, b], axis=-1)


def write_cube(path: Path, lut: np.ndarray, title: str, comments: list[str] | None = None) -> None:
    lut = np.asarray(lut, dtype=np.float64)
    n = lut.shape[0]
    if lut.shape != (n, n, n, 3) or n < 2:
        raise ValueError("LUT must have shape (N, N, N, 3) indexed [b, g, r]")
    if not np.all(np.isfinite(lut)):
        raise ValueError("LUT contains non-finite values")
    if '"' in title or "\n" in title:
        raise ValueError("Title may not contain quotes or newlines")
    lines = [f"# {c}" for c in (comments or [])]
    lines += [f'TITLE "{title}"', f"LUT_3D_SIZE {n}",
              "DOMAIN_MIN 0.0 0.0 0.0", "DOMAIN_MAX 1.0 1.0 1.0"]
    flat = np.clip(lut, 0.0, 1.0).reshape(-1, 3)
    lines += [f"{r:.6f} {g:.6f} {b:.6f}" for r, g, b in flat]
    Path(path).write_text("\n".join(lines) + "\n", encoding="ascii")


def read_cube(path: Path) -> np.ndarray:
    size = None
    rows = []
    for raw in Path(path).read_text(encoding="ascii").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key = line.split()[0]
        if key == "LUT_3D_SIZE":
            size = int(line.split()[1])
        elif key in ("TITLE", "DOMAIN_MIN", "DOMAIN_MAX"):
            if key.startswith("DOMAIN"):
                vals = [float(v) for v in line.split()[1:]]
                if vals != ([0.0] * 3 if key == "DOMAIN_MIN" else [1.0] * 3):
                    raise ValueError("Only the [0, 1] domain is supported")
        elif key == "LUT_1D_SIZE":
            raise ValueError("1D LUTs are not supported")
        else:
            rows.append([float(v) for v in line.split()])
    if size is None or len(rows) != size ** 3:
        raise ValueError("Missing LUT_3D_SIZE or wrong number of rows")
    return np.asarray(rows).reshape(size, size, size, 3)


def apply_lut(lut: np.ndarray, rgb: np.ndarray) -> np.ndarray:
    """Trilinear lookup of encoded RGB in [0, 1] through a [b, g, r]-indexed LUT."""
    n = lut.shape[0]
    x = np.clip(np.asarray(rgb, dtype=np.float64), 0.0, 1.0) * (n - 1)
    i0 = np.minimum(np.floor(x).astype(int), n - 2)
    f = x - i0
    out = np.zeros(x.shape, dtype=np.float64)
    for dr in (0, 1):
        wr = f[..., 0] if dr else 1 - f[..., 0]
        for dg in (0, 1):
            wg = f[..., 1] if dg else 1 - f[..., 1]
            for db in (0, 1):
                wb = f[..., 2] if db else 1 - f[..., 2]
                w = (wr * wg * wb)[..., None]
                out += w * lut[i0[..., 2] + db, i0[..., 1] + dg, i0[..., 0] + dr]
    return out

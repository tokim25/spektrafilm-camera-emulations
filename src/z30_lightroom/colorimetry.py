"""ProPhoto (ROMM) RGB and CIELAB D50 conversions.

Both gates measure in CIELAB D50, the native white of ProPhoto RGB, so no
chromatic adaptation is needed between Lightroom's ProPhoto export and the
SpektraFilm ProPhoto reference.
"""
from __future__ import annotations

import numpy as np

# ROMM RGB (ProPhoto) to CIE XYZ, D50 white. ISO 22028-2 / ANSI/I3A IT10.7666.
PROPHOTO_TO_XYZ = np.array([
    [0.7976749, 0.1351917, 0.0313534],
    [0.2880402, 0.7118741, 0.0000857],
    [0.0000000, 0.0000000, 0.8252100],
])
D50_WHITE = PROPHOTO_TO_XYZ.sum(axis=1)  # [0.96422, 1.0, 0.82521]

# Adobe's ProPhoto RGB ICC profile, used by Lightroom exports, is a pure 1.8 power.
PROPHOTO_GAMMA = 1.8


def prophoto_decode(encoded):
    """Adobe ProPhoto-encoded [0, 1] values to linear light."""
    return np.clip(np.asarray(encoded, dtype=np.float64), 0.0, None) ** PROPHOTO_GAMMA


def prophoto_encode(linear):
    """Linear ProPhoto light to Adobe ProPhoto encoding, clipped to [0, 1]."""
    return np.clip(np.asarray(linear, dtype=np.float64), 0.0, 1.0) ** (1.0 / PROPHOTO_GAMMA)


def xyz_to_lab(xyz, white=D50_WHITE):
    t = np.asarray(xyz, dtype=np.float64) / np.asarray(white)
    d = 6.0 / 29.0
    f = np.where(t > d ** 3, np.cbrt(t), t / (3 * d * d) + 4.0 / 29.0)
    return np.stack([116 * f[..., 1] - 16,
                     500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])], axis=-1)


def prophoto_linear_to_lab(rgb):
    """Linear ProPhoto RGB to CIELAB D50."""
    return xyz_to_lab(np.asarray(rgb, dtype=np.float64) @ PROPHOTO_TO_XYZ.T)


def lab_chroma_hue(lab):
    lab = np.asarray(lab, dtype=np.float64)
    chroma = np.hypot(lab[..., 1], lab[..., 2])
    hue = np.mod(np.degrees(np.arctan2(lab[..., 2], lab[..., 1])), 360.0)
    return chroma, hue

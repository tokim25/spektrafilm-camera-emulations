"""sRGB/D65 to CIE Lab and vectorized CIEDE2000, no optional dependencies."""
from __future__ import annotations
import numpy as np

_D65 = np.array([0.95047, 1.0, 1.08883], dtype=float)
_RGB2XYZ = np.array([[.4124564, .3575761, .1804375],
                    [.2126729, .7151522, .0721750],
                    [.0193339, .1191920, .9503041]], dtype=float)


def srgb_to_lab(rgb):
    """Convert display-encoded sRGB floats [0,1] to CIE Lab (D65)."""
    rgb = np.asarray(rgb, dtype=np.float64)
    if rgb.shape[-1] != 3 or not np.all(np.isfinite(rgb)) or np.any(rgb < 0) or np.any(rgb > 1):
        raise ValueError("Expected finite encoded sRGB triplets in [0,1]")
    linear = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
    xyz = (linear @ _RGB2XYZ.T) / _D65
    delta = 6 / 29
    f = np.where(xyz > delta**3, np.cbrt(xyz), xyz / (3 * delta**2) + 4 / 29)
    return np.stack([116*f[..., 1]-16, 500*(f[..., 0]-f[..., 1]), 200*(f[..., 1]-f[..., 2])], axis=-1)


def delta_e_2000(lab_a, lab_b):
    """CIEDE2000, kL=kC=kH=1; handles zero-chroma axes and degree wrapping."""
    A, B = np.broadcast_arrays(np.asarray(lab_a, dtype=np.float64), np.asarray(lab_b, dtype=np.float64))
    if A.shape[-1] != 3 or np.any(~np.isfinite(A)) or np.any(~np.isfinite(B)):
        raise ValueError("Expected finite Lab arrays with final dimension 3")
    L1, a1, b1 = np.moveaxis(A, -1, 0)
    L2, a2, b2 = np.moveaxis(B, -1, 0)
    C1, C2 = np.hypot(a1,b1), np.hypot(a2,b2)
    Cm = (C1+C2)/2
    G = .5 * (1 - np.sqrt(Cm**7 / (Cm**7 + 25**7)))
    a1p, a2p = (1+G)*a1, (1+G)*a2
    C1p, C2p = np.hypot(a1p,b1), np.hypot(a2p,b2)
    h1 = np.mod(np.degrees(np.arctan2(b1,a1p)), 360)
    h2 = np.mod(np.degrees(np.arctan2(b2,a2p)), 360)
    dLp = L2-L1
    dCp = C2p-C1p
    dh = h2-h1
    dh = np.where(dh > 180, dh-360, np.where(dh < -180, dh+360, dh))
    dh = np.where(C1p*C2p == 0, 0, dh)
    dHp = 2*np.sqrt(C1p*C2p)*np.sin(np.radians(dh/2))
    Lm = (L1+L2)/2
    Cp = (C1p+C2p)/2
    absdiff = np.abs(h1-h2)
    hp = np.where(C1p*C2p==0, h1+h2,
          np.where(absdiff<=180, (h1+h2)/2,
          np.where(h1+h2 < 360, (h1+h2+360)/2, (h1+h2-360)/2)))
    T = 1-.17*np.cos(np.radians(hp-30)) + .24*np.cos(np.radians(2*hp)) \
         +.32*np.cos(np.radians(3*hp+6)) - .20*np.cos(np.radians(4*hp-63))
    dtheta = 30*np.exp(-((hp-275)/25)**2)
    Rc = 2*np.sqrt(Cp**7/(Cp**7+25**7))
    Sl = 1 + .015*(Lm-50)**2/np.sqrt(20+(Lm-50)**2)
    Sc = 1 + .045*Cp
    Sh = 1 + .015*Cp*T
    Rt = -np.sin(np.radians(2*dtheta))*Rc
    dL, dC, dH = dLp/Sl, dCp/Sc, dHp/Sh
    return np.sqrt(np.maximum(0, dL*dL + dC*dC + dH*dH + Rt*dC*dH))


def delta_e_srgb(a,b):
    return delta_e_2000(srgb_to_lab(a),srgb_to_lab(b))

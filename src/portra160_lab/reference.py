"""SpektraFilm reference rendering, invoked on a machine with SpektraFilm installed.

Input is already RAW-developed into scene-linear ProPhoto RGB; this function
never assumes that an arbitrary JPEG, NEF, or RAF is calibrated scene-linear data.
"""
from __future__ import annotations
import json
import importlib.metadata
from pathlib import Path
import numpy as np
from .stocks import supported_stock

def render(source: Path, dest: Path, mode: str = "color", stock: str = "portra160") -> dict:
    profile = supported_stock(stock)
    film, print_profile = profile["film"], profile["print"]
    if mode not in ("color", "full"):
        raise ValueError("mode must be color or full")
    src = np.load(source, allow_pickle=False)
    if src.ndim != 3 or src.shape[2] != 3 or not np.issubdtype(src.dtype, np.floating):
        raise ValueError("Input must be HxWx3 floating-point .npy scene-linear ProPhoto RGB")
    if np.any(~np.isfinite(src)) or np.any(src < 0):
        raise ValueError("Input contains negative or non-finite linear light")
    try:
        from spektrafilm import init_params, simulate
    except ImportError as exc:
        raise RuntimeError("Install pinned spektrafilm on Python 3.13 (see README)") from exc
    params = init_params(film_profile=film, print_profile=print_profile)
    params.io.input_color_space = "ProPhoto RGB"
    params.io.input_cctf_decoding = False
    params.io.output_color_space = "sRGB"
    params.io.output_cctf_encoding = True
    if mode == "color":
        # Fixed, deterministic pixel transform: spatial/stochastic effects, exposure
        # auto-adjustment and scanner auto-corrections disabled by spektrafilm.
        params.debug.lut_mode = True
    else:
        # Keep grain and halation, but disable per-image exposure automation.
        params.camera.auto_exposure = False
        params.enlarger.print_exposure_compensation = False
        params.camera.exposure_compensation_ev = 0.0
    result = np.asarray(simulate(src, params), dtype=np.float32)
    if result.shape != src.shape or np.any(~np.isfinite(result)):
        raise RuntimeError("Unexpected reference output shape or invalid values")
    dest.parent.mkdir(parents=True,exist_ok=True)
    np.save(dest,result,allow_pickle=False)
    dist = importlib.metadata.distribution("spektrafilm")
    direct_url = None
    try:
        direct_url = json.loads(dist.read_text("direct_url.json") or "")
    except (json.JSONDecodeError, OSError, TypeError):
        direct_url = None
    installed_commit = ((direct_url or {}).get("vcs_info") or {}).get("commit_id")
    expected_commit = "3bb2c2d2801ff68b92019cf1dbcbb133d60832bc"
    metadata = {
      "stock":stock,"film":film,"print":print_profile,"mode":mode,
      "input_color_space":"ProPhoto RGB", "input_encoding":"linear",
      "output_color_space":"sRGB", "output_encoding":"display-encoded",
      "spektrafilm_package_version":dist.version,
      "input_file":str(source),"output_file":str(dest),
      "input_shape":list(src.shape),"source_commit_expected":expected_commit,
      "source_commit_installed":installed_commit,
      "source_commit_verified_at_runtime":installed_commit == expected_commit,
      "warning":"Full mode has spatial/stochastic components; color mode is deterministic and suitable for color fitting. Scene-linear input is user-prepared and must be calibrated."
    }
    with open(dest.with_suffix('.json'),'w') as f:json.dump(metadata,f,indent=2)
    return metadata

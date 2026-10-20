"""Reproducible, *provisional* NEF/RAF -> linear ProPhoto development.

This is a usable ingestion path, not a substitute for a chart-measured camera
input profile. rawpy/LibRaw applies its embedded camera color matrices and
produces 16-bit RGB, so highlights can clip before SpektraFilm sees them.
Every output has an auditable, machine-readable sidecar recording this fact.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
from typing import Any
import numpy as np

SUPPORTED_EXTENSIONS = {'.nef', '.raf'}


def _hash_file(p: Path) -> str:
    h = sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def prepare_raw(source: Path, dest: Path, *, white_balance: str = 'camera',
                demosaic: str = 'AHD') -> dict[str, Any]:
    source, dest = Path(source), Path(dest)
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError('Only original Nikon .NEF and Fujifilm .RAF files are accepted')
    if dest.suffix.lower() != '.npy':
        raise ValueError('Output must be a .npy file, not a TIFF or JPEG')
    if white_balance not in ('camera', 'daylight'):
        raise ValueError('white_balance must be camera or daylight')
    if demosaic not in ('AHD', 'DCB'):
        raise ValueError('demosaic must be AHD or DCB')
    try:
        import rawpy
    except ImportError as exc:
        raise RuntimeError('Install the RAW extra: pip install -e ".[raw]"') from exc
    algorithm = getattr(rawpy.DemosaicAlgorithm, demosaic)
    raw = rawpy.imread(str(source))
    try:
        kwargs = dict(
            use_camera_wb=(white_balance == 'camera'),
            use_auto_wb=False,
            no_auto_bright=True,
            bright=1.0,
            gamma=(1.0, 1.0),  # display gamma OFF; scene-linear output
            output_color=rawpy.ColorSpace.ProPhoto,
            output_bps=16,
            demosaic_algorithm=algorithm,
            highlight_mode=rawpy.HighlightMode.Clip,
            exp_shift=1.0,
        )
        arr = raw.postprocess(**kwargs)
        cam_wb = [float(v) for v in raw.camera_whitebalance]
        day_wb = [float(v) for v in raw.daylight_whitebalance]
        black = [int(v) for v in raw.black_level_per_channel]
        white = int(raw.white_level)
    finally:
        raw.close()
    if arr.ndim != 3 or arr.shape[2] != 3 or arr.dtype != np.uint16:
        raise RuntimeError('Unexpected output from LibRaw: expected uint16 HxWx3')
    # 16-bit output is normalized to 0..1, retaining the linear-light encoding.
    out = arr.astype(np.float32) / 65535.0
    if np.any(~np.isfinite(out)):
        raise RuntimeError('Nonfinite RGB from LibRaw')
    dest.parent.mkdir(parents=True, exist_ok=True)
    np.save(dest, out, allow_pickle=False)
    clip_fraction = float(np.any(arr >= 65534, axis=2).mean())
    sidecar = {
        'format': 'spektrafilm-camera-linear-input-v1',
        'source_path': str(source),
        'source_sha256': _hash_file(source),
        'out_path': str(dest),
        'out_sha256': _hash_file(dest),
        'output_color_space': 'ProPhoto RGB',
        'output_encoding': 'scene-linear, 16-bit LibRaw converted to 32-bit float',
        'white_balance_mode': white_balance,
        'demosaic': demosaic,
        'camera_whitebalance': cam_wb,
        'daylight_whitebalance': day_wb,
        'raw_black_levels': black,
        'raw_white_level': white,
        'clipped_pixel_fraction': clip_fraction,
        'rawpy_version': importlib.metadata.version('rawpy'),
        'spektrafilm_ready': clip_fraction < 0.002,
        'true_camera_color_calibration_complete': False,
        'raw_processing_level': 'provisional_libraw_camera_matrix',
        'calibration_status': 'provisional_not_colorchecker_measured',
        'warning': (
            'A RAW source converted through LibRaw camera matrices, NOT a calibrated '
            'camera input profile. No automatic exposure or display gamma was applied. '
            '16-bit conversion may clip highlights; inspect clipped_pixel_fraction. '
            'For final maximum-fidelity validation develop RAWs through a measured '
            'DCP/ICC profile to unclipped float TIFF/EXR and import as scene-linear.'
        ),
    }
    dest.with_suffix('.json').write_text(json.dumps(sidecar, indent=2) + '\n', encoding='utf-8')
    return sidecar

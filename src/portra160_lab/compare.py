"""Convenience one-scene image comparison; always reports no held-out validation."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from .experiments import extract_patches, measure


def _sha256(path: Path) -> str:
    h=sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):
            h.update(data)
    return h.hexdigest()


def compare_scene(reference: Path, candidate: Path, regions: Path, output: Path,
                  *,camera:str,stock:str='portra160',assume_srgb:bool=False) -> dict:
    """Compare aligned camera/reference renderings of ONE RAW scene.

    No color matching can be asserted from a one-scene fit, even if error=0.
    Never compares Zf output to a different Fuji scene.
    """
    if camera not in ('Nikon Zf','Fujifilm X100V'):
        raise ValueError('camera must be Nikon Zf or Fujifilm X100V')
    src=extract_patches(Path(reference),Path(regions),stock=stock,assume_srgb=assume_srgb)
    actual=extract_patches(Path(candidate),Path(regions),stock=stock,assume_srgb=assume_srgb)
    results=measure(src,actual)
    out={
       'kind':'spektrafilm-one-scene-camera-comparison-v1',
       'stock':stock,'camera':camera,
       'reference':str(reference),'reference_sha256':_sha256(reference),
       'candidate':str(candidate),'candidate_sha256':_sha256(candidate),
       'regions':str(regions),'regions_sha256':_sha256(regions),
       'statistics':results,
       'color_match_verified':False,'camera_file_import_verified':False,
       'held_out_validation_complete':False,
       'warning':('These patches compare ONE pair of spatially aligned images. '
          'They do not prove the candidate uses correct Kodak film stock settings, '
          'nor that a native recipe was accepted by camera hardware. '
          'Run on separate withheld RAW scenes before claiming accuracy.'),
    }
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    return out

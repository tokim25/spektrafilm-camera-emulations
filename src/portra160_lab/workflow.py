"""End-to-end SpektraFilm reference execution from original camera RAW.

No camera look is invented here; this produces the *reference* that candidates
must be measured against, not an NP3 or Fujifilm custom settings recipe.
"""
from __future__ import annotations
import json
from pathlib import Path
from .raw_pipeline import prepare_raw
from .reference import render
from .stocks import supported_stock


def render_raw(source: Path, out: Path, *, stock: str='portra160', mode: str='color',
               white_balance: str='camera', demosaic:str='AHD',
               permit_clipping: bool=False) -> dict:
    supported_stock(stock)
    source=Path(source)
    out=Path(out)
    if out.suffix.lower() != '.npy':
        raise ValueError('Reference output must be a .npy path')
    linear=out.with_name(out.stem+'_raw_linear_prophoto.npy')
    prepared=prepare_raw(source,linear,white_balance=white_balance,demosaic=demosaic)
    if not permit_clipping and not prepared['spektrafilm_ready']:
        raise ValueError(
            'RAW development has clipped more than 0.2% of the image. The unclipped '
            'source and its processing manifest were preserved. Change exposure/scene '
            'or use a float RAW developer. Use --permit-clipping to explicitly override.'
        )
    ref=render(linear,out,mode,stock=stock)
    result={'kind':'camera-lab-reference-run-v1',
            'source_raw':str(source),
            'linear_input_manifest':str(linear.with_suffix('.json')),
            'spektrafilm_reference_manifest':str(out.with_suffix('.json')),
            'reference_output':str(out),
            'stock':stock, 'film':ref['film'],'print':ref['print'],
            'mode':mode,'raw_preprocessing':prepared,
            'camera_native_recipe_generated':False,
            'camera_native_fidelity_validated':False}
    out.with_name(out.stem+'_run.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result

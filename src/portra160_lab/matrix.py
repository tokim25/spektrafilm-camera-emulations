"""Render a reproducible matrix of supported SpektraFilm references."""
from __future__ import annotations
import json
from pathlib import Path
from .reference import render
from .stocks import all_stocks, supported_stock

def render_matrix(source: Path, out_dir: Path, *, stocks: list[str] | None = None) -> dict:
    source, out_dir = Path(source), Path(out_dir)
    keys = stocks or [k for k,v in all_stocks().items() if v.get('status') == 'upstream_profile_available']
    if not keys: raise ValueError('At least one supported stock is required')
    records=[]
    for key in keys:
        profile=supported_stock(key)
        dest=out_dir/f'{key}.npy'
        meta=render(source,dest,mode='color',stock=key)
        records.append({'stock':key,'film':profile['film'],'print':profile['print'],'output':str(dest),'metadata':str(dest.with_suffix('.json')),'source_commit_verified':meta['source_commit_verified_at_runtime']})
    manifest={'kind':'spektrafilm-reference-matrix-v1','input':str(source),'mode':'color','records':records,'camera_recipe_generated':False,'camera_validation_completed':False}
    out_dir.mkdir(parents=True,exist_ok=True)
    (out_dir/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

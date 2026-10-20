"""Suggest the NEXT settings to measure from real camera-response experiments.

This is an empirical LOCAL LINEAR SURROGATE for the camera's controls, not an
NP3 or Fujifilm rendering engine. It never certifies fidelity from predictions.
Camera responses must be supplied by actual renders of the same camera RAW.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .color import srgb_to_lab, delta_e_2000
from .experiments import _validate, measure
from .fuji_x100v import format_recipe, validate
from .nikon_np3 import serialize


def _lab_patches(rec: dict, names: list[str]) -> np.ndarray:
    vals = _validate(rec)
    if set(vals) != set(names):
        raise ValueError('All measured probe patches must have identical patch IDs')
    return srgb_to_lab(np.stack([vals[name]['rgb'] for name in names]))


def _set_deep(o: dict, path: tuple[str,...], value: Any) -> None:
    for name in path[:-1]:
        o = o.setdefault(name, {})
    o[path[-1]] = value


def _leaf_numeric_settings(obj: dict, prefix: tuple[str,...]=()) -> dict[tuple[str,...],float]:
    leaves={}
    for k,v in obj.items():
        if k in ('name','validated_on_camera','comment'):
            continue
        p=prefix+(k,)
        if isinstance(v,dict):
            leaves.update(_leaf_numeric_settings(v,p))
        elif type(v) in (float,int):
            leaves[p]=float(v)
    return leaves


def _flatten_probes(base: dict, probes: list[tuple[dict,float]]) -> dict:
    opts=deepcopy(base)
    b=_leaf_numeric_settings(base)
    paths=set(b)
    for s,_ in probes:
        paths |= set(_leaf_numeric_settings(s))
    for path in paths:
        # Default missing numerical controls to 0, but don't synthesize a
        # missing white-balance Kelvin or unrelated categorical controls.
        if path[-1] == 'kelvin' and path not in b:
            continue
        val=b.get(path,0.0)
        for s,coef in probes:
            val += coef * (_leaf_numeric_settings(s).get(path,b.get(path,0.0)) - b.get(path,0.0))
        _set_deep(opts,path,int(round(val)))
    return opts


def _weighted_fit(reference:dict, base:dict, differences:list[np.ndarray], *, regularization:float):
    names=sorted(_validate(reference))
    ref=_validate(reference)
    weights={'skin':3.,'neutral':2.,'highlight':2.,'shadow':1.5,'general':1.}
    w=np.array([weights.get(ref[p]['category'],1.) for p in names],dtype=np.float64)
    W=np.repeat(np.sqrt(w),3)
    initial=_lab_patches(base,names)
    target=_lab_patches(reference,names)
    A=np.stack([d.flatten() for d in differences],axis=1)
    b=(target-initial).flatten()
    A=np.vstack([A*W[:,None],np.sqrt(regularization)*np.eye(len(differences))])
    b=np.concatenate([b*W,np.zeros(len(differences))])
    coef=np.linalg.lstsq(A,b,rcond=None)[0]
    # Proposals stay within the size of observed perturbations: extrapolation
    # without validation isn't justified as an optimized recipe.
    coef=np.clip(coef,-1,1)
    estimate=initial + np.stack(differences,axis=0).transpose(1,2,0)@coef
    return coef, float(np.mean(delta_e_2000(target,estimate))),float(np.mean(delta_e_2000(target,initial)))


def fit_probes(reference_path: Path,kit_path:Path,observations:Path,out:Path,*,camera:str,regularization:float=10.0) -> dict:
    """Use measured probe charts to create a *next test candidate*.

    Required: kit manifest + patch files named LABxx.json in
    `observations/{nikon_zf|fujifilm_x100v}`. For X100V, numeric adjustments
    are restricted to PROVIA where their actual effects have been sampled.
    Unknown or missing probe files are ignored; at least two observations,
    including baseline, are necessary. The result is not a validated look.
    """
    if camera not in ('zf','x100v'):
        raise ValueError('camera must be zf or x100v')
    if not np.isfinite(regularization) or regularization < 0:
        raise ValueError('regularization must be a nonnegative finite number')
    camdir='nikon_zf' if camera=='zf' else 'fujifilm_x100v'
    label='Nikon Zf' if camera=='zf' else 'Fujifilm X100V'
    key=f'{camdir}_probes'
    manifest=json.loads((Path(kit_path)/'manifest.json').read_text('utf-8'))
    if manifest.get('kind')!='camera-response-probe-kit-v1':
        raise ValueError('Invalid diagnostic probe manifest')
    reference=json.loads(Path(reference_path).read_text('utf-8'))
    if reference.get('stock','portra160')!=manifest['target_stock']:
        raise ValueError('Reference and camera probe kit film stocks do not match')
    _validate(reference)
    observed=[]
    for item in manifest[key]:
        path=Path(observations)/camdir/f"{item['settings']['name']}.json"
        if not path.is_file():continue
        rec=json.loads(path.read_text('utf-8'))
        rec.setdefault('stock',manifest['target_stock'])
        rec.setdefault('format','portra160-patches-v1')
        if rec.get('stock')!=manifest['target_stock']:
            raise ValueError(f'Observation stock mismatch for {path}')
        # Explicit pairwise validation checks all patch ids and RGB bounds.
        measure(reference,rec)
        observed.append((item,rec,path))
    base=next(((m,r,p) for m,r,p in observed if m['index']==1),None)
    if base is None:
        raise ValueError(f'Missing measured {label} LAB01 baseline')
    if len(observed)<2:
        raise ValueError(f'Need measured base and at least one modified {label} probe. Found {len(observed)}.')
    (base_meta,base_rec,base_path)=base
    if camera=='x100v':
        # The other three baseline simulations remain separately rankable.
        # Only PROVIA has perturbed color/tonal controls in the probe kit.
        relevant=[(m,r,p) for m,r,p in observed if m['index']>=5]
    else:
        relevant=[(m,r,p) for m,r,p in observed if m['index']>=2]
    if not relevant:
        raise ValueError(f'No numeric perturbation measurements for {label}')
    names=sorted(_validate(reference))
    base_lab=_lab_patches(base_rec,names)
    differences=[_lab_patches(r,names)-base_lab for _,r,_ in relevant]
    if any(not np.any(np.abs(d)>1e-7) for d in differences):
        raise ValueError('At least one supposedly changed probe has unchanged measured patches. Recheck renders.')
    coefs,pred_error,base_error=_weighted_fit(reference,base_rec,differences,regularization=regularization)
    opts=_flatten_probes(base_meta['settings'],[(m['settings'],float(c)) for (m,r,p),c in zip(relevant,coefs)])
    opts['name']='LABNEXT'
    if camera=='zf':
        raw=serialize(opts)
        candidate_path=Path(out)/'PICCON10.NP3'
    else:
        validate(opts)
        raw=format_recipe(opts).encode('utf-8')
        candidate_path=Path(out)/'X100V_LABNEXT.txt'
    candidate_path.parent.mkdir(parents=True,exist_ok=True)
    candidate_path.write_bytes(raw)
    result={
        'kind':'camera-color-proposal-v1','target_stock':manifest['target_stock'],
        'camera':label,'source_reference':str(reference_path),'source_kit':str(kit_path),
        'measured_baseline':str(base_path),
        'measured_perturbations':[{ 'experiment':m['experiment'], 'path':str(p), 'coefficient':float(c)} for (m,r,p),c in zip(relevant,coefs)],
        'settings':opts,'new_candidate_file':str(candidate_path),
        'sha256':hashlib.sha256(raw).hexdigest(),
        'baseline_mean_deltaE00':base_error,
        'predicted_training_mean_deltaE00':pred_error,
        'camera_render_verified':False,'spektrafilm_fidelity_verified':False,
        'warning':'Local linear surrogate estimate ONLY. Candidate must be rendered on the actual camera engine, measured, and tested on independent scenes before using as a film emulation. Predicted training error is not camera fidelity.',
    }
    (Path(out)/'proposal.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result

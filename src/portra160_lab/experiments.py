"""Measure color chart regions and rank actual camera-rendered recipe candidates.

No theoretical recipe-fitting claims: rankings require measured, aligned outputs.
"""
from __future__ import annotations
import io
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageCms
from .color import delta_e_srgb
from .stocks import supported_stock


def extract_patches(image_path: Path, region_file: Path, *, assume_srgb=False, stock="portra160") -> dict:
    """Extract center patches; `.npy` is encoded sRGB float, photos require ICC.

    Rectangles must be created independently for each geometrically aligned image.
    Array inputs are deliberately *not* scene-linear data; use reference rendering
    first to get display-encoded sRGB before applying this function.
    """
    supported_stock(stock)
    regions = json.loads(region_file.read_text())
    if not isinstance(regions.get("patches"),list) or not regions["patches"]:
        raise ValueError("Region file must contain patches array")
    if image_path.suffix.lower()=='.npy':
        pixels = np.load(image_path,allow_pickle=False).astype(np.float64)
        provenance = "npy assumed display-encoded sRGB per pipeline contract"
    else:
        with Image.open(image_path) as f:
            icc=f.info.get('icc_profile')
            if icc:
                src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
                dst = ImageCms.createProfile('sRGB')
                converted = ImageCms.profileToProfile(f.convert('RGB'),src,dst,outputMode='RGB')
                provenance = 'source ICC profile converted to sRGB'
            elif assume_srgb:
                converted = f.convert('RGB')
                provenance = 'unprofiled image assumed sRGB by explicit user flag'
            else:
                raise ValueError("Photo lacks ICC profile. Pass --assume-srgb only if you know the encoding.")
            pixels=np.asarray(converted,dtype=np.float64)/255.0
    if pixels.ndim!=3 or pixels.shape[-1]!=3 or not np.all(np.isfinite(pixels)):
        raise ValueError('Expected HxWx3 finite RGB image')
    h,w,_=pixels.shape
    found=set()
    result=[]
    for p in regions['patches']:
        key=p['id']
        if not isinstance(key,str) or not key or key in found:
            raise ValueError('Non-empty patch IDs must be unique')
        found.add(key)
        box=p['box']
        if len(box)!=4 or any(isinstance(z,bool) or not isinstance(z,int) for z in box):
            raise ValueError(f'{key}: integer box [x1,y1,x2,y2] required')
        x1,y1,x2,y2=box
        if not (0<=x1<x2<=w and 0<=y1<y2<=h):
            raise ValueError(f'{key}: rectangle outside image')
        roi=pixels[y1:y2,x1:x2]
        rgb=np.median(roi,axis=(0,1))
        if np.any(rgb<0) or np.any(rgb>1):
            raise ValueError(f'{key}: out-of-gamut encoded output; resolve color management first')
        result.append({'id':key,'category':p.get('category','general'),'rgb':rgb.tolist(),
                       'sample_count':int(roi.shape[0]*roi.shape[1])})
    return {'format':'portra160-patches-v1','stock':stock,'source':str(image_path),
            'color_space':'sRGB','encoding':'display-encoded','provenance':provenance,
            'patches':result}


def _validate(record):
    if record.get('color_space')!='sRGB' or record.get('encoding')!='display-encoded':
        raise ValueError('Only display-encoded sRGB patch files are supported')
    patches=record.get('patches')
    if not isinstance(patches,list) or len(patches)==0:
        raise ValueError('Missing patches')
    m={}
    for p in patches:
        k=p['id']
        if not isinstance(k,str) or not k or k in m:
            raise ValueError('Duplicate or empty patch identifier')
        rgb=np.asarray(p['rgb'], dtype=float)
        if rgb.shape!=(3,) or not np.all(np.isfinite(rgb)) or np.any(rgb<0) or np.any(rgb>1):
            raise ValueError(f'{k}: RGB must be three finite sRGB values [0,1]')
        m[k]={'rgb':rgb,'category':p.get('category','general')}
    return m


def measure(reference: dict, candidate: dict) -> dict:
    if reference.get('format')!='portra160-patches-v1' or candidate.get('format')!='portra160-patches-v1':
        raise ValueError('Unsupported or missing patch format')
    ref_stock=reference.get('stock','portra160')
    if candidate.get('stock','portra160')!=ref_stock:
        raise ValueError('Cannot compare patches generated for different film stocks')
    supported_stock(ref_stock)
    ref,cam=_validate(reference),_validate(candidate)
    if set(ref)!=set(cam):
        raise ValueError(f'Patch IDs differ: missing={sorted(set(ref)-set(cam))}, extra={sorted(set(cam)-set(ref))}')
    ids=sorted(ref)
    a=np.array([ref[k]['rgb'] for k in ids]);b=np.array([cam[k]['rgb'] for k in ids])
    e=np.asarray(delta_e_srgb(a,b),dtype=float)
    # Category weights are explicit so priority can be adjusted with real validation.
    weights={'skin':3.,'neutral':2.,'highlight':2.,'shadow':1.5,'general':1.}
    ww=np.array([weights.get(ref[k]['category'],1.) for k in ids])
    by_cat={}
    for c in sorted(set(ref[k]['category'] for k in ids)):
        sel=np.array([ref[k]['category']==c for k in ids]);by_cat[c]=float(e[sel].mean())
    return {'weighted_mean_deltaE00':float(np.average(e,weights=ww)),
            'mean_deltaE00':float(e.mean()),'median_deltaE00':float(np.median(e)),
            'p95_deltaE00':float(np.percentile(e,95)), 'max_deltaE00':float(e.max()),
            'by_category_mean_deltaE00':by_cat,'patch_count':len(ids),
            'per_patch':[{'id':k,'category':ref[k]['category'],'deltaE00':float(v)} for k,v in zip(ids,e)]}


def rank(reference_path: Path, candidate_paths: list[Path]) -> dict:
    reference=json.loads(reference_path.read_text())
    profile=supported_stock(reference.get('stock','portra160'))
    if not candidate_paths:raise ValueError('At least one candidate needed')
    scored=[]
    for path in candidate_paths:
        cand=json.loads(path.read_text())
        if cand.get('camera') not in ('Nikon Zf','Fujifilm X100V'):
            raise ValueError(f'{path}: candidate camera must be Nikon Zf or Fujifilm X100V')
        stats=measure(reference,cand)
        scored.append({'name':cand.get('name',path.stem),'camera':cand['camera'],
                       'settings':cand.get('settings',{}),'source':str(path), 'statistics':stats})
    # Candidate rankings are camera-specific; never compare one camera's rank to another's.
    groups={}
    for s in scored:groups.setdefault(s['camera'],[]).append(s)
    for k in groups:groups[k].sort(key=lambda c:c['statistics']['weighted_mean_deltaE00'])
    return {'stock':reference.get('stock','portra160'),'film':profile['film'],'print':profile['print'],
            'status':'measured candidate comparison; no unseen camera tests inferred',
            'ranking_key':'weighted_mean_deltaE00 (lower is better)',
            'category_weights':{'skin':3,'neutral':2,'highlight':2,'shadow':1.5,'general':1},
            'ranked_by_camera':groups}

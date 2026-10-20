"""Portra 160 calibration CLI."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .experiments import extract_patches, rank
from .reference import render
from .stocks import all_stocks
from .nikon_np3 import export_file as export_nikon
from .fuji_x100v import export_file as export_fuji
from .probe_kit import create_probe_kit
from .fit_probes import fit_probes
from .raw_pipeline import prepare_raw
from .phase1 import phase1_status
from .compare import compare_scene
from .workflow import render_raw
from .matrix import render_matrix


def main(argv=None):
    ap=argparse.ArgumentParser(prog='portra160-lab')
    sp=ap.add_subparsers(dest='action',required=True)
    p=sp.add_parser('render',help='Run SpektraFilm on prepared scene-linear ProPhoto RGB .npy')
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--mode',choices=['color','full'],default='color')
    p.add_argument('--stock',default='portra160',help='Film stock key. Use list-stocks to see availability')
    sp.add_parser('list-stocks',help='Show available and missing SpektraFilm profiles')
    p=sp.add_parser('render-raw',help='Original NEF/RAF -> linear ProPhoto -> SpektraFilm reference (requires rawpy + SpektraFilm)')
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--stock',default='portra160')
    p.add_argument('--mode',choices=['color','full'],default='color')
    p.add_argument('--white-balance',choices=['camera','daylight'],default='camera')
    p.add_argument('--demosaic',choices=['AHD','DCB'],default='AHD')
    p.add_argument('--permit-clipping',action='store_true')
    p=sp.add_parser('compare-scene',help='Score one camera JPG against aligned SpektraFilm reference')
    p.add_argument('--reference',required=True,type=Path)
    p.add_argument('--candidate',required=True,type=Path)
    p.add_argument('--regions',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--camera',choices=['Nikon Zf','Fujifilm X100V'],required=True)
    p.add_argument('--stock',default='portra160')
    p.add_argument('--assume-srgb',action='store_true')
    p=sp.add_parser('phase1-status',help='Read the real Phase 1 release gates; no fake camera-validation claim')
    p.add_argument('--workspace',type=Path,default=Path('.'))
    p=sp.add_parser('prepare-raw',help='Provisional .NEF/.RAF RAW -> scene-linear ProPhoto .npy (needs rawpy)')
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--white-balance',choices=['camera','daylight'],default='camera')
    p.add_argument('--demosaic',choices=['AHD','DCB'],default='AHD')
    p=sp.add_parser('probe-kit',help='Generate neutral diagnostic camera-response tests (NOT film looks)')
    p.add_argument('--out',type=Path,required=True,help='Output directory; will not replace an existing directory by default')
    p.add_argument('--stock',default='portra160')
    p.add_argument('--overwrite',action='store_true',help='Replace only a directory created as a probe kit')
    p=sp.add_parser('fit-probes',help='Suggest next candidate from measured camera responses (NOT validated fidelity)')
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--kit',type=Path,required=True)
    p.add_argument('--observations',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--camera',choices=['zf','x100v'],required=True)
    p=sp.add_parser('zf-export',help='Serialize Nikon NP3 calibration candidate (not color-validated)')
    p.add_argument('--settings',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--experimental',action='store_true',help='Acknowledge camera import and film-match are unverified')
    p=sp.add_parser('x100v-export',help='Format validated X100V custom-setting candidate (manual entry)')
    p.add_argument('--settings',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--experimental',action='store_true',help='Acknowledge camera match is unverified')
    p=sp.add_parser('extract',help='Sample sRGB patches from a measured image')
    p.add_argument('--image',required=True,type=Path)
    p.add_argument('--regions',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--assume-srgb',action='store_true')
    p.add_argument('--stock',default='portra160',help='Film stock for reference/candidate patches')
    p=sp.add_parser('rank',help='Rank real candidate camera renders against the SpektraFilm reference')
    p.add_argument('--reference',required=True,type=Path)
    p.add_argument('--candidates',required=True,nargs='+',type=Path)
    p.add_argument('--out',required=True,type=Path)
    p=sp.add_parser('render-matrix',help='Render all or selected upstream film/print references')
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--out-dir',required=True,type=Path)
    p.add_argument('--stocks',nargs='*',default=None)
    args=ap.parse_args(argv)
    if args.action=='render-raw':
        print(json.dumps(render_raw(args.input,args.out,stock=args.stock,mode=args.mode,white_balance=args.white_balance,demosaic=args.demosaic,permit_clipping=args.permit_clipping),indent=2));return 0
    if args.action=='compare-scene':
        result=compare_scene(args.reference,args.candidate,args.regions,args.out,camera=args.camera,stock=args.stock,assume_srgb=args.assume_srgb)
        print(json.dumps(result,indent=2));return 0
    if args.action=='phase1-status':
        print(json.dumps(phase1_status(args.workspace),indent=2));return 0
    if args.action=='prepare-raw':
        print(json.dumps(prepare_raw(args.input,args.out,white_balance=args.white_balance,demosaic=args.demosaic),indent=2));return 0
    if args.action=='fit-probes':
        result=fit_probes(args.reference,args.kit,args.observations,args.out,camera=args.camera)
        print(json.dumps(result,indent=2));return 0
    if args.action=='probe-kit':
        report=create_probe_kit(args.out,stock=args.stock,overwrite=args.overwrite)
        print(json.dumps({'path':str(args.out),'target':report['target_stock'],
            'nikon_probes':len(report['nikon_zf_probes']),
            'fujifilm_probes':len(report['fujifilm_x100v_probes']),
            'warning':'Diagnostic camera response probes, NOT film emulations. Camera import unverified.'},indent=2))
        return 0
    if args.action=='list-stocks':
        print(json.dumps(all_stocks(),indent=2));return 0
    if args.action=='render-matrix':
        print(json.dumps(render_matrix(args.input,args.out_dir,stocks=args.stocks),indent=2));return 0
    if args.action=='zf-export':
        result=export_nikon(args.settings,args.out,experimental=args.experimental)
        print(json.dumps(result,indent=2));return 0
    if args.action=='x100v-export':
        result=export_fuji(args.settings,args.out,experimental=args.experimental)
        print(json.dumps(result,indent=2));return 0
    if args.action=='render':
        result=render(args.input,args.out,args.mode,stock=args.stock)
        print(json.dumps(result,indent=2));return 0
    if args.action=='extract':
        result=extract_patches(args.image,args.regions,assume_srgb=args.assume_srgb,stock=args.stock)
    else:
        result=rank(args.reference,args.candidates)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(f'Wrote {args.out}')
    return 0

if __name__=='__main__':raise SystemExit(main())

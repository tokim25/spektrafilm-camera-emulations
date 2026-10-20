"""Reproducible, neutral *camera-response experiments*, not film looks.

The experiments identify how Zf NP3 sliders and X100V's restricted presets
move observed output. SpektraFilm reference fitting begins only after these
experiments have been rendered on the camera's own pipeline and measured.
"""
from __future__ import annotations

import json
import hashlib
import shutil
from pathlib import Path

from .fuji_x100v import format_recipe, validate
from .nikon_np3 import serialize
from .stocks import supported_stock

Z_F_PROBES: tuple[tuple[str, dict], ...] = (
    ('BASE', {}),
    ('CONTRAST_PLUS', {'contrast': 30}),
    ('CONTRAST_MINUS', {'contrast': -30}),
    ('SAT_PLUS', {'saturation': 25}),
    ('SAT_MINUS', {'saturation': -25}),
    ('RED_CHROMA_PLUS', {'colorBlender': {'red': {'chroma': 40}}}),
    ('GREEN_CHROMA_MINUS', {'colorBlender': {'green': {'chroma': -40}}}),
    ('BLUE_CHROMA_PLUS', {'colorBlender': {'blue': {'chroma': 40}}}),
    ('SHADOW_BRIGHT_PLUS', {'colorGrading': {'shadows': {'brightness': 25}}}),
)

# We make baseline control differences explicit, don't use other people's
# recipes, and keep the camera at its base native ISO / DR100 for comparison.
FUJI_PROBES: tuple[tuple[str, dict], ...] = (
    ('PROVIA_BASE', {'film_simulation': 'PROVIA'}),
    ('ASTIA_BASE', {'film_simulation': 'ASTIA'}),
    ('CLASSIC_CHROME_BASE', {'film_simulation': 'CLASSIC CHROME'}),
    ('PRO_NEG_STD_BASE', {'film_simulation': 'PRO NEG. STD'}),
    ('PROVIA_COLOR_PLUS', {'film_simulation': 'PROVIA', 'color': 3}),
    ('PROVIA_TONE_PLUS', {'film_simulation': 'PROVIA', 'highlight': 2, 'shadow': 2}),
    ('PROVIA_WB_SHIFT', {'film_simulation': 'PROVIA', 'white_balance': {'mode': 'DAYLIGHT','red': 4,'blue': -4}}),
)

FUJI_BASE = {
    'film_simulation': 'PROVIA', 'dynamic_range': 100, 'dr_priority': 'OFF',
    'highlight': 0, 'shadow': 0, 'color': 0,
    'sharpness': 0, 'noise_reduction': 0, 'clarity': 0,
    'grain_roughness': 'OFF', 'grain_size': 'SMALL',
    'color_chrome': 'OFF', 'color_chrome_blue': 'OFF',
    'white_balance': {'mode': 'DAYLIGHT', 'red': 0, 'blue': 0}, 'iso': 160,
}


def _save(path: Path, data: bytes) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {'path': str(path), 'size_bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def create_probe_kit(destination: Path, *, stock: str='portra160', overwrite: bool=False) -> dict:
    """Build a 9-NP3 / 7-manual-recipe response characterization kit.

    Emits complete experiment metadata and exact settings. No camera state is
    touched and no claim of a SpektraFilm look is made. Only supports
    existing upstream film profiles as fitting targets.
    """
    profile = supported_stock(stock)
    dest = Path(destination)
    if dest.exists():
        if not overwrite:
            raise FileExistsError(f'{dest} already exists; use --overwrite only if safe')
        if not dest.is_dir():
            raise ValueError('Probe output must be a directory')
        # Avoid deleting unrelated files. Overwrite only an existing probe kit.
        manifest = dest / 'manifest.json'
        if not manifest.exists() or json.loads(manifest.read_text()).get('kind') != 'camera-response-probe-kit-v1':
            raise ValueError('Refusing to overwrite a directory that is not our probe kit')
        shutil.rmtree(dest)
    dest.mkdir(parents=True,exist_ok=True)
    nikon = []
    fuji = []
    for index,(kind,changes) in enumerate(Z_F_PROBES,1):
        opts={'name':f'LAB{index:02d}', **changes}
        data=serialize(opts)
        target=dest/'nikon_zf'/'NIKON'/'CUSTOMPC'/f'PICCON{index:02d}.NP3'
        audit=_save(target,data)
        audit['path']=str(target.relative_to(dest))
        nikon.append({'index':index,'experiment':kind,'settings':opts,**audit})
    for index,(kind,changes) in enumerate(FUJI_PROBES,1):
        opts={**FUJI_BASE,**changes,'name':f'LAB{index:02d}'}
        validate(opts)
        target=dest/'fujifilm_x100v'/f'C{index:02d}_{kind}.txt'
        audit=_save(target,format_recipe(opts).encode('utf-8'))
        audit['path']=str(target.relative_to(dest))
        fuji.append({'index':index,'experiment':kind,'settings':opts,**audit})
    report={
        'kind':'camera-response-probe-kit-v1','target_stock':stock,
        'target_film_profile':profile['film'],'target_print_profile':profile['print'],
        'scope':'measuring the camera response to changes, NOT fitted film emulations',
        'camera_import_verified':False,'color_match_verified':False,
        'nikon_zf_probes':nikon,'fujifilm_x100v_probes':fuji,
        'next_action':'Render SAME RAW under each candidate in NX Studio / X RAW Studio. '
                      'Extract corresponding sRGB patches and optimize toward actual SpektraFilm reference.',
    }
    (dest/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (dest/'READ_THIS_FIRST.txt').write_text(
        'CAMERA RESPONSE TEST KIT - NOT PORTRA 160 PRESETS\n\n'
        'These files are diagnostic tests to help us measure Nikon Zf and Fujifilm X100V rendering.\n'
        'They do not reproduce Kodak Portra 160 yet. No camera import has been tested.\n\n'
        'NIKON Zf:\n'
        '1. Back up current custom Picture Controls. Insert a camera-formatted card into your Mac.\n'
        '2. Transfer test files from nikon_zf/NIKON/CUSTOMPC to NIKON/CUSTOMPC on the card.\n'
        '3. Import only into empty custom Picture Control slots, never overwrite favorites.\n'
        '4. If the camera rejects any file, stop and report its filename; do not flash firmware.\n'
        '5. Create one common NEF and develop it once with each trial in Nikon NX Studio.\n\n'
        'FUJIFILM X100V:\n'
        '1. Back up all C1-C7 recipe values and do NOT assume you can auto-import these.\n'
        '2. Read the text files and enter them manually in spare custom slots.\n'
        '3. Reprocess a common RAF through X RAW Studio for each candidate when possible.\n'
        '4. Use a fixed exposure and WB; for accurate white-balance characterization\n'
        '   record the differences between camera and RAW Studio controls.\n\n'
        'All comparisons should use the same RAW capture per camera.\n'
        'Sharing photos between different camera models is not a true matched RAW test.\n'
        'Source research: https://github.com/andreavolpato/spektrafilm\n',
        encoding='utf-8')
    return report

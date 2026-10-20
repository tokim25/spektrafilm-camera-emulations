"""Validate and format X100V camera-native test settings.

Does not invent settings: a fit/measurement process must supply values.
Reference controls: Fujifilm official X100V Image Quality manual.
"""
from __future__ import annotations
import json
from pathlib import Path

FILM_SIMULATIONS={
    'PROVIA','VELVIA','ASTIA','CLASSIC CHROME','PRO NEG. HI','PRO NEG. STD',
    'CLASSIC NEG.','ETERNA','ACROS','MONOCHROME','SEPIA',
}


def validate(settings: dict) -> dict:
    if not isinstance(settings,dict):raise ValueError('Settings must be a JSON object')
    keys={'name','film_simulation','dynamic_range','dr_priority','highlight','shadow','color',
          'sharpness','noise_reduction','clarity','grain_roughness','grain_size',
          'color_chrome','color_chrome_blue','white_balance','iso'}
    if set(settings)-keys:raise ValueError(f'Unknown X100V controls: {sorted(set(settings)-keys)}')
    if not isinstance(settings.get('name'),str) or not settings['name'].strip():
        raise ValueError('Custom setting needs a nonempty name')
    sim=settings.get('film_simulation')
    if sim not in FILM_SIMULATIONS:
        raise ValueError('Choose one X100V-supported base film simulation')
    dr=settings.get('dynamic_range',100)
    if dr not in (100,200,400):raise ValueError('X100V dynamic_range must be 100, 200, or 400')
    priority=settings.get('dr_priority','OFF')
    if priority!='OFF':
        raise ValueError('Only D RANGE PRIORITY OFF is supported for controlled contrast fitting')
    for field,lo,hi in [
        ('highlight',-2,4),('shadow',-2,4),('color',-4,4),
        ('sharpness',-4,4),('noise_reduction',-4,4),('clarity',-5,5),
    ]:
        v=settings.get(field,0)
        if type(v)!=int or not lo<=v<=hi:
            raise ValueError(f'{field} must be an integer from {lo} to {hi}')
    rough=settings.get('grain_roughness','OFF')
    if rough not in ('OFF','WEAK','STRONG'):raise ValueError('Invalid grain roughness')
    if settings.get('grain_size','SMALL') not in ('SMALL','LARGE'):
        raise ValueError('Invalid grain size')
    for key in ('color_chrome','color_chrome_blue'):
        if settings.get(key,'OFF') not in ('OFF','WEAK','STRONG'):
            raise ValueError(f'{key} must be OFF, WEAK, or STRONG')
    if sim in ('ACROS','MONOCHROME','SEPIA') and settings.get('color',0)!=0:
        raise ValueError('COLOR is unavailable or meaningless for monochrome base simulations')
    wb=settings.get('white_balance')
    if not isinstance(wb,dict) or set(wb)-{'mode','kelvin','red','blue'}:
        raise ValueError('white_balance needs mode, kelvin (if K), and red/blue shifts')
    if wb.get('mode') not in ('K','DAYLIGHT','AUTO'):
        raise ValueError('white_balance mode must be K, DAYLIGHT or AUTO')
    if wb.get('mode')=='K':
        # The manufacturer describes 10K steps. Do not assert undocumented absolute bounds.
        k=wb.get('kelvin')
        if type(k)!=int or k%10 or not 2000<=k<=12000:
            raise ValueError('white_balance.kelvin must be 10K increments in provisional range 2000–12000; confirm camera acceptance')
    elif 'kelvin' in wb:
        raise ValueError('kelvin may only be set in K mode')
    for k in ('red','blue'):
        v=wb.get(k,0)
        if type(v)!=int or not -9<=v<=9:
            raise ValueError(f'white_balance.{k} requires an integer -9..9')
    iso=settings.get('iso')
    if iso is not None:
        if type(iso)!=int or iso<160:
            raise ValueError('iso must be a whole value >= 160')
        if dr==200 and iso<320:raise ValueError('DR200 requires ISO 320 or greater')
        if dr==400 and iso<640:raise ValueError('DR400 requires ISO 640 or greater')
    return settings


def format_recipe(settings: dict) -> str:
    validate(settings)
    wb=settings['white_balance'];kelvin=f" {wb['kelvin']}K" if wb['mode']=='K' else ''
    def e(key,default):return settings.get(key,default)
    return '\n'.join([
        'FUJIFILM X100V CUSTOM SETTINGS - UNVERIFIED CALIBRATION CANDIDATE',
        f"Name: {settings['name']}",
        f"Film simulation: {settings['film_simulation']}",
        f"Dynamic Range: DR{e('dynamic_range',100)}",'D RANGE PRIORITY: OFF',
        f"White balance: {wb['mode']}{kelvin}, Red {wb.get('red',0):+d}, Blue {wb.get('blue',0):+d}",
        f"Tone curve highlight: {e('highlight',0):+d}",
        f"Tone curve shadow: {e('shadow',0):+d}",
        f"Color: {e('color',0):+d}",
        f"Sharpness: {e('sharpness',0):+d}",
        f"Noise reduction: {e('noise_reduction',0):+d}",
        f"Clarity: {e('clarity',0):+d}",
        f"Grain roughness: {e('grain_roughness','OFF')}",
        f"Grain size: {e('grain_size','SMALL')}",
        f"Color Chrome Effect: {e('color_chrome','OFF')}",
        f"Color Chrome FX Blue: {e('color_chrome_blue','OFF')}",
        f"Minimum required ISO: {160 if e('dynamic_range',100)==100 else (320 if e('dynamic_range',100)==200 else 640)}",
        'Not from Fuji X Weekly. No measured SpektraFilm fidelity is claimed.',
        'Menu: IMAGE QUALITY SETTING > EDIT/SAVE CUSTOM SETTING > Choose bank > EDIT.',
        '',
    ])


def export_file(source: Path,dest: Path,*,experimental:bool=False) -> dict:
    data=json.loads(Path(source).read_text('utf-8'))
    if not experimental:
        raise ValueError('X100V camera and color-matching have not been verified; explicit --experimental required')
    settings={k:v for k,v in data.items() if k!='validated_on_camera'}
    output=format_recipe(settings)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(output,encoding='utf-8')
    return {'path':str(dest),'model':'Fujifilm X100V','color_calibration_verified':False,'experimental':True}

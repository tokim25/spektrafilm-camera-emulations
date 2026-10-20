"""Nikon NP3 writer for calibration trials, ported from ssssota's MIT library.

Upstream: https://github.com/ssssota/nikon-flexible-color-picture-control
Retains the unmodified Nikon NP3 structural template from upstream's sample.
Neither format conformance nor roundtrip proves a camera will accept a file.
"""
from __future__ import annotations
import base64
import json
import math
import re
import struct
from pathlib import Path

# ssssota/nikon-flexible-color-picture-control/samples/vanilla.NP3 (MIT license).
_TEMPLATE_B64 = '''
TkNQAAAAAQAAAAAEMDMxMAAAAgAAAAAUdmFuaWxsYQAAAAAAAAAAAAAAAAAA
AAMAAAAAAgAgAAAEAAAAAAIAAAAABQAAAAAC/wEAAAYAAAAAAogEAAAHAAAA
AAKCBAAACAAAAAAC/wQAAAkAAAAAAv8EAAAKAAAAAAL/BAAACwAAAAAC/wQA
AAwAAAAAAv8AAAANAAAAAAL/AAAADgAAAAAC/wQAAA8AAAAAAv8BAAAQAAAA
AAL/AQAAEQAAAAAC/wEAABIAAAAAAv8BAAATAAAAAAL/AQAAFAAAAAACgAEA
ABUAAAAAAv8KAAAWAAAAAAKEBAAAFwAAAAAC/wQAABgAAAAAAv8EAAAZAAAA
AAKAAQAAGgAAAAACgAEAABsAAAAAAoABAAAcAAAAAAKAAQAAHQAAAAACgAEA
AB4AAAAAAoABAAAfAAAAAByAgICAgICAgICAgICAgICAgICAgICAgIABAQEA
AAAgAAAAABSAAICAgACAgIAAgIABAQEAsgGAAQAAAAA=
'''
# Nikon sample tone-curve extension (MIT source): baseWithToneCurve data
# prior to its 257 * uint16 ramp, followed by a four-byte terminator.
BASE = base64.b64decode(_TEMPLATE_B64)
_CURVE_HEADER = bytes.fromhex(
    '00 00 02 42 49 30 00 ff 00 ff 01 00 03 00 00 80 80 ff ff '
    + '00 '*49
)
assert len(_CURVE_HEADER) == 68
TONED = BASE + _CURVE_HEADER + b''.join(
    struct.pack('>H',(i*32767+128)//256) for i in range(257)
) + b'\x00'*4
assert len(TONED) == 978
OFFSET = dict(
    sharpning=0x52, midRangeSharpning=0xf2, clarity=0x5c, contrast=0x110,
    highlights=0x11a, shadows=0x124, whiteLevel=0x12e, blackLevel=0x138,
    saturation=0x142,
)
BLENDER = dict(red=0x14c, orange=0x14f, yellow=0x152, green=0x155,
               cyan=0x158, blue=0x15b, purple=0x15e, magenta=0x161)
GRADING = dict(highlights=0x170, midTone=0x174, shadows=0x178)


def _n(v: object, minimum: float, maximum: float, key: str) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise ValueError(f'{key} must be a finite number')
    if not minimum <= v <= maximum:
        raise ValueError(f'{key} must be between {minimum} and {maximum}')
    return float(v)


def _u8(v: float) -> int:
    # Javascript Uint8Array assignment truncates toward zero.
    return math.trunc(v)


def _set(buf: bytearray, where: int, v: float):
    val = _u8(v)
    if not 0 <= val <= 255:
        raise ValueError('Invalid encoded control value')
    buf[where] = val


def serialize(options: dict) -> bytes:
    if not isinstance(options, dict):
        raise ValueError('NP3 settings must be a JSON object')
    allowed = {'name','comment','toneCurve','colorBlender','colorGrading',*OFFSET}
    unknown = set(options)-allowed
    if unknown:
        raise ValueError(f'Unknown NP3 controls: {sorted(unknown)}')
    name = options.get('name')
    if not isinstance(name, str) or not re.fullmatch(r'[\x20-\x7E]{1,19}', name):
        raise ValueError('Camera Picture Control name must be 1-19 ASCII printable characters')
    buf = bytearray(BASE)
    buf[0x18:0x18+20] = b'\0'*20
    buf[0x18:0x18+len(name)] = name.encode('ascii')
    for key, where in OFFSET.items():
        default, lo, hi, unit = (2,-3,9,4) if key=='sharpning' else ((1,-5,5,4) if key=='midRangeSharpning' else ((0.5,-5,5,4) if key=='clarity' else (0,-100,100,1)))
        v=_n(options.get(key,default),lo,hi,key)
        _set(buf,where,128+v*unit)
    blender=options.get('colorBlender') or {}
    if not isinstance(blender,dict) or set(blender)-set(BLENDER):
        raise ValueError('Invalid colorBlender fields')
    for key, where in BLENDER.items():
        vals = blender.get(key) or {}
        if not isinstance(vals,dict) or set(vals)-{'hue','chroma','brightness'}:
            raise ValueError(f'Invalid colorBlender.{key}')
        for i,k in enumerate(('hue','chroma','brightness')):
            _set(buf,where+i,128+_n(vals.get(k,0),-100,100,f'blender.{key}.{k}'))
    grading=options.get('colorGrading') or {}
    if not isinstance(grading,dict) or set(grading)-({*GRADING,'blending','balance'}):
        raise ValueError('Invalid colorGrading fields')
    for key, where in GRADING.items():
        vals=grading.get(key) or {}
        if not isinstance(vals,dict) or set(vals)-{'hue','chroma','brightness'}:
            raise ValueError(f'Invalid grading {key}')
        deg=_n(vals.get('hue',0),0,360,f'grading.{key}.hue')%360
        deg=int(deg)
        _set(buf,where,128+(deg>>8))
        _set(buf,where+1,deg&255)
        _set(buf,where+2,128+_n(vals.get('chroma',0),-100,100,f'grading.{key}.chroma'))
        _set(buf,where+3,128+_n(vals.get('brightness',0),-100,100,f'grading.{key}.brightness'))
    _set(buf,0x180,128+_n(grading.get('blending',50),0,100,'grading.blending'))
    _set(buf,0x182,128+_n(grading.get('balance',0),-100,100,'grading.balance'))
    tone = options.get('toneCurve')
    comment = options.get('comment','')
    if not isinstance(comment,str) or '\0' in comment or len(comment)>256:
        raise ValueError('comment must be 0-256 characters and contain no NUL')
    if comment:
        raw=comment.encode('utf-8')+b'\0'
        if len(raw)%2:raw+=b'\0'
        buf[0x185]=1;buf[0x186]=1
        buf+=struct.pack('>I',len(raw))+raw+struct.pack('>I',2 if tone is not None else 0)
    if tone is not None:
        if not isinstance(tone,dict) or set(tone)!={'raw','points'}:
            raise ValueError('toneCurve needs raw array and points array')
        raw=tone['raw'];points=tone['points']
        if not isinstance(raw,list) or len(raw)!=257:
            raise ValueError('toneCurve.raw requires 257 integers')
        if not isinstance(points,list) or not 2<=len(points)<=20:
            raise ValueError('toneCurve.points requires 2-20 points')
        if any(not isinstance(n,int) or isinstance(n,bool) or not (0<=n<=32767) for n in raw):
            raise ValueError('Invalid 16-bit tone curve values')
        if any(raw[i]>raw[i+1] for i in range(256)):
            raise ValueError('Tone curve must be monotonic')
        coords=[]
        for p in points:
            if not isinstance(p,dict) or set(p)!={'x','y'}:
                raise ValueError('Each point needs x,y')
            x,y=p['x'],p['y']
            if any(not isinstance(z,int) or isinstance(z,bool) or not 0<=z<=255 for z in (x,y)):
                raise ValueError('Invalid tone curve control point')
            coords.append((x,y))
        if coords[0][0]!=0 or coords[-1][0]!=255 or any(coords[i][0]>=coords[i+1][0] for i in range(len(coords)-1)):
            raise ValueError('Tone curve endpoints must be 0,255 and x strictly increasing')
        delta=len(buf)-len(BASE)
        buf += TONED[len(BASE):]
        for where in (0x110,0x11a,0x124,0x12e,0x138): buf[where]=1
        if not comment:buf[0x187]=2
        for i,v in enumerate(raw): struct.pack_into('>H',buf,0x1cc+delta+i*2,v)
        buf[0x194+delta]=len(coords)
        for i,(x,y) in enumerate(coords):
            buf[0x194+delta+1+i*2]=x
            buf[0x194+delta+2+i*2]=y
    if len(buf)<392 or buf[:4]!=b'NCP\0' or buf[12:16]!=b'0310':
        raise RuntimeError('Internal NP3 template corrupted')
    return bytes(buf)


def export_file(source: Path, dest: Path, *, experimental: bool=False) -> dict:
    opts=json.loads(Path(source).read_text('utf-8'))
    if not experimental:
        raise ValueError('Nikon Zf camera and color-matching have not been verified; explicit --experimental flag required')
    raw=serialize({k:v for k,v in opts.items() if k!='validated_on_camera'})
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(raw)
    return {'path':str(dest),'size_bytes':len(raw),'camera_import_verified':False,
            'color_calibration_verified':False,'experimental':True}

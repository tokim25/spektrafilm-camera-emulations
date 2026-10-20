import json
from pathlib import Path
import pytest

from portra160_lab.probe_kit import create_probe_kit
from portra160_lab.fit_probes import fit_probes


def patches(rgb, stock='portra160'):
    return {
        'format':'portra160-patches-v1', 'stock':stock,
        'color_space':'sRGB','encoding':'display-encoded',
        'patches':[
            {'id':'skin','category':'skin','rgb':rgb},
            {'id':'neutral','category':'neutral','rgb':[0.45,0.45,0.45]},
        ],
    }


def files(tmp_path, camera, candidate_index):
    kit=tmp_path/'kit';create_probe_kit(kit)
    obs=tmp_path/'observations'/camera;obs.mkdir(parents=True)
    (obs/'LAB01.json').write_text(json.dumps(patches([0.5,0.35,0.2])))
    (obs/f'LAB{candidate_index:02d}.json').write_text(json.dumps(patches([0.55,0.35,0.2])))
    reference=tmp_path/'reference.json'
    reference.write_text(json.dumps(patches([0.525,0.35,0.2])))
    return reference, kit, tmp_path/'observations'


def test_nikon_fitter_outputs_unverified_np3(tmp_path):
    ref,kit,obs=files(tmp_path,'nikon_zf',4)
    result=fit_probes(ref,kit,obs,tmp_path/'next',camera='zf')
    assert result['camera']=='Nikon Zf'
    assert result['spektrafilm_fidelity_verified'] is False
    assert result['camera_render_verified'] is False
    assert result['settings']['saturation']>0
    assert (tmp_path/'next'/'PICCON10.NP3').read_bytes()[:4]==b'NCP\0'


def test_fuji_fitter_outputs_unverified_recipe(tmp_path):
    ref,kit,obs=files(tmp_path,'fujifilm_x100v',5)
    result=fit_probes(ref,kit,obs,tmp_path/'next',camera='x100v')
    assert result['camera']=='Fujifilm X100V'
    assert result['spektrafilm_fidelity_verified'] is False
    assert 0<result['settings']['color']<=3
    assert 'UNVERIFIED' in (tmp_path/'next'/'X100V_LABNEXT.txt').read_text()


def test_fit_without_measured_probes_fails(tmp_path):
    ref,kit,obs=files(tmp_path,'nikon_zf',4)
    (obs/'nikon_zf'/'LAB01.json').unlink()
    with pytest.raises(ValueError,match='Missing measured'):
        fit_probes(ref,kit,obs,tmp_path/'next',camera='zf')


def test_fit_stock_mismatch_fails(tmp_path):
    ref,kit,obs=files(tmp_path,'nikon_zf',4)
    x=patches([0.4,0.5,0.2],stock='vision3_250d')
    ref.write_text(json.dumps(x))
    with pytest.raises(ValueError,match='film stocks do not match'):
        fit_probes(ref,kit,obs,tmp_path/'next',camera='zf')

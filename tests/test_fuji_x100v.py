import json
import pytest
from portra160_lab.fuji_x100v import validate,format_recipe,export_file


def trial():
    return {'name':'EXPERIMENT','film_simulation':'PROVIA',
            'white_balance':{'mode':'DAYLIGHT','red':0,'blue':0},
            'dynamic_range':100, 'iso':160}


def test_neutral_trial_formats():
    txt=format_recipe(trial())
    assert 'PROVIA' in txt and 'UNVERIFIED' in txt and 'DR100' in txt


def test_iso_interlock():
    x=trial();x['dynamic_range']=400
    with pytest.raises(ValueError,match='ISO 640'):
        validate(x)
    x['iso']=640;validate(x)


def test_tone_control_bounds():
    x=trial();x['highlight']=5
    with pytest.raises(ValueError,match='highlight'):
        validate(x)


def test_export_requires_acknowledgement(tmp_path):
    p=tmp_path/'candidate.json';p.write_text(json.dumps(trial()))
    with pytest.raises(ValueError,match='--experimental'):
        export_file(p,tmp_path/'candidate.txt')
    out=export_file(p,tmp_path/'candidate.txt',experimental=True)
    assert out['color_calibration_verified'] is False

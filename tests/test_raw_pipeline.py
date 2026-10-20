from types import SimpleNamespace
import sys
import json
from pathlib import Path
import numpy as np
import pytest

from portra160_lab.raw_pipeline import prepare_raw
from portra160_lab.phase1 import phase1_status
from portra160_lab.compare import compare_scene


class FakeRaw:
    camera_whitebalance=[2, 1, 1.3, 1]
    daylight_whitebalance=[2.2, 1, 1.5, 1]
    black_level_per_channel=[128,128,128,128]
    white_level=16000
    def __init__(self):
        self.settings=None
        self.closed=False
    def postprocess(self, **kwargs):
        self.settings=kwargs
        a=np.zeros((5,4,3),dtype=np.uint16)
        a[:,:,:]=8000
        a[0,0]=65535
        return a
    def close(self):
        self.closed=True


def test_prepare_raw_provisional_and_auditable(tmp_path,monkeypatch):
    raw=FakeRaw()
    f=tmp_path/'img.NEF'; f.write_bytes(b'FAKE CAMERA BYTES TEST ONLY')
    import importlib.metadata
    monkeypatch.setattr(importlib.metadata,'version',lambda name:'0.26.1')
    mock=SimpleNamespace(
       imread=lambda path:raw,
       DemosaicAlgorithm=SimpleNamespace(AHD='ahd',DCB='dcb'),
       ColorSpace=SimpleNamespace(ProPhoto='prophoto'),
       HighlightMode=SimpleNamespace(Clip='clip'))
    monkeypatch.setitem(sys.modules,'rawpy',mock)
    output=tmp_path/'linear.npy'
    r=prepare_raw(f,output)
    img=np.load(output,allow_pickle=False)
    assert img.dtype==np.float32 and img.shape==(5,4,3)
    assert np.isclose(img[1,1,0],8000/65535)
    assert raw.settings['gamma']==(1.,1.) and raw.settings['no_auto_bright']
    assert raw.settings['output_color']=='prophoto' and raw.closed
    assert r['calibration_status']=='provisional_not_colorchecker_measured'
    assert r['clipped_pixel_fraction']==pytest.approx(.05)
    assert r['spektrafilm_ready'] is False
    assert json.loads(output.with_suffix('.json').read_text())['source_sha256']==r['source_sha256']


def test_prepare_raw_refuses_jpg(tmp_path):
    f=tmp_path/'bad.jpg';f.write_bytes(b'jpeg')
    with pytest.raises(ValueError,match='Only original'):
        prepare_raw(f,tmp_path/'a.npy')


def test_phase1_never_marks_unmeasured_as_complete(tmp_path):
    result=phase1_status(tmp_path)
    assert result['ready_for_everyday_use'] is False
    assert not result['gates']['reference_image_exists']
    assert result['gates']['exact_upstream_stock'] is True


def test_compare_scene_is_not_device_validation(tmp_path):
    pixels=np.full((7,7,3),.5,dtype=np.float32)
    a=tmp_path/'r.npy'; b=tmp_path/'c.npy'
    np.save(a,pixels,allow_pickle=False);np.save(b,pixels,allow_pickle=False)
    reg=tmp_path/'regions.json';reg.write_text(json.dumps({'patches':[{'id':'gray','category':'neutral','box':[1,1,6,6]}]}))
    report=compare_scene(a,b,reg,tmp_path/'report.json',camera='Nikon Zf')
    assert report['statistics']['mean_deltaE00']==pytest.approx(0)
    assert not report['held_out_validation_complete']
    assert not report['color_match_verified']


def test_compare_scene_invalid_camera(tmp_path):
    with pytest.raises(ValueError,match='camera must'):
        compare_scene(tmp_path/'a',tmp_path/'b',tmp_path/'c',tmp_path/'d',camera='Generic')

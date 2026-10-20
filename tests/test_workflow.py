from pathlib import Path
import json
import pytest
from portra160_lab.workflow import render_raw


def test_render_raw_calls_actual_upstream_entrypoint_with_prepared_input(tmp_path,monkeypatch):
    import portra160_lab.workflow as w
    called={}
    def fake_prepare(source,dest,**kwargs):
        called['source']=source;called['linear']=dest
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(b'fake linear data')
        dest.with_suffix('.json').write_text('{}')
        return {'spektrafilm_ready':True,'calibration_status':'provisional_not_colorchecker_measured'}
    def fake_render(source,dest,mode,**kwargs):
        called['render_source']=source;called['stock']=kwargs['stock'];called['mode']=mode
        dest.write_bytes(b'fake reference')
        dest.with_suffix('.json').write_text('{}')
        return {'film':'kodak_portra_160','print':'kodak_portra_endura'}
    monkeypatch.setattr(w,'prepare_raw',fake_prepare)
    monkeypatch.setattr(w,'render',fake_render)
    dest=tmp_path/'ref.npy'
    result=render_raw(tmp_path/'sample.NEF',dest)
    assert called['source']==tmp_path/'sample.NEF'
    assert called['render_source']==called['linear']
    assert called['stock']=='portra160' and called['mode']=='color'
    assert not result['camera_native_fidelity_validated']
    assert json.loads((tmp_path/'ref_run.json').read_text())['film']=='kodak_portra_160'


def test_render_raw_refuses_lost_highlights(tmp_path,monkeypatch):
    import portra160_lab.workflow as w
    def fake_prepare(source,dest,**kwargs):
        return {'spektrafilm_ready':False,'clipped_pixel_fraction':0.1}
    monkeypatch.setattr(w,'prepare_raw',fake_prepare)
    with pytest.raises(ValueError,match='clipped'):
        render_raw(tmp_path/'sample.RAF',tmp_path/'reference.npy')

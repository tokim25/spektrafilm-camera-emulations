import json
import numpy as np
from portra160_lab.matrix import render_matrix

def test_matrix_writes_manifest_and_hashes(tmp_path, monkeypatch):
    source=tmp_path/'input.npy'; np.save(source,np.full((2,2,3),.25,dtype='float32'))
    def fake_render(source,dest,mode,stock):
        np.save(dest,np.full((2,2,3),.5,dtype='float32'))
        dest.with_suffix('.json').write_text(json.dumps({'source_commit_installed':'abc','source_commit_verified_at_runtime':True}))
        return {'source_commit_installed':'abc','source_commit_verified_at_runtime':True}
    monkeypatch.setattr('portra160_lab.matrix.render',fake_render)
    monkeypatch.setattr('portra160_lab.matrix.all_stocks',lambda:{'portra400':{'status':'upstream_profile_available'}})
    monkeypatch.setattr('portra160_lab.matrix.supported_stock',lambda key:{'film':'kodak_portra_400','print':'kodak_portra_endura'})
    out=render_matrix(source,tmp_path/'out')
    assert out['records'][0]['output_sha256'] and out['records'][0]['metadata_sha256']
    assert json.loads((tmp_path/'out'/'manifest.json').read_text())['camera_recipe_generated'] is False

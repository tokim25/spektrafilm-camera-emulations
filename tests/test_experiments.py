import numpy as np
import pytest
import json
from portra160_lab.experiments import measure,extract_patches,rank

def patches(vals,cam=None):
    d={'format':'portra160-patches-v1','color_space':'sRGB','encoding':'display-encoded',
       'patches':[{'id':i,'category':cat,'rgb':v} for i,cat,v in vals]}
    if cam:d.update(camera=cam,name='candidate')
    return d

def test_identical_measures_zero():
    ref=patches([('a','skin',[.3,.5,.2]),('b','neutral',[.2,.2,.2])])
    m=measure(ref,ref)
    assert m['weighted_mean_deltaE00']==pytest.approx(0,abs=1e-10)

def test_different_id_fails():
    ref=patches([('a','skin',[.3,.5,.2])])
    cand=patches([('b','skin',[.3,.5,.2])])
    with pytest.raises(ValueError,match='Patch IDs differ'):measure(ref,cand)

def test_rank_keeps_cameras_separate(tmp_path):
    r=patches([('skin','skin',[.8,.5,.4])]);p=tmp_path/'reference.json';p.write_text(json.dumps(r))
    files=[]
    for name,cam,v in [('worse','Nikon Zf',[.1,.1,.1]),('better','Nikon Zf',[.79,.5,.4]),('fuji','Fujifilm X100V',[.8,.5,.4])]:
        d=patches([('skin','skin',v)],cam=cam);d['name']=name
        q=tmp_path/(name+'.json');q.write_text(json.dumps(d));files.append(q)
    result=rank(p,files)
    assert [x['name'] for x in result['ranked_by_camera']['Nikon Zf']]==['better','worse']
    assert len(result['ranked_by_camera']['Fujifilm X100V'])==1

def test_extract_npy(tmp_path):
    rgb=np.zeros((10,10,3),dtype=float);rgb[2:8,2:8]=[.25,.5,.75]
    p=tmp_path/'render.npy';np.save(p,rgb)
    reg=tmp_path/'regions.json';reg.write_text(json.dumps({'patches':[{'id':'a','box':[2,2,8,8]}]}))
    out=extract_patches(p,reg)
    np.testing.assert_allclose(out['patches'][0]['rgb'],[.25,.5,.75])


def test_prevent_cross_stock_color_fitting():
    ref=patches([('a','general',[.4,.5,.3])]);ref['stock']='portra400'
    cand=patches([('a','general',[.4,.5,.3])]);cand['stock']='portra160'
    with pytest.raises(ValueError,match='different film stocks'):
        measure(ref,cand)

def test_rank_uses_actual_stock_metadata(tmp_path):
    ref=patches([('a','general',[.4,.5,.3])]);ref['stock']='vision3_250d'
    cam=patches([('a','general',[.4,.5,.3])],cam='Nikon Zf');cam['stock']='vision3_250d'
    p=tmp_path/'r.json';p.write_text(json.dumps(ref))
    q=tmp_path/'c.json';q.write_text(json.dumps(cam))
    r=rank(p,[q])
    assert r['stock']=='vision3_250d' and r['print']=='kodak_2383'

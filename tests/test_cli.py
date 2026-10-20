import json
import pytest
from portra160_lab.cli import main

def test_cli_extract_and_rank(tmp_path):
    import numpy as np
    px=np.full((8,8,3),.4,dtype=float)
    f=tmp_path/'img.npy';np.save(f,px)
    regions=tmp_path/'regions.json';regions.write_text(json.dumps({'patches':[{'id':'n','category':'neutral','box':[1,1,7,7]}]}))
    ref=tmp_path/'reference.json'
    assert main(['extract','--image',str(f),'--regions',str(regions),'--out',str(ref)])==0
    c=json.loads(ref.read_text());c['camera']='Nikon Zf';c['name']='test'
    candidate=tmp_path/'candidate.json';candidate.write_text(json.dumps(c))
    result=tmp_path/'result.json'
    assert main(['rank','--reference',str(ref),'--candidates',str(candidate),'--out',str(result)])==0
    assert json.loads(result.read_text())['ranked_by_camera']['Nikon Zf'][0]['statistics']['weighted_mean_deltaE00']==0

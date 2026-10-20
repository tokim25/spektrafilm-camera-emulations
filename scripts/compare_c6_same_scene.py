from pathlib import Path
import json
import numpy as np
from PIL import Image
from portra160_lab.color import delta_e_srgb

root=Path(__file__).resolve().parents[1]
name='DSCF4360'
ref=np.load(root/f'results/hardware/x100v_c6/{name}_portra160_reference_1041.npy')
im=Image.open(root/f'data/hardware/x100v_c6/{name}.JPG').convert('RGB')
im=im.resize((ref.shape[1],ref.shape[0]),Image.Resampling.BILINEAR)
cam=np.asarray(im,dtype=np.float32)/255.0
valid=np.all(np.isfinite(ref),axis=2)&np.all(np.isfinite(cam),axis=2)
step=8
idx=np.where(valid[::step,::step].ravel())[0]
rr=ref[::step,::step].reshape(-1,3)[idx]
cc=cam[::step,::step].reshape(-1,3)[idx]
def lin(x): return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def enc(x): return np.where(x<=.0031308,12.92*x,1.055*np.maximum(x,0)**(1/2.4)-.055)
scores=[]
for ev in np.arange(-1.0,2.51,.05):
    adj=np.clip(enc(np.clip(lin(cc)*2**ev,0,1)),0,1)
    e=delta_e_srgb(adj,rr)
    scores.append((float(e.mean()),float(np.median(e)),float(np.percentile(e,95)),float(ev)))
best=min(scores)
ev=best[3]
adj=np.clip(enc(np.clip(lin(cam)*2**ev,0,1)),0,1)
side=np.concatenate([adj,ref],axis=1)
Image.fromarray(np.uint8(np.clip(side,0,1)*255),'RGB').save(root/f'results/hardware/x100v_c6/{name}_comparison_side_by_side.jpg',quality=92)
report={'kind':'x100v-c6-portra160-held-out-diagnostic-v1','camera':'Fujifilm X100V','destination':'C6','source_raw':f'data/hardware/x100v_c6/{name}.RAF','source_jpeg':f'data/hardware/x100v_c6/{name}.JPG','spektrafilm_reference':f'results/hardware/x100v_c6/{name}_portra160_reference_1041.npy','scene_match_to_c5':False,'comparison':{'best_exposure_ev':ev,'mean_deltaE00':best[0],'median_deltaE00':best[1],'p95_deltaE00':best[2],'mask':'all finite pixels; every eighth pixel; camera JPEG resized to reference'},'interpretation':'Held-out scene captured with the same C6 settings. This tests generalization beyond the cube scene, but it is still not a controlled chart measurement and does not prove a general recipe.','hardware_write_status':'manual C6 entry reported; no USB write performed'}
(root/f'results/hardware/x100v_c6/{name}_comparison_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

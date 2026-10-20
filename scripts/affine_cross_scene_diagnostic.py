"""Cross-scene diagnostic; never produces a camera recipe.

Fits an affine transform in display-linear RGB on the C6 cube and evaluates it
unchanged on the held-out plant scene. A large held-out error means the fit is
not a safe basis for camera controls.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from portra160_lab.color import delta_e_srgb

root=Path(__file__).resolve().parents[1]
def load(name):
    ref=np.load(root/f'results/hardware/x100v_c6/{name}_portra160_reference_1041.npy')
    im=Image.open(root/f'data/hardware/x100v_c6/{name}.JPG').convert('RGB').resize((ref.shape[1],ref.shape[0]),Image.Resampling.BILINEAR)
    return ref,np.asarray(im,dtype=np.float64)/255
def lin(x): return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def enc(x): return np.where(x<=.0031308,12.92*x,1.055*np.maximum(x,0)**(1/2.4)-.055)
def score(a,b):
    e=delta_e_srgb(np.clip(a,0,1),np.clip(b,0,1)); return {'mean':float(e.mean()),'median':float(np.median(e)),'p95':float(np.percentile(e,95))}
cube_ref,cube_cam=load('DSCF4355'); plant_ref,plant_cam=load('DSCF4360')
step=8; x=lin(cube_cam[::step,::step]).reshape(-1,3); y=lin(cube_ref[::step,::step]).reshape(-1,3)
X=np.concatenate([x,np.ones((len(x),1))],1); coef=np.linalg.lstsq(X,y,rcond=None)[0]
cube_fit=enc(np.clip(np.concatenate([lin(cube_cam),np.ones((*cube_cam.shape[:2],1))],2)@coef,0,1))
plant_fit=enc(np.clip(np.concatenate([lin(plant_cam),np.ones((*plant_cam.shape[:2],1))],2)@coef,0,1))
report={'kind':'x100v-c6-cross-scene-affine-diagnostic-v1','fit_scene':'DSCF4355 cube','held_out_scene':'DSCF4360 plant','raw_transform_space':'display-linear RGB with affine bias','fit_scene_error':score(cube_fit,cube_ref),'held_out_scene_error':score(plant_fit,plant_ref),'interpretation':'Diagnostic only. A cross-scene affine fit is not a Fujifilm custom-setting recipe and does not establish camera readiness.','coefficient_matrix':coef.tolist()}
out=root/'results/hardware/x100v_c6/affine_cross_scene_diagnostic.json'; out.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))

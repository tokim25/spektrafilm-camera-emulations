import numpy as np
from portra160_lab.color import delta_e_2000,delta_e_srgb,srgb_to_lab

def test_sharma_reference_examples():
    # Published CIEDE2000 verification pairs from Sharma, Wu, Dalal (2005).
    a=np.array([[50,2.6772,-79.7751],[50,3.1571,-77.2803],
                [50,2.8361,-74.0200],[50,-1.3802,-84.2814]])
    b=np.array([[50,0,-82.7485],[50,0,-82.7485],
                [50,0,-82.7485],[50,0,-82.7485]])
    np.testing.assert_allclose(delta_e_2000(a,b),[2.0425,2.8615,3.4412,1.0000],atol=.0001)

def test_identity_and_known_white_black():
    arr=np.array([[0,0,0],[1,1,1],[.5,.5,.5]],dtype=float)
    np.testing.assert_allclose(delta_e_srgb(arr,arr),0,atol=1e-10)
    assert srgb_to_lab([1,1,1])[0]>99.9
    assert delta_e_srgb([0,0,0],[1,1,1])>95

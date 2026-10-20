import json
import struct
import hashlib
import pytest
from portra160_lab.nikon_np3 import BASE,TONED,serialize,export_file


def test_upstream_mit_fixture_exact_roundtrip():
    assert len(BASE)==392
    assert serialize({'name':'vanilla'})==BASE
    assert BASE[:4]==b'NCP\0' and BASE[12:16]==b'0310'
    assert hashlib.sha1(f"blob {len(BASE)}\0".encode()+BASE).hexdigest()=="eb53acc822be88342981bbc3d8ec6b5b0d0e9823"


def test_tone_curve_serialization():
    raw=[min(32767,i*128) for i in range(257)]
    data=serialize({'name':'tonecurve-noop','toneCurve':{'raw':raw,'points':[{'x':0,'y':0},{'x':255,'y':255}]}})
    assert len(data)==len(TONED)==978
    assert data[0x187]==2
    assert data[0x110]==data[0x11a]==data[0x124]==1
    assert data[0x194]==2
    assert data[0x195:0x199]==b'\0\0\xff\xff'
    assert [struct.unpack_from('>H',data,0x1cc+2*i)[0] for i in (0,1,100,256)]==[raw[i] for i in (0,1,100,256)]


def test_upstream_tonecurve_fixture_exact():
    # Exact upstream Git blob, including 257 uint16 points and Nikon metadata.
    linear=[(i*32767+128)//256 for i in range(257)]
    output=serialize({"name":"tonecurve-noop", "toneCurve":{
        "raw":linear,"points":[{"x":0,"y":0},{"x":128,"y":128},{"x":255,"y":255}]}})
    sha=hashlib.sha1(f"blob {len(output)}\0".encode()+output).hexdigest()
    assert sha=="74ad0076439d9ac22388926f6ed3bccebbf707f4"


def test_color_blender_bytes():
    x=serialize({'name':'TEST','colorBlender':{'green':{'chroma':-17}},'colorGrading':{'shadows':{'hue':270,'chroma':4}}})
    assert x[0x156]==128-17
    assert x[0x178:0x17a]==bytes([129,14])


def test_comment_fixtures_byte_identical():
    linear=[(i*32767+128)//256 for i in range(257)]
    combos=[
      (serialize({"name":"comment-a","comment":"a"}), "5954f2653b9d99a8a1206f16cf0fff587ee24efe"),
      (serialize({"name":"comment-a-tonecurve","comment":"a","toneCurve":{
        "raw":linear,"points":[{"x":0,"y":0},{"x":128,"y":128},{"x":255,"y":255}]}}), "33144b9c60a8ce4b17dedcfc9b6769279d769683"),
    ]
    for data,expected in combos:
        assert hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()==expected


def test_names_limits():
    with pytest.raises(ValueError):serialize({'name':'hi'*10})
    with pytest.raises(ValueError):serialize({'name':'©'})
    with pytest.raises(ValueError):serialize({'name':'TEST','contrast':180})


def test_no_unverified_profile_export_without_opt_in(tmp_path):
    src=tmp_path/'draft.json'
    src.write_text(json.dumps({'name':'NEUTRAL','validated_on_camera':False}))
    with pytest.raises(ValueError,match='explicit --experimental'):
        export_file(src,tmp_path/'PICCON01.NP3')
    info=export_file(src,tmp_path/'PICCON01.NP3',experimental=True)
    assert info['camera_import_verified'] is False
    assert (tmp_path/'PICCON01.NP3').read_bytes()[:4]==b'NCP\0'

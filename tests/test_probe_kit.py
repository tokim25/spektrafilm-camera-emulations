import hashlib
import json
from pathlib import Path
import pytest
from portra160_lab.probe_kit import create_probe_kit


def test_probe_kit_outputs_diagnostic_files_and_manifest(tmp_path):
    dest=tmp_path/'kit'
    report=create_probe_kit(dest)
    assert report['target_stock']=='portra160'
    assert all(not Path(row['path']).is_absolute() for row in report['nikon_zf_probes'])
    assert all(not Path(row['path']).is_absolute() for row in report['fujifilm_x100v_probes'])
    assert report['color_match_verified'] is False
    assert report['camera_import_verified'] is False
    assert len(report['nikon_zf_probes'])==9
    assert len(report['fujifilm_x100v_probes'])==7
    for row in report['nikon_zf_probes']+report['fujifilm_x100v_probes']:
        p=dest/row['path']
        assert p.exists()
        assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
    assert (dest/'nikon_zf'/'NIKON'/'CUSTOMPC'/'PICCON01.NP3').read_bytes().startswith(b'NCP\0')
    assert 'NOT PORTRA' in (dest/'READ_THIS_FIRST.txt').read_text()


def test_probe_kit_does_not_overwrite_existing_directory(tmp_path):
    p=tmp_path/'kit'
    create_probe_kit(p)
    with pytest.raises(FileExistsError):create_probe_kit(p)
    other=tmp_path/'other';other.mkdir();(other/'valuable').write_text('keep')
    with pytest.raises(ValueError,match='Refusing'):
        create_probe_kit(other,overwrite=True)
    assert (other/'valuable').read_text()=='keep'
    create_probe_kit(p,overwrite=True)


@pytest.mark.parametrize('name',['ektachrome400','trix400','aerocolor_iv'])
def test_missing_spectral_data_does_not_allow_probe_kit(tmp_path,name):
    with pytest.raises(ValueError,match='must not be substituted'):
        create_probe_kit(tmp_path/name,stock=name)
    assert not (tmp_path/name).exists()

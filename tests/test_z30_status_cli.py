"""Gate status reads evidence values, never file existence alone."""
import json

from z30_lightroom.cli import main
from z30_lightroom.cube import read_cube
from z30_lightroom.status import status


def test_empty_workspace_meets_nothing(tmp_path):
    res = status(tmp_path)
    assert res["goal_met"] is False
    blocked = [k for k, v in res["stocks"].items() if v["blocked"]]
    assert sorted(blocked) == ["doublex5222", "hp5plus400", "superia400", "trix400"]
    assert res["stocks"]["portra160"]["gates"]["reference"]["met"] is False


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def test_reference_gate_requires_verified_commit_and_z30(tmp_path):
    root = tmp_path / "results" / "z30"
    scene = root / "scenes" / "s1.npy"
    _write(scene.with_suffix(".json"), {"camera_model": "NIKON Z 30"})
    _write(root / "references" / "s1" / "portra160.json", {"input": str(scene), "spektrafilm": {"verified": False}})
    assert status(tmp_path)["stocks"]["portra160"]["gates"]["reference"]["met"] is False
    _write(root / "references" / "s1" / "portra160.json", {"input": str(scene), "spektrafilm": {"verified": True}})
    assert status(tmp_path)["stocks"]["portra160"]["gates"]["reference"]["met"] is True


def test_simulated_or_failing_look_reports_do_not_pass(tmp_path):
    root = tmp_path / "results" / "z30" / "look_gate"
    _write(root / "look_gate_portra160.json", {"evidence_source": "simulated_standin",
                                               "lightroom": {"version": None}, "pooled_heldout": {"pass": True}})
    assert status(tmp_path)["stocks"]["portra160"]["gates"]["look"]["met"] is False
    _write(root / "look_gate_portra160.json", {"evidence_source": "lightroom_export",
                                               "lightroom": {"version": "15.0"}, "pooled_heldout": {"pass": False}})
    assert status(tmp_path)["stocks"]["portra160"]["gates"]["look"]["met"] is False


def test_install_gate_rejects_author_tester(tmp_path):
    rec = {"tester_is_author": True, "backup_done": True, "installed": True,
           "readback_matches": True, "uninstalled_restored": True}
    _write(tmp_path / "results" / "z30" / "install" / "portra160.json", rec)
    assert status(tmp_path)["stocks"]["portra160"]["gates"]["install"]["met"] is False


def test_probe_kit_cli(tmp_path, capsys):
    assert main(["probe-kit", "--out", str(tmp_path)]) == 0
    lut = read_cube(tmp_path / "z30_probe_rotate_rgb_gbr.cube")
    assert lut.shape == (33, 33, 33, 3)
    assert abs(lut[0, 0, 32, 2] - 1.0) < 1e-6  # input pure red -> output blue channel carries it
    assert main(["status", "--workspace", str(tmp_path)]) == 1

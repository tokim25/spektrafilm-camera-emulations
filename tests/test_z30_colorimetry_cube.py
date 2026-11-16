"""Independent reference checks for z30_lightroom colorimetry and .cube I/O."""
import numpy as np
import pytest

from z30_lightroom.colorimetry import (PROPHOTO_TO_XYZ, D50_WHITE, prophoto_decode, prophoto_encode,
                                       xyz_to_lab, prophoto_linear_to_lab)
from z30_lightroom.cube import identity_lut, write_cube, read_cube, apply_lut


def test_prophoto_white_is_d50():
    # ICC D50 PCS white: X=0.9642, Y=1.0, Z=0.8249 (ICC.1) ; ROMM normalises to 0.96422/1/0.82521
    np.testing.assert_allclose(D50_WHITE, [0.96422, 1.0, 0.82521], atol=2e-5)


def test_prophoto_matrix_matches_colour_science():
    colour = pytest.importorskip("colour")
    ref = colour.RGB_COLOURSPACES["ProPhoto RGB"].matrix_RGB_to_XYZ
    # colour-science rounds to 4 decimals and uses the ICC D50 Z of 0.8249 instead of
    # ROMM's 0.82521; the 3e-4 difference is below 0.05 dE00 for any colour.
    np.testing.assert_allclose(PROPHOTO_TO_XYZ, ref, atol=4e-4)


def test_lab_matches_colour_science_d50():
    colour = pytest.importorskip("colour")
    rng = np.random.default_rng(3)
    xyz = rng.random((50, 3)) * D50_WHITE
    ours = xyz_to_lab(xyz)
    ref = colour.XYZ_to_Lab(xyz, colour.XYZ_to_xy(D50_WHITE))
    np.testing.assert_allclose(ours, ref, atol=1e-6)


def test_white_and_black_lab():
    np.testing.assert_allclose(prophoto_linear_to_lab(np.ones(3)), [100, 0, 0], atol=1e-3)
    np.testing.assert_allclose(prophoto_linear_to_lab(np.zeros(3)), [0, 0, 0], atol=1e-9)


def test_prophoto_encoding_roundtrip_and_value():
    x = np.linspace(0, 1, 11)
    np.testing.assert_allclose(prophoto_decode(prophoto_encode(x)), x, atol=1e-12)
    assert prophoto_encode(0.18) == pytest.approx(0.18 ** (1 / 1.8))


def test_cube_roundtrip_and_upstream_reader(tmp_path):
    lut = identity_lut(5) ** 1.3
    p = tmp_path / "t.cube"
    write_cube(p, lut, "test")
    np.testing.assert_allclose(read_cube(p), lut, atol=1e-6)
    cube_mod = pytest.importorskip("spektrafilm_lut_creator.formats.cube")
    upstream = cube_mod.CubeFormat().read(p)
    np.testing.assert_allclose(upstream.table, lut, atol=1e-6)


def test_red_index_varies_fastest(tmp_path):
    p = tmp_path / "i.cube"
    write_cube(p, identity_lut(3), "id")
    body = [l for l in p.read_text().splitlines() if l[:1].isdigit()]
    assert body[0] == "0.000000 0.000000 0.000000"
    assert body[1] == "0.500000 0.000000 0.000000"
    assert body[3] == "0.000000 0.500000 0.000000"
    assert body[9] == "0.000000 0.000000 0.500000"


def test_trilinear_exact_for_affine_maps():
    m = np.array([[0.7, 0.2, 0.1], [0.1, 0.8, 0.0], [0.05, 0.1, 0.6]])
    lut = identity_lut(9) @ m.T + 0.02
    x = np.random.default_rng(0).random((200, 3))
    np.testing.assert_allclose(apply_lut(lut, x), x @ m.T + 0.02, atol=1e-12)


def test_cube_rejects_bad_files(tmp_path):
    p = tmp_path / "bad.cube"
    p.write_text("LUT_3D_SIZE 2\n0 0 0\n")
    with pytest.raises(ValueError):
        read_cube(p)
    with pytest.raises(ValueError):
        write_cube(tmp_path / "x.cube", np.zeros((2, 2, 3, 3)), "x")

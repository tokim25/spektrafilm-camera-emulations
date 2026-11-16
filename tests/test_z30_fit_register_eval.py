"""Algorithm tests with known ground truth. These prove the math recovers known
transforms; they do not prove Lightroom or film fidelity."""
import numpy as np
import pytest

from portra160_lab.color import delta_e_2000
from z30_lightroom.colorimetry import prophoto_encode, prophoto_decode, prophoto_linear_to_lab
from z30_lightroom.cube import apply_lut
from z30_lightroom.evaluate import gate_stats, group_masks, load_thresholds
from z30_lightroom.fit import fit_inverse_model, apply_inverse_model, build_prior_lut, fit_lut
from z30_lightroom.probes import PROBES, characterize, predict
from z30_lightroom.register import Registration, register, warp_to_reference
from z30_lightroom.stocks import available_keys, available_stock, load_registry


def fake_lightroom(scene):
    """Stand-in for Camera Raw: a matrix, a filmic tone curve, ProPhoto encoding."""
    m = np.array([[1.05, -0.03, -0.02], [0.02, 0.97, 0.01], [0.0, 0.04, 0.96]])
    x = np.clip(scene @ m.T, 0, None)
    return prophoto_encode(x * 2.2 / (1 + x * 2.2))


def fake_film(scene):
    """Stand-in for SpektraFilm: smooth, nonlinear, cross-channel."""
    x = np.clip(scene, 0, None)
    y = x / (x + 0.25)
    mix = np.array([[0.9, 0.08, 0.02], [0.05, 0.9, 0.05], [0.03, 0.12, 0.85]])
    return np.clip(0.9 * (y @ mix.T) ** 1.1 + 0.02, 0, 1)


def test_fit_recovers_known_mapping_on_held_out_samples():
    rng = np.random.default_rng(7)
    def scenes(k):
        base = rng.random((k, 1)) ** 2 * 1.2
        tint = 1 + (rng.random((k, 3)) - 0.5) * 0.8
        return np.clip(base * tint, 0, 2)
    train, test = scenes(6000), scenes(3000)
    x_train = fake_lightroom(train)
    coef = fit_inverse_model(x_train, train)
    prior = build_prior_lut(coef, lambda img: fake_film(img.reshape(-1, 3)).reshape(img.shape),
                            prophoto_encode, n=17)
    lut = fit_lut(x_train, prophoto_encode(fake_film(train)), prior, smoothness=1.0)
    pred = prophoto_decode(apply_lut(lut, fake_lightroom(test)))
    de = delta_e_2000(prophoto_linear_to_lab(fake_film(test)), prophoto_linear_to_lab(pred))
    assert de.mean() < 1.0
    assert np.percentile(de, 95) < 2.5


def test_inverse_model_inverts_tone_curve():
    rng = np.random.default_rng(1)
    scene = rng.random((4000, 3)) * 1.5
    est = apply_inverse_model(fit_inverse_model(fake_lightroom(scene), scene), fake_lightroom(scene[:500]))
    assert np.median(np.abs(est - scene[:500]) / (scene[:500] + 0.05)) < 0.05


def test_inverse_model_extrapolates_to_saturated_colours():
    """Train on muted colours only; saturated colours must still invert sensibly."""
    rng = np.random.default_rng(11)
    lum = rng.random((5000, 1)) * 1.2
    muted = lum * (1 + (rng.random((5000, 3)) - 0.5) * 0.3)
    model = fit_inverse_model(fake_lightroom(muted), muted)
    sat = np.array([[0.8, 0.05, 0.05], [0.05, 0.6, 0.05], [0.05, 0.1, 0.7], [0.7, 0.6, 0.03]])
    est = apply_inverse_model(model, fake_lightroom(sat))
    de = delta_e_2000(prophoto_linear_to_lab(sat), prophoto_linear_to_lab(est))
    assert de.max() < 3.0


def texture(h, w, seed):
    from scipy import ndimage
    rng = np.random.default_rng(seed)
    base = ndimage.gaussian_filter(rng.random((h, w)), 3) * 4
    img = np.stack([base, ndimage.gaussian_filter(rng.random((h, w)), 4) + base * 0.5, base * 0.7], -1)
    return np.clip(img, 0.01, None)


def test_registration_recovers_known_warp():
    ref = texture(240, 360, 2)
    truth = Registration(scale=1.03, rotation_deg=0.4, shift_x=3.0, shift_y=-2.0, k1=0.02, k2=0.0,
                         ref_shape=(240, 360), export_shape=(240, 360))
    # Build an export whose resampling onto the reference grid returns `ref`, by
    # scattering reference pixels to their true export positions and interpolating.
    from scipy.interpolate import griddata
    from z30_lightroom.register import _coords
    yy, xx = np.mgrid[0:240, 0:360].astype(float)
    ey, ex = _coords(truth, (240, 360))
    export = np.zeros_like(ref)
    pts = np.stack([ey.ravel(), ex.ravel()], 1)
    for c in range(3):
        export[..., c] = griddata(pts, ref[..., c].ravel(), (yy, xx), method="linear", fill_value=0.05)
    reg = register(ref, export, work_width=360)
    got_y, got_x = _coords(reg, (240, 360))
    err = np.hypot(got_y - ey, got_x - ex)[20:-20, 20:-20]
    assert np.median(err) < 0.5
    warped, valid = warp_to_reference(export, reg, (240, 360))
    assert valid[20:-20, 20:-20].all()


def test_gate_stats_rules():
    cfg = load_thresholds()
    lim = cfg["gates"]["look"]
    de = np.array([0.5] * 30 + [5.0])
    groups = {"all": np.ones(31, bool), "neutrals": np.ones(31, bool),
              "skin": np.zeros(31, bool), "saturated": np.arange(31) < 5}
    rep = gate_stats(de, groups, lim, cfg["min_samples_for_p95"])
    assert rep["skin"]["pass"] is False and rep["skin"]["n"] == 0
    assert rep["saturated"]["p95"] is None  # fewer than 20 samples
    assert rep["neutrals"]["pass"] is False  # max 5.0 > 3.0
    assert rep["pass"] is False


def test_group_masks():
    cfg = load_thresholds()
    lab = np.array([[50, 0, 0], [65, 18, 22], [50, 60, 20], [50, -10, 10]])  # last: green, hue 135
    g = group_masks(lab, cfg)
    assert g["neutrals"].tolist() == [True, False, False, False]
    assert g["skin"].tolist() == [False, True, False, False]
    assert g["saturated"].tolist() == [False, False, True, False]


@pytest.mark.parametrize("space", ["prophoto", "srgb", "adobergb"])
def test_probe_characterization_identifies_lut_space(space):
    rng = np.random.default_rng(5)
    identity = prophoto_encode(rng.random((800, 3)) * 0.6 + 0.02)
    probe_export = predict(identity, "rotate_rgb_gbr", space)
    res = characterize(identity, probe_export, "rotate_rgb_gbr")
    assert res["best_hypothesis"] == space and res["hypothesis_holds"]


def test_probe_identity_is_identity():
    x = np.random.default_rng(0).random((10, 3))
    np.testing.assert_allclose(PROBES["identity"](x), x)


def test_stock_registry_fails_closed():
    keys = available_keys()
    assert sorted(keys) == sorted(["portra160", "portra400", "ektar100", "gold200", "kodachrome64",
                                   "vision3_250d", "vision3_500t"])
    assert len(load_registry()) == 11
    for missing in ("doublex5222", "trix400", "hp5plus400", "superia400"):
        with pytest.raises(ValueError):
            available_stock(missing)
    with pytest.raises(ValueError):
        available_stock("fujifilm_xtra_400")

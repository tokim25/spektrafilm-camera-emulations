# SpektraFilm Camera Lab: Portra 160 first

**First calibration target:** Kodak Portra 160 negative + Kodak Portra Endura paper, using the [SpektraFilm](https://github.com/andreavolpato/spektrafilm) reference implementation.

**Cameras:** Nikon Zf and Fujifilm X100V. **Objective:** the closest *measurable camera-native approximation* to the reference, not a hand-picked "Portra vibe."

## Phase 1 delivery status (October 20, 2026)

Phase 1 is shipped as an experimental software/reference release. Physical
camera validation is intentionally deferred and is not required for this
release track. The project does not claim that its NP3 or X100V artifacts are
camera-ready; those remain a separate future hardware-validation track.

Phase 2 reference expansion has begun: the pinned pipeline now renders the
Portra 400 target and all available prioritized film/print combinations. See
[`PHASE2_STATUS.md`](PHASE2_STATUS.md). These are reference outputs, not
camera recipes.

**This is a reproducible calibration developer kit, not a camera-ready Portra 160 preset.**
The user-defined Phase 1 release gate is stricter than a build passing tests:

- The SpektraFilm reference rendering must actually run on real Nikon Zf NEF and Fujifilm X100V RAF data.
- At least one generated Nikon Portra 160 NP3 and one actual Fuji X100V custom-setting recipe must be **fitted from that reference** using camera output, rather than guessed or copied from Fuji X Weekly.
- The Nikon file must import and the Fuji settings must work on the actual target bodies.
- Independent held-out scene comparisons must be documented.

These gates are **not yet met**. `portra160-lab phase1-status --workspace .` reports each blocker; it never calls a neutral format-test file a Portra 160 emulation.

For the exact upstream reference renderer used by the audit, install the
optional pinned dependency with `python -m pip install -e '.[raw,reference]'`.
The revision is fixed to `3bb2c2d2801ff68b92019cf1dbcbb133d60832bc`; do not
replace it with an unpinned package when reproducing reported renders.

The required Nikon Zf and Fujifilm X100V hardware procedure is documented in
`HARDWARE_VALIDATION_CHECKLIST.md`. It includes backup, explicit destination,
readback, restoration, and held-out-scene requirements.

If you do not have a gray-card scene, see `ALTERNATIVES.md` for online-sample
options and the limits of what they can prove.

### What changed in this release

- **New:** `prepare-raw` ingests original NEF/RAF using optional rawpy and creates 32-bit *linear ProPhoto* `.npy` + complete source hashes/settings metadata. This is **provisional** LibRaw camera-matrix processing, not measured camera-chart calibration; 16-bit conversion can clip highlights.
- **New:** `render-raw` provides one command for RAW import and actual SpektraFilm reference rendering. It refuses outputs where >0.2% pixels clip unless deliberately overridden. The pinned renderer has now been executed on a downsampled public X100V RAF working copy; full camera calibration remains unverified.
- **New:** `compare-scene` measures aligned reference/camera images on named regions and reports ΔE00 without pretending this proves hardware acceptance or held-out fidelity.
- **New:** `phase1-status` states release gates and blockers, rather than guessing success from file existence.
- **Extended user-prioritized queue:** Portra 400, Vision3 250D, Ektar 100, Portra 800, Vision3 50D, Vision3 500T, plus Vision Premier 2393 print-film combinations. Ektachrome 400, Tri-X and AeroColor IV still lack exact upstream film profiles and are deferred.
- **Tests:** 48 local tests passed. The tests validate Python logic and file-format encoding, not film-color accuracy or camera behavior.

### Simplest execution on a Mac

Install the package in Python 3.13, then the optional RAW dependency:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,raw]"
```

Clone and install the **exact pinned SpektraFilm source** (GPLv3) in the same virtual environment:

```bash
git clone https://github.com/andreavolpato/spektrafilm.git third_party/spektrafilm-src
git -C third_party/spektrafilm-src checkout 3bb2c2d2801ff68b92019cf1dbcbb133d60832bc
pip install -e third_party/spektrafilm-src
```

Then, with a camera original such as `example.NEF`:

```bash
portra160-lab render-raw --input example.NEF --out results/portra160_reference.npy --stock portra160 --mode color
```

This creates a reference array and audit sidecars. For an aligned JPEG developed using one candidate camera setting and region coordinates in `examples/regions.example.json`:

```bash
portra160-lab compare-scene --reference results/portra160_reference.npy \
  --candidate camera_candidate.jpg --regions examples/regions.example.json \
  --camera "Nikon Zf" --assume-srgb --out results/zf_comparison.json
```

**Important:** The example regions are **not** valid for arbitrary test photographs. Replace them with patch coordinates aligned to the actual RAW/JPEG pair, verify the JPEG color encoding, and repeat for a Fuji RAF/JPEG and held-out scenes. Camera samples found online can bootstrap tests but cannot establish absolute spectrally calibrated color accuracy.

---

## Project status, 2026-10-20

| Component | Status |
| --- | --- |
| Locked Portra 160/Endura configuration | Complete; data in `config/portra160.json` |
| Direct scene-linear reference-render wrapper | Implemented and executed against pinned SpektraFilm on a documented downsampled public X100V RAF working copy |
| Provisional RAW ingestion for Nikon NEF and Fuji RAF | Implemented; optional `rawpy` dependency unavailable here |
| One-shot reference rendering from a camera RAW | Implemented; integration-tested with stubs, **not executed end-to-end** |
| One-scene aligned camera-versus-reference measurement | Implemented and unit-tested, no real images available |
| Deterministic color-reference mode | Implemented, relies on upstream `debug.lut_mode` |
| Full photographic reference mode (grain, halation) | Implemented; not yet run end-to-end |
| CIEDE2000 and measured candidate ranking | Implemented; local tests passing |
| ICC-aware patch extraction from camera images | Implemented; initial unit test uses .npy |
| Nikon Zf NP3 export | **Format writer implemented** and byte-verified against four MIT-licensed upstream fixtures; **no Portra 160 settings fitted** and no Zf hardware import test |
| Fujifilm X100V C1–C7 export | **Manual recipe formatter implemented** with official X100V control bounds; **no Portra 160 settings fitted**; no USB writing |
| Automated NX Studio / X RAW Studio render loop | **Not implemented**, automation feasibility not yet proven |
| Camera-tested fidelity score | **Not available**; no measured target-camera images supplied |
| Native camera-response diagnostic kit | **Implemented**; nine Zf NP3 test files and seven X100V manual trial sheets |
| Measured-response next-candidate fitter | **Implemented and unit-tested**; consumes real measured patches, has no real-camera measurements yet |
| Publisher-hosted RAW test-image manifest | **Added**; actual binary downloads blocked in this runtime |
| Safe personal-use sample downloader | **Implemented and unit-tested**; cannot inspect remote originals from this environment |

The package **does not contain a completed Portra 160 profile**. It contains an experimental Nikon NP3 *neutral file-format import test* and an X100V *neutral settings trial*, neither representing Portra 160. The calibration engine is an actual tested starter, not a claimed successful camera conversion.

The long-term stock queue and missing-profile research are in [STOCK_ROADMAP.md](STOCK_ROADMAP.md). No recipes from Fuji X Weekly or other third-party look collections are used as reference.

## Camera-response experiments: the next measurable step (2026-10-20)

**These are intentionally NOT Portra 160 presets.** They let us see what each camera really does when a single control is changed, then use SpektraFilm's Portra 160 + Portra Endura result as the target of a measured fit. The files are not sourced from Fuji X Weekly or community film recipes.

The release includes `build/portra160_camera_probes/` already generated. To regenerate:

```bash
portra160-lab probe-kit --out build/portra160_camera_probes --stock portra160 --overwrite
```

The output is 9 experimental Nikon `.NP3` files (`nikon_zf/NIKON/CUSTOMPC/`) and 7 Fujifilm X100V manual settings sheets (`fujifilm_x100v/`). `manifest.json` stores exact settings and SHA-256 hashes for reproducibility. `READ_THIS_FIRST.txt` explains safe trials. **No camera is modified by creating the kit.** Only write to expendable custom slots, after backing up what is already there. The files have not been accepted by a physical Zf yet; failures should stop the test rather than prompt firmware changes.

To evaluate them, render **the same actual Nikon NEF** with baseline LAB01 and chosen modified controls in NX Studio; do the equivalent for the **same actual Fujifilm RAF** in X RAW Studio where supported. Create matching sRGB patch JSON files named `LAB01.json`, `LAB02.json`, etc. using `portra160-lab extract`. The reference must be from SpektraFilm processing **the same RAW's calibrated scene-linear development**, not from an unrelated test image. Keep full source and renderer metadata.

```bash
# Example: once reference + actual measured camera patches exist
portra160-lab fit-probes \
  --camera zf \
  --reference results/scene01-reference-patches.json \
  --kit build/portra160_camera_probes \
  --observations measurements/ \
  --out build/zf_next_test

# Also supports --camera x100v with observations under measurements/fujifilm_x100v/
```

The program creates **one proposed next test**, not a verified or ready-to-use look. Its coefficients come from a regularized, local linear model in CIE Lab. It deliberately limits extrapolation to observed step sizes. Re-render that proposal on the real camera engine and measure held-out photos before trusting it. Note that the initial X100V numeric probes are on Provia; other built-in film simulation bases are included only as discrete reference comparisons. More probes will be needed around whichever base performs best.

### Film roadmap, no substitutions

| Film | SpektraFilm profile | What happens next |
|---|---|---|
| **Portra 160** | Yes, `kodak_portra_160` / `kodak_portra_endura` | First calibration; still no verified camera-native recipe |
| Portra 400 | Yes, `kodak_portra_400` / `kodak_portra_endura` | Only after Portra 160 method is proven |
| Vision3 250D | Yes, `kodak_vision3_250d` / `kodak_2383` | Can reuse validated fitter; specific print choice must be documented |
| Ektachrome 400 | **No** (`kodak_ektachrome_100` is a different film) | Establish which historical 400 stock/version and find measured sensitometry; do not rename E100 |
| Tri-X 400 | **No** | Obtain the right B&W sensitometric data and build/test a monochrome film/print workflow |
| AeroColor IV 2460 | **No** | Use historical Kodak aerial-film measurement data, document processing conditions, and validate a new spectral profile |

Upstream profiles are listed in [`src/spektrafilm/data/profiles`](https://github.com/andreavolpato/spektrafilm/tree/main/src/spektrafilm/data/profiles). The project refuses to render stocks lacking an upstream profile rather than inventing an output that shares their name. Kodak's older Ektachrome 400X is a candidate historical stock, not automatically what the user meant by Ektachrome 400.

## Online Nikon Zf / Fujifilm X100V test images (added 2026-10-20)

The checked-in `data/sources/online_samples.json` gives direct, publisher-listed download URLs for **6 core files** and **4 extended files**, including a controlled X100V ISO 160 studio RAW+JPEG set, an X100V field RAW+JPEG set, and one Nikon Zf NEF plus a *tentatively paired* JPEG. Two other Nikon NEFs and another X100V pair can be added through `--set extended` or `--set all`.

The acquisition command works separately from SpektraFilm and only requires Python 3.13's standard library:

```bash
# Inspect all source URLs without network access
python scripts/acquire_samples.py --set all --dry-run

# Acquire a small core set to data/raw/ on your Mac
python scripts/acquire_samples.py --set core

# Acquire the 4 additional files
python scripts/acquire_samples.py --set extended

# Retry an individual item (for example if the publisher's studio host blocks access)
python scripts/acquire_samples.py --id x100v-studio-160-raf --force
```

The script downloads each file to a temporary `.part` file, rejects HTML responses / wrong file headers / implausibly small RAW or JPEG files, writes only after basic verification, computes SHA-256, and records local receipts in `data/raw/acquisition_report.json`. These checks establish file type, **not camera model or matched capture identity**. Subsequent EXIF inspection and image inspection are essential before using a pair in quantitative tests.

**Actual download status:** Public X100V RAF/JPEG studio and field pairs and a Nikon Zf NEF/JPEG pair were acquired locally on 2026-10-20. They remain gitignored copyrighted working files and are not redistributed. File headers identify the advertised camera models; the Nikon pair has matching timestamps. The Fuji studio RAF was developed and rendered through pinned SpektraFilm on a downsampled working copy. These samples validate pipeline behavior only: they are not a calibrated chart dataset and do not establish camera fidelity or hardware acceptance.

**License warning:** The linked review/test images remain the respective photographers' and publishers' copyrighted works. Use locally for personal review, and do not commit downloaded originals or redistribute them in ZIPs or public repos. For release-ready automated CI tests, substitute redistributable source imagery with explicit permissions. The `data/raw/` directory is gitignored.

**Calibration caveat:** These are mostly ordinary review images, **not measured ColorChecker photographs**. They are suitable for RAW pipeline integration, qualitative validation, repeatability checks, and comparing candidate rendering behavior. They **cannot establish absolute CIEDE2000 color accuracy** without a known target, controlled lighting, registration, and proper RAW input development. The Zf JPEG in the manifest is only tentatively associated with its NEF based on the review order and exposure; check capture time and content before treating it as the same shot.

Reviewed publishers:

- [Imaging Resource X100V ISO 160 studio images](https://www.imaging-resource.com/cameras/fujifilm-x100v-review/samples/) (RAF and same-stem camera JPEG).
- [Photography Blog X100V review samples](https://www.photographyblog.com/reviews/fujifilm_x100v_review) (RAF and JPEG).
- [Photography Blog Nikon Zf review samples](https://www.photographyblog.com/reviews/nikon_zf_review) (NEF and JPEG; matched-shoot identity needs verification).

## 1. Install on a Mac with Python 3.13

```bash
# Clone/unzip this repo, then from its root:
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'

# Upstream library: pin this exact revision to make results reproducible.
python -m pip install 'git+https://github.com/andreavolpato/spektrafilm.git@3bb2c2d2801ff68b92019cf1dbcbb133d60832bc'

# Basic quality checks
pytest -q
```

SpektraFilm has a comparatively large Python dependency tree including OpenImageIO and may require platform-specific build tools. Its own README currently recommends Python 3.13. If installation fails, diagnose the external dependency separately: **do not silently substitute an unrelated LUT.**

## 2. Prepare reference-quality input

Use a linear scene-referred `HxWx3` floating-point `.npy` RGB array in **linear ProPhoto RGB**, converted accurately from your RAW image, with fixed white balance and no tone-mapping or nonlinear edits. A display-encoded JPEG, Nikon NEF, or Fujifilm RAF is **not** this input. Record development transform, calibration target, reference illuminant, exposure, and white balance for every run.

You can save such an array as:

```python
import numpy as np
# img_linear_prophoto: your *actually calibrated* HxWx3 float array,
# in linear ProPhoto RGB, with scene highlights allowed above 1.0.
np.save('data/scene01_linear_prophoto.npy', img_linear_prophoto)
```

The tool intentionally does not include a fake RAW converter: camera-specific DNG/NEF/RAF color transforms and exposure calibration must be correct for maximum fidelity.

## 3. Generate the Portra 160 reference

```bash
# Color-only: deterministic, no grain/halation, to isolate the emulation's color behavior
portra160-lab render --stock portra160 \
  --input data/scene01_linear_prophoto.npy \
  --out results/scene01_color.npy --mode color

# Photographic reference: grain, halation, and spatial interactions enabled
portra160-lab render --stock portra160 \
  --input data/scene01_linear_prophoto.npy \
  --out results/scene01_full.npy --mode full
```

The `.npy` output is **display-encoded sRGB**, not scene-linear. It remains floating-point to avoid quantization. A JSON provenance sidecar records source, mode and parameters. Note that *full* mode is potentially stochastic. The version sidecar includes the expected source commit but cannot prove the installed checkout matches that SHA: retain the Git install log for that audit.

`color` mode relies on SpektraFilm's documented `debug.lut_mode` behavior to disable its spatial and stochastic effects, automatic exposure compensation, and per-image corrections. Therefore the **color** target is an intentionally different experiment from the **full photographic** target. Never present the color-only output as the full spectral-plus-grain image.

## 4. Extract real measured patches

First measure a **reference image** and a **camera JPEG/TIFF** with matching image content. For strict evaluation, prefer a uniformly lit chart or scene where target patches are registered to identical regions. Use *different* ROI coordinates when the camera images are not pixel-aligned.

```bash
portra160-lab extract \
  --image results/scene01_color.npy \
  --regions examples/regions.example.json \
  --out results/reference-patches.json

portra160-lab extract \
  --image measurements/zf_candidate01.tif \
  --regions measurements/zf_candidate01_regions.json \
  --out results/zf_candidate01-patches.json
```

When extracting from photo files, embedded ICC profiles are transformed into sRGB. Unprofiled images are rejected unless you explicitly pass `--assume-srgb`. A JPEG may have compression artifacts, so export a high-bit-depth, tagged image when possible. Mask or avoid gradients, specularities, and patch edges; this starter uses the median RGB within each rectangle. Do **not** average arbitrary unmatched pixels and report the result as calibration accuracy.

Candidate patch files need their provenance and the exact camera setting controls used:

```json
{
  "format": "portra160-patches-v1",
  "camera": "Nikon Zf",
  "name": "Portra160 experiment 01",
  "color_space": "sRGB",
  "encoding": "display-encoded",
  "settings": {"picture_control": "Flexible Color custom A", "source_file": "measurements/experiment01.NP3"},
  "patches": [{"id": "neutral-mid", "category": "neutral", "rgb": [0.5, 0.5, 0.5]}]
}
```

All candidate and reference patches must use the **same IDs**. Use full sets (skin, neutral, shadow, highlight, general) for genuine camera experiments; one patch is only a schema example.

## 5. Rank camera candidate renders

```bash
portra160-lab rank \
  --reference results/reference-patches.json \
  --candidates measurements/zf-*.json measurements/x100v-*.json \
  --out results/ranking.json
```

Candidates are ranked **within each camera**, never jointly. Current objective is category-weighted mean CIEDE2000: skin=3, neutral=2, highlight=2, shadow=1.5, general=1. These are configurable research preferences, **not a validated perceptual weighting standard**. Reports retain median, p95, max, individual patches and by-category mean. A future optimizer may use a Pareto frontier with guardrails on skin and highlights. No candidate is called validated unless independently tested on withheld scenes and lighting.

## New: film availability and export-format tests

You can now inspect which requested film stocks are actually present in the pinned SpektraFilm source:

```bash
portra160-lab list-stocks
```

Ten prioritized film/print combinations are registered for reference rendering: `portra160`, `portra400`, and `vision3_250d`. For example, **once SpektraFilm and calibrated linear input are available**:

```bash
portra160-lab render --stock portra400 --input data/scene01_linear_prophoto.npy --out results/portra400.npy --mode color
portra160-lab render --stock vision3_250d --input data/scene01_linear_prophoto.npy --out results/vision3_250d.npy --mode color
```

Ektachrome 400, Tri-X 400 and AeroColor IV correctly **refuse to render** until validated exact stock profiles exist. Ektachrome 100 does not silently replace Ektachrome 400.

Two experimental exporters can now produce **unvalidated camera test artifacts** without an installed SpektraFilm environment:

```bash
# Nikon NP3 byte-structure test file (LABNEUTRALTEST, NOT Portra)
portra160-lab zf-export --settings config/zf_neutral_import_test.json \
  --out build/nikon/PICCON01.NP3 --experimental

# Fuji X100V manually entered neutral settings (NOT Portra)
portra160-lab x100v-export --settings config/x100v_neutral_import_test.json \
  --out build/fuji/x100v_neutral.txt --experimental
```

An NP3 calibration file with custom tone curve and 8-color adjustments is serializable by `portra160_lab.nikon_np3.serialize`. The binary output has been checked for exact agreement with MIT-licensed NP3 examples from [ssssota](https://github.com/ssssota/nikon-flexible-color-picture-control), including comments and a 257-point tone curve. The MIT license appears at `third_party/nikon-flexible-color-picture-control.MIT.txt`. **This validates binary encoding, not Nikon camera acceptance or appearance.** The X100V renderer covers supported setting values and enforces DR ISO constraints; it does **not** write USB custom banks or invent a Portra recipe.

## Cameras and intended future exporters

### Nikon Zf

Produce an `.NP3` via [ssssota's reader/writer](https://github.com/ssssota/nikon-flexible-color-picture-control), with [NP3 Lab](https://github.com/MJ-best/np3-lab) as a tested Zf import reference. Constrain parameters to values supported by the camera and verify them in **NX Studio**. Be aware that a custom tone curve may replace separate contrast/highlight/shadow settings in the NP3 format. We must confirm a particular candidate produces the intended real Zf JPEG before claiming fidelity.

### Fujifilm X100V

Constrain the search to actual X100V custom-setting parameters, supported film simulations and firmware version. Use [fujifilm-ptp-reference](https://github.com/zgrimz/fujifilm-ptp-reference) and [FilmKit issue #1](https://github.com/eggricesoy/filmkit/issues/1) as evidence of reads and partial writes. Do not assume all camera/firmware combinations are writable. Prefer manually loading candidate settings for the first trials; later USB writes must backup, verify target bank, read back each changed property, and verify restoration.

## Capture/calibration protocol (required for meaningful fidelity)

1. Shoot a color chart + neutral reference + actual portraits/foliage using each camera's RAW+JPEG at fixed ISO, shutter, aperture, and manually selected white balance. Record camera firmware, lens, chart lighting, and raw processor settings. Use representative tungsten and daylight sessions.
2. Create a scene-linear ProPhoto RGB render from each *camera's own RAW*. Avoid baked look presets and auto tone processing. Develop matched, color-managed references using a chart-based camera input calibration. Record all profiles and exposure decisions.
3. Run SpektraFilm separately for each camera's source RAW development, with *identical* Portra 160/Endura film parameters.
4. Use each camera's own image processor to render candidate recipes from **the same RAW capture**. On the X100V, X RAW Studio is an option; on the Zf, NX Studio is an option. Their unattended automation and output reproducibility need an explicit feasibility spike.
5. Register charts and extract patches in display-encoded, color-managed sRGB. Fit candidate settings from those observed outputs, not hand-written equivalents of LUT RGB values.
6. Reserve entire scenes and at least one lighting condition for withheld validation. Measure category-specific accuracy, color shifts, tone response, and highlight clipping. Keep grain and halation as separate, perceptual full-render comparisons.
7. Save raw data, previews, source hashes, exact camera settings and firmware versions to an immutable experiment record. Preserve failures, not just winning settings.

## Design decisions and limitations

- **Maximum fidelity:** calibration needs real camera sample data. No extrapolation from Nikon to Fujifilm or another body.
- **Scene-linear correctness:** SpektraFilm's LUT creator currently disables scene-linear inputs until highlight-range shaper support is completed. Use the runtime instead of fabricating a linear `.cube`.
- **Color accuracy:** the deterministic color-only reference is the attainable camera-native objective; full grain/halation effects cannot be embedded losslessly in NP3 or Fuji custom banks.
- **Statistics:** deltaE2000 comparisons assume correct, *shared* color management and chart patch correspondence, not arbitrary scene RGB pixels.
- **Remote operation:** this project's comparison engine is tested locally; USB/NX Studio integration and actual camera tests are **future milestones**.

## Licensing

Project code: GPL-3.0-only. It imports SpektraFilm but does not redistribute source film profiles or LUT assets. The original SpektraFilm runtime is GPLv3. The Portra 160 profile is CC BY-SA 4.0 and must be attributed to **Andrea Volpato** with the original project URL when redistributed or encoded as derivative output. Retain this attribution in distributed recipes. Consult [the dedicated profile/LUT license](https://github.com/andreavolpato/spektrafilm/blob/main/SPEKTRAFILM_LICENSE.txt) before commercial distribution.

## Next implementation milestones

1. Color-managed RAW preprocessing from real Zf NEF / X100V RAF with measurable camera profile calibration and TIFF/EXR export.
2. Reproducible renderer automation feasibility experiments on NX Studio and Fujifilm X RAW Studio.
3. **Done (format layer):** Nikon NP3 serializer with binary fixtures; Fuji X100V manual-settings formatter with bounds checking. Need renderer-driven values and real hardware verification.
4. Optimization across calibrated camera renderings, followed by held-out validation.
5. Camera import/export and carefully checked backup/restore.

This prototype intentionally stops at the **measured candidate ranking** layer until inputs and renderer feasibility are verified.

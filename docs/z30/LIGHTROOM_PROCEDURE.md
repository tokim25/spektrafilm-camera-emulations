# Nikon Z30 Lightroom procedure

This is the Mac-side half of the Z30 work. The cloud session built the tools,
rendered the SpektraFilm references and tested the fitting on a simulated
stand-in. Only Lightroom itself can produce the evidence the look gate and the
install gate need, so these steps run on your Mac.

Every profile made here stays experimental until `z30-lightroom status` reports
its gates as met.

## 1. Set up the tools

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -e '.[lightroom,dev]'
git clone https://github.com/andreavolpato/spektrafilm.git third_party/spektrafilm-src
git -C third_party/spektrafilm-src checkout 3bb2c2d2801ff68b92019cf1dbcbb133d60832bc
pip install -e third_party/spektrafilm-src
z30-lightroom verify-source   # must print "verified": true
pytest -q
```

## 2. Collect NEFs and fix the split before measuring

1. Put the four public-domain files listed in `config/z30_samples.json` in
   `data/raw/z30/` and check their SHA-256 values.
2. Download the 41 Photography Blog NEFs to `data/raw/z30/photographyblog/`.
   They are copyrighted: keep them local and never commit them.
3. Write `data/z30_manifest.json` (format in `src/z30_lightroom/workflow.py`).
   Decide the split by rule before any measurement, so held-out scenes are never
   chosen after seeing results. Suggested rule: odd-numbered Photography Blog
   files and both garden files are `train`; even-numbered files and both toy
   files are `heldout`.
4. Record the exact Lightroom Classic version and Camera Raw version in the
   manifest's `lightroom` block. Your About box also settles which Lightroom
   version first supported the Z30, an open fact in `docs/z30/FACTS.md`.

## 3. Develop and export settings, identical for every export

| Setting | Value |
| --- | --- |
| Develop | Reset all, then White Balance "As Shot", Exposure and every slider 0 |
| Profile | The probe, identity or stock profile being tested, nothing else |
| Sharpening, Noise Reduction | 0 |
| Lens Corrections | Profile corrections off. A built-in Nikon correction that cannot be turned off is fine; registration handles it. |
| Crop | None |
| Export format | TIFF, no compression, 16 bits, ProPhoto RGB |
| Image sizing, output sharpening | Off |

The tools refuse exports that are not 16-bit or do not embed ProPhoto RGB.

## 4. Make profiles from `.cube` files in Camera Raw

Lightroom cannot make a profile from a LUT itself; Photoshop's Camera Raw can.
These menu names are from memory and may differ by version, so check them on
yours and correct this document if they do.

1. Open any Z30 NEF in Camera Raw from Photoshop and reset it to defaults.
2. In the Presets panel, Option-click the Create Preset button to open
   **Create Profile**.
3. Name it exactly like the `.cube` file, untick every setting group, and
   enable **Color Lookup Table**. Load the `.cube` file.
4. If the dialog offers a table space, choose ProPhoto RGB. Leave the amount
   range at its default and note the defaults you saw.
5. Restart Lightroom so the new profile appears in its Profile Browser.

Make every profile, probe, identity and stock alike, by exactly this method.
The fit depends on the identity profile and the stock profiles sharing one
pipeline.

## 5. Probe Camera Raw before fitting anything

```bash
z30-lightroom probe-kit --out build/z30_probe_kit
```

Make a profile from each of the four probe cubes. Export one colourful training
scene with each, then run:

```bash
z30-lightroom characterize --nef <nef> --scene-id <id> \
  --identity-export <identity.tif> --probe-export <rotate.tif> --probe rotate_rgb_gbr
```

It exits 0 only if Camera Raw applies the LUT to ProPhoto-encoded values at the
end of its pipeline, which is what the fit assumes. Repeat for `red_gain_085`
and `power_125`. If any probe fails, stop and report the output: the fit would
be built on a wrong assumption.

## 6. Fit, then validate on held-out scenes

1. Export every scene in the manifest with the identity profile.
2. Fit each available stock:
   `z30-lightroom fit --manifest data/z30_manifest.json --stock portra160`
3. Make a profile from each fitted `results/z30/luts/Z30_<stock>_experimental.cube`.
4. Export every held-out scene with each stock profile and list the files under
   `stock_exports` in the manifest.
5. `z30-lightroom evaluate --manifest data/z30_manifest.json --stock portra160`
   writes `results/z30/look_gate/look_gate_portra160.json`.

## 7. Install gate

Someone other than the author follows `docs/z30/INSTALL.md` on a clean
Lightroom and fills in `docs/z30/install_record_template.json`, saved as
`results/z30/install/<stock>.json`.

## 8. Check the gates

```bash
z30-lightroom status
```

The calibration gate (tungsten DCP from ColorChecker SG captures) has no
tooling yet and stays blocked, as `docs/z30/STATUS.md` explains.

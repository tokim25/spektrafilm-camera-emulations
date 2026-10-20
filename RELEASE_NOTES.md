# SpektraFilm Camera Lab 0.3: Phase 1 development release

October 20, 2026

**Not an everyday-use Portra 160 camera emulation yet.** User acceptance criteria require hardware proof and actual SpektraFilm reference comparisons. The X100V is now physically detected and has a verified read-only backup, but no custom-setting write, readback, or image-quality acceptance has been completed; Nikon hardware evidence is still absent.

## Shipped in this bundle

- End-to-end `render-raw` CLI plumbing from original Nikon `.NEF` / Fujifilm `.RAF` through optional rawpy provisional linear ProPhoto development to the **real upstream** SpektraFilm runner, with source hashes, clipping checks and audit sidecars.
- `prepare-raw`, `compare-scene`, and `phase1-status` CLI commands.
- An expanded prioritized film/print registry including Ektar 100, Portra 800, Vision3 50D, Vision3 500T, and Vision Premier 2393 as an alternate printing stage paired with Vision3 camera negatives. No other stock substitutions.
- Previous Nikon NP3 binary writer and X100V manual settings format writer, measured candidate optimizer, and developer camera-response probes.
- **51 local passing tests**. They cover code paths and numerical fixtures; they
  do not by themselves prove camera rendering, film fidelity, or hardware
  acceptance.

## Deferred camera-validation track

Hardware import, property-level readback, restoration, and practical image
quality remain future work. They do not block the experimental software and
reference release described here. No camera-ready claim is made.

- Public RAW/JPEG samples and the pinned SpektraFilm/rawpy runtime have since been acquired and executed; see the independent verification section below.
- Camera-rendered real outputs and actual Zf/X100V import acceptance have not been recorded.
- No measured camera-native Portra 160 settings have been generated.
- The native file **examples/nikon_zf_import_test/PICCON01.NP3** is a neutral format diagnostic, **not a Portra recipe**.

Run `portra160-lab phase1-status --workspace .` for the machine-readable blocker list. See `README.md` for the Mac RAW import path.

## Independent online-sample verification (2026-10-20)

The declared runtime was independently installed in `.audit-venv` with
NumPy 2.5.4, Pillow 12.3.0, pytest 9.1.1, rawpy 0.26.1, and the package's
exact SpektraFilm revision `3bb2c2d2801ff68b92019cf1dbcbb133d60832bc`.

With third-party pytest plugin autoload disabled to prevent SpektraFilm's
napari GUI test fixture from writing outside the workspace:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .../.audit-venv/bin/python -m pytest -q
48 passed in 0.09s
```

Public sample acquisition succeeded for X100V studio/field RAF+JPEG pairs and
a Nikon Zf NEF+JPEG pair. The acquisition receipt is local and gitignored.
The Fuji studio RAF developed through rawpy with clipped fraction
`0.0002804289`; the Nikon NEF developed with clipped fraction `0.05575985` and
must not be used for strict fitting without an unclipped workflow.

A real deterministic Portra 160 + Endura render completed on a documented
695x1041 downsampled Fuji working copy. The output is finite display-encoded
sRGB, range `0.0196575..0.8691247`, with the pinned source commit verified via
the installed distribution's `direct_url.json`. An exploratory six-region
comparison against the publisher JPEG measured mean ΔE00 `21.9580`; it remains
diagnostic only because the regions are not calibrated chart patches.

These results validate the software and reference-render path. They do not
constitute a camera-native recipe, physical NP3 import, X100V custom-setting
readback, or everyday-use release.

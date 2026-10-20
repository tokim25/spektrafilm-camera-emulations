# Independent audit report — Phase 1 / Kodak Portra 160

Audit date: 2026-10-20 (America/Los_Angeles)

## Executive conclusion

Phase 1 is not shippable as a camera-native Portra 160 emulation. The supplied
kit is a development scaffold with useful defensive guardrails, not a fitted
Nikon Zf or Fujifilm X100V recipe. Real X100V RAW/JPEG captures and provisional
SpektraFilm-vs-camera diagnostics now exist, including one held-out scene, but
there is still no camera import acceptance, property-level readback, measured
chart calibration, Nikon hardware test, or completed multi-scene release
validation.

The repository claim of “48 local passing tests” was stale. After installing
the declared dependencies in the project-local audit environment and adding
the safety/regression tests, the current suite is **51 passed**. The workspace
still is not a Git checkout, so there is no local commit history to audit.

## Pass 1 — code and provenance

Verified from the supplied files:

- The package has a coherent `src/` layout, a `pyproject.toml`, 12 test modules,
  configuration, sample-manifest, probe artifacts, and a Nikon MIT notice.
- The declared runtime is Python >=3.13 with NumPy and Pillow; pytest and rawpy
  are optional dependencies. No lockfile, hash-pinned environment, Git
  metadata, CI configuration, `AGENTS.md`, or issue/PR metadata is included.
- Portra 160 is registered as `kodak_portra_160` plus
  `kodak_portra_endura`; missing stocks fail closed. The source revision is
  recorded in metadata/documentation, but the package does not contain the
  upstream checkout, and runtime verification of that commit is explicitly
  false in the renderer metadata.
- The reference wrapper requires a floating-point HxWx3 `.npy` in linear
  ProPhoto RGB. The RAW path uses optional rawpy and labels its output
  provisional. It does not constitute a measured camera input calibration.
- CIEDE2000 is independently numerically correct against the Sharma/Wu/Dalal
  reference vector: `[2.04245968, 2.86151017, 3.4411906, 0.99999886]`.
- The NP3 writer is an experimental serializer based on an embedded upstream
  template. It deliberately refuses export without `--experimental` and
  reports camera import and color calibration as false.
- The X100V implementation is a manual text recipe formatter only. It does not
  implement USB read, backup, write, readback, or restoration.

Provenance checks against the upstream pages confirm that SpektraFilm exists,
contains its profile data under `src/spektrafilm/data/profiles`, and publishes
an explicit CC BY-SA 4.0 profile/LUT license and GPLv3 software license. The
kit’s attribution direction is therefore plausible, but it should ship the
upstream license text or a stable link alongside any derived profile/LUT-like
artifact. The NP3 source attribution is present through the MIT notice.

## Pass 2 — independent execution

The original missing-runtime blocker was later resolved in a project-local
`.audit-venv` using the declared dependencies plus the pinned SpektraFilm
checkout. The exact current evidence is:

- Public samples acquired into the gitignored `data/raw/` folder: X100V RAF/JPEG
  studio and field pairs, and Nikon Zf NEF/JPEG pair. File headers identify the
  X100V and Zf models; the Nikon NEF and JPEG timestamps match exactly.
- `pytest` passes **51/51** with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. The
  environment variable is required because SpektraFilm's napari dependency
  otherwise injects a GUI test fixture that cannot write its cache in this
  sandbox. This is an environment isolation detail, not a project-test failure.
- rawpy 0.27.1 developed the Fuji studio RAF into provisional linear ProPhoto
  RGB with clipped fraction `0.0002804289` (below the 0.2% guard). The Nikon
  NEF developed with clipped fraction `0.05575985`, so it is rejected for
  strict reference fitting unless an unclipped RAW workflow is used.
- SpektraFilm 0.3.4 installed from the requested Git revision
  `3bb2c2d2801ff68b92019cf1dbcbb133d60832bc`; the distribution's
  `direct_url.json` independently verifies that commit.
- A real deterministic `kodak_portra_160` + `kodak_portra_endura` color render
  completed on a documented 695x1041 downsampled Fuji working copy and was
  promoted to the canonical `results/portra160_reference.npy` artifact. The
  output is finite display-encoded sRGB with range `0.0196575..0.8691247`.
- An exploratory six-region comparison against the corresponding publisher
  JPEG produced mean/weighted ΔE00 `21.9580` (median `20.9530`, max `26.5027`).
  The regions are spatial boxes, not chart patches, so this is a pipeline
  diagnostic only; the report correctly leaves all camera-validation flags
  false.

This proves the RAW plumbing and upstream reference call can run. It does not
upgrade ordinary publisher review imagery into a calibrated chart target or
prove a camera-native Portra fit.

### Physical X100V evidence added after the initial audit

The camera was connected in USB Backup/Restore mode. Two full backups were
made; their SHA-256 hashes differ, confirming a state change after the user
entered the experimental C6 values manually. The original backup remains
available for restoration. Image Capture then downloaded physical RAF/JPEG
pairs. The C6 cube repeat (`DSCF4355`) measured mean/median/p95 ΔE00
5.34/4.77/10.39; the held-out plant scene (`DSCF4360`) measured
5.75/5.38/10.92. These reports use a provisional LibRaw camera-matrix input,
downsampled color render, and an exposure-only search; they are diagnostics,
not a validated recipe. No USB settings write or property-level readback was
performed.

Observed commands and results:

| Check | Result |
|---|---|
| `python3 --version` | Python 3.14.8 |
| `python3 -m pytest -q` | Failed before collection: `pytest` missing |
| `python3 -m unittest discover -s tests -v` | 12 import errors: missing pytest, NumPy, package path |
| `pip install -e '.[dev]'` | Failed: PEP 668 externally managed environment |
| clean `.venv` install | Failed: DNS unavailable while fetching build dependencies |
| CLI `phase1-status` / `list-stocks` | Failed at import: Pillow missing |
| direct CIEDE2000 vector | Passed independently |
| SpektraFilm render | Passed on documented downsampled Fuji working copy; full-resolution attempt exceeded several minutes without output |
| rawpy NEF/RAF development | Passed for Fuji; Nikon passed provisionally but clipped 5.58% |

The canonical reference is now reproducible, but it is still based on a
public review sample and provisional RAW development; it is not a calibrated
chart reference. No exposure comparison or genuine camera candidate score can
be claimed from this kit.
The existing workflow tests use monkeypatched renderer/RAW functions; they
verify plumbing, not the upstream renderer or a RAW file.

## Pass 3 — camera compatibility

The checked-in neutral NP3 is 496 bytes, begins with `NCP\0`, contains version
`0310`, and has the embedded name `LABNEUTRALTEST`. The two checked-in neutral
files have identical SHA-256:

`967bcdc7a045af9a53a99f2e6921b8e7eeb51acaf4dd467d48256f2351ae4b19`

This establishes only internal structure and deterministic serialization. It
does not establish Nikon Zf acceptance, NX Studio interpretation, or appearance
on a Zf. Those require a physical Zf, an expendable custom slot, a backup of
existing controls, import through Nikon’s supported workflow, and a captured
JPEG/NEF readback.

An independent run of the upstream MIT reader/writer package
`nikon-flexible-color-picture-control@1.0.0` deserialized the file and
re-serialized it byte-identically: 496 input bytes, 496 output bytes,
`byte_identical=true`, name `LABNEUTRALTEST`, version `0310`, contrast 0,
saturation 0. This proves format round-trip compatibility with that reference
implementation, not physical Zf acceptance.

The same independent round-trip also passed a generated 992-byte comment plus
257-point tone-curve fixture, preserving the comment, all 3 control points,
the raw endpoints/midpoint `[0, 16384, 32767]`, and byte identity.

The Fuji artifacts are trial sheets, not USB protocol support. Safe USB
procedures remain unimplemented and require a physical X100V, firmware/version
identification, an explicit destination bank, a complete pre-write backup, and
property-level readback plus restoration testing.

During this audit an actual X100V was connected through the official Fujifilm
TETHER APP 1.34.1 in `USB RAW CONV./BACKUP RESTORE` mode. A read-only full
settings backup was created before any write attempt:
`FUJIFILM_X100V_20261020_1129.dat`, 38,912 bytes,
SHA-256 `cd6967b9db012672be0ba6ac23de57c943f9207b59b0939a218c42f19cc4042e`.
The user initially selected C7, then changed the expendable destination to C5. The official application
offers only whole-camera restore in this mode; it does not accept the generated
text recipe or expose a supported per-bank write/readback API. The user entered
the candidate manually into C5 and a second official backup was created. It
remained 38,912 bytes but changed from SHA-256
`cd6967b9db012672be0ba6ac23de57c943f9207b59b0939a218c42f19cc4042e` to
`19a76f1cf468a64b72defc9116e8b258e650ac25c8d37c612bec2460d1165806`.
This proves that camera state changed after the C5 operation, but it is not
property-level readback and does not prove every requested value was stored.
The Fuji application gate remains false pending image-quality validation.

The user then supplied five new X100V RAF/JPEG pairs through macOS Image
Capture. The latest pair (`DSCF4330`, 11:42:20) was developed through LibRaw,
downsampled deterministically, and rendered with the pinned SpektraFilm
Portra 160/Endura profiles. The C5 JPEG is substantially brighter and warmer
than the unexposed reference. After an exposure-only search, the best offset
was +1.88 EV, but the full-image diagnostic remained mean ΔE00 14.71, median
13.83, and p95 21.85. This is a real same-scene diagnostic, not a chart fit;
it does not establish a camera-ready recipe, and the result reinforces that
the current neutral C5 candidate needs measured fitting.

The software now includes `portra160_lab.fuji_safe`, a transport-agnostic safety
wrapper that enforces those invariants and has three fake-transport tests. It
does not claim to implement Fujifilm's undocumented PTP command mapping; that
adapter still requires hardware/firmware testing.

## Misleading or incomplete claims

- “48 local passing tests” was stale; the current reproducible result is 51
  passed, with CI configuration present but no repository/CI run yet.
- “RAW download support” is a guarded downloader for publisher URLs; no binary
  originals are included, and downloads do not prove paired captures or color
  calibration.
- “Reference rendering” and “full photographic reference mode” are implemented
  wrappers, but neither was executed against the pinned SpektraFilm source in
  this environment.
- “Nikon NP3 export” means experimental byte serialization, not a validated Zf
  import or Portra profile.
- “Fujifilm X100V export” means manual text formatting, not camera protocol
  support or a writable custom-setting file.
- “Highest-fidelity camera-native interpretation” is not yet supported by
  measured camera data, fitted controls, held-out scenes, or hardware results.

## Smallest remaining ship set

1. Restore a real Git repository and add reproducible CI with a lockfile or
   fully pinned environment; make the full test count a CI artifact.
2. Install and verify the exact SpektraFilm commit, rawpy, and Pillow/NumPy in
   a supported environment; record package and source hashes.
3. Acquire legally usable, controlled Nikon Zf NEF and X100V RAF captures,
   preferably ColorChecker scenes, and calibrate RAW input transforms.
4. Produce deterministic Portra 160/Endura color-only references and separate
   full grain/halation references; verify exposure, encoding, gamut, clipping,
   and CIEDE2000 independently.
5. Fit supported Nikon controls from same-scene camera renders, export a named
   NP3, and verify round-trip in an independent reader plus physical Zf import.
6. Implement or explicitly narrow Fuji USB support; perform backup, explicit
   destination selection, write, readback, restoration, and physical X100V
   image-quality tests.
7. Validate held-out scenes and lighting, publish comparison images and error
   reports, preserve SpektraFilm attribution/share-alike notices, and only then
   label the artifacts camera-ready.

## Repository/PR status

Since the initial audit, probe-kit manifest generation was corrected to store
paths relative to the kit root. Two independently generated kits now have
identical manifests across different output directories, and the checked-in
kit was regenerated with the corrected format. This fixes reproducibility of
the diagnostic artifacts only; it does not create camera measurements.

No commit or pull request was created: the supplied directory contains no
`.git` directory or remote configuration, and no authorized GitHub connector
was available in this audit context. This report is therefore an uncommitted
local audit artifact until the project is restored as a Git repository.

The local GitHub CLI was checked again during continuation: account `tokim25`
is configured, but its token is invalid and requires interactive
`gh auth login`. Repository creation/publication therefore remains externally
blocked; no remote mutation was attempted.

Sources checked: [SpektraFilm](https://github.com/andreavolpato/spektrafilm),
[SpektraFilm license](https://github.com/andreavolpato/spektrafilm/blob/main/SPEKTRAFILM_LICENSE.txt),
and [the Nikon NP3 reader/writer reference](https://github.com/ssssota/nikon-flexible-color-picture-control).

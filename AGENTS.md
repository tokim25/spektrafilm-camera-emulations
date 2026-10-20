# AGENTS.md

## Scope

This project converts the SpektraFilm Portra 160/Endura reference into
measured, camera-native candidates for Nikon Zf and Fujifilm X100V. Do not
describe an artifact as a recipe, preset, or camera-ready release unless the
release gates below are evidenced in the repository.

## Engineering standards

- Keep the pinned SpektraFilm revision and all source/license attribution
  explicit. Do not substitute Fuji X Weekly or other community recipes.
- Keep film color, grain, and halation errors separate in measurements.
- Reject missing upstream profiles rather than silently substituting another
  stock.
- Never write camera settings without an explicit destination, complete backup,
  readback, and restoration procedure.
- Every new numerical transform needs an independent reference-vector or
  fixture test, and every camera claim needs same-scene evidence.

## Verification requirements

Before merging changes, run the declared test suite in a clean supported
environment, verify the pinned SpektraFilm source revision, and run the
independent audit checks. Tests that monkeypatch RAW or renderer calls prove
plumbing only; they do not prove film fidelity.

Hardware acceptance requires:

1. Nikon NP3 round-trip through an independent reader and physical Zf import.
2. Fuji X100V backup, explicit-bank write, property readback, restoration, and
   physical image capture.
3. Same-scene Portra reference and camera output measurements, plus held-out
   scene validation and published error reports.

## Release criteria

The release remains experimental until all three hardware gates and the
SpektraFilm reference-render gate are complete. The current neutral NP3 and
X100V sheets are diagnostics, not Portra 160 emulations.

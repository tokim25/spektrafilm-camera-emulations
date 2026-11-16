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

## Nikon Z30 Lightroom track

The maintainer extended the scope to Lightroom profiles for the Nikon Z30
(`src/z30_lightroom/`, `docs/z30/`). The same standards apply, plus:

- Goal stocks and their availability live in `config/z30_goal_stocks.json`.
  Stocks without a profile at the pinned commit fail closed. Moving the pin to
  reach upstream `dev` profiles needs the maintainer's approval.
- Acceptance thresholds are frozen in `config/z30_acceptance_thresholds.json`.
  Never loosen them because a gate failed.
- Results from the simulated Lightroom stand-in (`results/z30/simulation/`)
  prove pipeline mechanics only and never count toward a gate.
- Never write to a user's Lightroom folders or catalog from code. Installation
  follows `docs/z30/INSTALL.md`.

## Release criteria

The release remains experimental until all three hardware gates and the
SpektraFilm reference-render gate are complete. The current neutral NP3 and
X100V sheets are diagnostics, not Portra 160 emulations.

# Handoff: Nikon Z30 Lightroom work, cloud session to local Mac session

The goal is Lightroom profiles for the Nikon Z30 that reproduce pinned
SpektraFilm stock renders of the same RAW, within the frozen ΔE00 thresholds,
on held-out photos, with every number reproducible from this repository.

The cloud session (branch `claude/dreamy-shannon-e23nov`) built and tested the
tools. The remaining work needs Lightroom, Camera Raw and the camera, which
only exist on the Mac.

## Done in the cloud session

- `src/z30_lightroom/` package and `z30-lightroom` CLI. 76 tests pass (51
  existing, 25 new).
- References for 7 stocks on 4 public-domain Z30 NEFs, rendered at the pinned
  commit with runtime verification. The `.npy` files are not committed;
  `z30-lightroom reference` regenerates them.
- A simulated dry run (`scripts/z30_simulated_dry_run.py`) proving the fit and
  evaluate mechanics on real NEFs with a fake Lightroom. Its results never
  count toward a gate. The toy scene was used for diagnosis, so it is not a
  clean held-out scene.
- Procedure: `docs/z30/LIGHTROOM_PROCEDURE.md`. Install: `docs/z30/INSTALL.md`.
  Facts: `docs/z30/FACTS.md`. Chart capture settings: `docs/z30/CAPTURE_SETTINGS.md`.

## Open decisions for the maintainer

1. Double-X 5222 and Tri-X 400 exist only on upstream `dev`. Options: a
   separate recorded pin for those two, moving the whole pin, or keeping them
   blocked.
2. Superia 400 has no upstream profile. Only Superia X-TRA 400 exists. Keep it
   blocked, or switch the goal to X-TRA 400 under its real name.
3. HP5 Plus 400 has no upstream profile anywhere and stays blocked.

## Next steps on the Mac, in order

1. Set up tools: section 1 of the procedure. `z30-lightroom verify-source`
   must report `"verified": true`.
2. Download the 4 public-domain NEFs (`config/z30_samples.json`) and the 41
   Photography Blog NEFs (local only, never commit). Write
   `data/z30_manifest.json` with the split fixed by rule before measuring.
3. Probe Camera Raw (section 5). Stop if any probe fails.
4. Identity exports, fit each stock, make stock profiles, held-out exports,
   evaluate (section 6).
5. Install gate with a tester who did not build the profiles (section 7).
6. Calibration gate: ColorChecker SG captures under tungsten
   (`CAPTURE_SETTINGS.md`). No DCP tooling exists yet; building it is open work.
7. `z30-lightroom status` reports what is met.

## Rules that carry over

Read `AGENTS.md`. Never loosen a threshold after a failure. Never substitute a
stock. Never write to Lightroom folders or the catalog from code. Report
failures plainly.

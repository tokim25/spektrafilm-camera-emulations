# Film priority for SpektraFilm camera-native matching

**Cameras:** Nikon Zf and Fujifilm X100V. **Source of looks:** SpektraFilm only. **Priority:** measured fidelity. No Fuji X Weekly recipes, no third-party recipe shortcuts.

The exact [SpektraFilm revision](https://github.com/andreavolpato/spektrafilm/commit/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc) is pinned in `config/film_catalog.json`.

| Order | Desired look | Exact SpektraFilm input | SpektraFilm printed through | Status |
|---|---|---|---|---|
| 1 | **Portra 160** | `kodak_portra_160` | `kodak_portra_endura` | Phase 1; no hardware-validated camera preset yet |
| 2 | **Portra 400** | `kodak_portra_400` | `kodak_portra_endura` | Profile available; fit after phase 1 |
| 3 | **Vision3 250D** | `kodak_vision3_250d` | `kodak_2383` | Profile available; fit after phase 1 |
| 4 | **Ektar 100** | `kodak_ektar_100` | `kodak_portra_endura` | Profile available; queued |
| 5 | **Portra 800** | `kodak_portra_800` | `kodak_portra_endura` | Profile available; queued (not push variants) |
| 6 | **Vision3 50D** | `kodak_vision3_50d` | `kodak_2383` | Profile available; queued |
| 7 | **Vision3 500T** | `kodak_vision3_500t` | `kodak_2383` | Profile available; queued |
| 8 | **Kodak Vision Premier 2393** | VISION3 250D, 50D, or 500T | `kodak_2393` | Profile available as printing stock; alternate cinematic print workflow, **not a camera film** |

These combinations are registered with explicit keys in `config/film_catalog.json`, including `vision3_250d_2393`, `vision3_50d_2393`, and `vision3_500t_2393`. The 2393 combinations are technically permitted by the profile format but remain **unrendered and unvalidated** until execution with the pinned upstream pipeline.

## Deprioritized until real stock measurements are available

- **Ektachrome 400:** missing. The available Ektachrome 100 profile is not interchangeable.
- **Tri-X 400:** missing. Requires correct measured B&W negative model and print path.
- **AeroColor IV 2460:** missing. Requires its own aerial-film process/curve data.

## Phase 1 must pass all of these conditions before "ready"

1. Run the pinned SpektraFilm Portra 160 negative + Endura print simulation on appropriately developed camera RAWs.
2. Build camera-response measurements from the same RAW captures, fixed exposure/white balance, and real NX Studio / X RAW Studio rendering.
3. Optimize Nikon custom Picture Control values and Fujifilm native custom settings against the actual rendered reference.
4. Verify a resulting `.NP3` imports into the physical Zf and Fujifilm settings work on a physical X100V.
5. Measure color and tone error on withheld images, including skin, green foliage, and mixed lighting, not just a tuning chart.
6. Preserve an export bundle with exact settings, source profile identifiers, experiment manifests, credit/CC BY-SA attribution and an honest remaining-error report.

Current phase 1 status: **NOT SHIPPED FOR EVERYDAY USE**. This repository ships the tested engineering components and native diagnostics; it does not ship validated Portra 160 presets.

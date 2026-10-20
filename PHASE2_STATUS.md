# Phase 2 status — reference expansion

Phase 2 begins with the reference-rendering track. It does not claim camera
recipes or hardware validation.

## Verified on 2026-10-20

Using SpektraFilm 0.3.4 at commit
`3bb2c2d2801ff68b92019cf1dbcbb133d60832bc`, the deterministic color-only
pipeline rendered the held-out X100V plant RAW-derived scene (`DSCF4360`) for
all nine available Phase 2 combinations:

- Portra 400 + Portra Endura
- VISION3 250D + Kodak 2383
- Ektar 100 + Portra Endura
- Portra 800 + Portra Endura
- VISION3 50D + Kodak 2383
- VISION3 500T + Kodak 2383
- VISION3 250D + Vision Premier 2393
- VISION3 50D + Vision Premier 2393
- VISION3 500T + Vision Premier 2393

Portra 400 was also rendered for the repeated cube scene. Outputs are
display-encoded sRGB arrays with sidecar metadata recording the exact film,
print, input encoding, and upstream commit.

## Not yet done

These are reference renders only. Phase 2 still needs camera-response fitting,
measured comparisons, and export review for each stock. Vision Premier 2393 is
treated only as a print-film option, never as a camera negative. Missing
profiles remain rejected rather than substituted.

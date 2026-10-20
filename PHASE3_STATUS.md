# Phase 3 status — reproducible reference matrix

Phase 3 starts the measured-candidate workflow with a batch reference matrix.
The new `render-matrix` command renders selected stocks, or every upstream
profile in the catalog, from one scene-linear ProPhoto input and writes a
manifest containing film, print, output, and pinned-commit verification.

Example:

```text
portra160-lab render-matrix --input scene_linear.npy --out-dir results/matrix --stocks portra400 vision3_250d
```

The manifest explicitly records that no camera recipe or hardware validation
was generated. Phase 3 still needs measured camera outputs before any fitting
or export can be called a camera emulation.

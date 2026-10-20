# Alternatives to an owner-provided gray-card scene

## What can be substituted

The project can use legally accessible third-party RAW/JPEG pairs for three
limited purposes:

1. **RAW plumbing and model identification.** The existing X100V and Zf pairs
   are sufficient to verify headers, demosaicing, color-space handling, and
   deterministic SpektraFilm rendering.
2. **Exposure/noise stress tests.** The Imaging Resource X100V review publishes
   RAF/JPEG pairs across ISO 80–51200 with exposure metadata. These are useful
   for exposure and noise behavior, but are copyrighted review material and
   are not controlled color targets: [sample index](https://www.imaging-resource.com/cameras/fujifilm-x100v-review/samples/).
3. **A proxy studio-scene comparison.** DPReview states that its Zf review used
   its standard studio test scene, but the page does not provide a traceable
   color-chart calibration target. It can support qualitative comparison only:
   [Zf studio-scene report](https://www.dpreview.com/articles/6308510174/nikon-zf-added-to-studio-scene/).

## What cannot be substituted

No online sample found in the audit provides all of: exact camera settings,
known illuminant, a documented ColorChecker/gray-card target, paired RAW and
out-of-camera JPEG, and redistribution rights. Therefore online samples cannot
clear the measured-fit, held-out validation, or physical import gates.

## Practical replacement paths

- **Best:** borrow or rent each camera for one hour and photograph a ColorChecker
  Classic or a neutral gray card under a fixed daylight source. This is the
  smallest experiment that clears the calibration uncertainty.
- **Second best:** obtain permission from a test lab or reviewer for original
  chart RAWs and their scene metadata. Treat the data as private evidence and
  do not commit the binaries.
- **Software-only release:** publish the current artifacts as an experimental
  SpektraFilm reference and NP3/recipe scaffold, explicitly excluding
  camera-ready claims. This does not satisfy Phase 1 ship criteria.

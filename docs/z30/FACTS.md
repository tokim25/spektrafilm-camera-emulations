# Nikon Z30 and Lightroom facts

Each fact has a source or a measurement. Unverified items stay marked until
someone checks them.

## Verified

| Fact | Value | Evidence |
| --- | --- | --- |
| NEF bit depth | 12-bit and 14-bit both offered | CC0 files `NIKON_Z30_12BIT.NEF` and `NIKON_Z30_14BIT.NEF` from raw.pixls.us; white levels 4095 and 16383 |
| NEF compression | Lossless compressed | MakerNote `NEFCompression` in all four CC0 files; Sans Mirror review says it is the only RAW option |
| Black level | 252 (12-bit), 1008 (14-bit), all channels | rawpy 0.26.1 / LibRaw 0.22.0 |
| Sensor output size | 5600 x 3728, RGGB-type pattern | rawpy |
| LibRaw colour matrix (XYZ to camera) | `[[1.0339, -0.3822, -0.0890], [-0.4183, 1.2023, 0.2436], [-0.0671, 0.1638, 0.7049]]` | rawpy `rgb_xyz_matrix`. Used only for the provisional reference development; never written into a profile, because LibRaw takes it from Adobe's DNG data. |
| SpektraFilm stocks at the pin | 7 of the 11 goal stocks exist | `config/z30_goal_stocks.json`; listed from the pinned checkout |
| SpektraFilm colour mode | Deterministic and strictly per pixel | Permuted, cropped and repeated renders all matched exactly (difference 0.0) |
| Kodachrome 64 | Positive film, rendered as a direct scan; print profile unused | Output identical with two different print profiles |

## Not yet verified

| Question | Why it matters | How to settle it |
| --- | --- | --- |
| First Lightroom / Camera Raw version with Z30 support | Records the minimum supported version | Adobe's supported-cameras page (blocked from the cloud session) or your Lightroom About box |
| Adobe profiles shipped for the Z30 | Which base the identity profile sits on | Lightroom Profile Browser on a Z30 NEF |
| Where Camera Raw applies a profile LUT, and in which encoding | The fit assumes ProPhoto-encoded values at the end of the pipeline | `z30-lightroom characterize` with the probe kit |
| Create Profile dialog names and table-space options | The procedure's menu steps | Camera Raw on your Mac |
| Whether Lightroom cloud renders the same as Classic | Parity is reported, not gated | Export the same scene from both and compare |
| Whether Z lens distortion correction can be turned off | Affects alignment only; registration handles it either way | Lens Corrections panel |

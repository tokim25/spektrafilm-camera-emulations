# Z30 chart capture settings

These settings apply to the ColorChecker SG captures for the calibration gate. They were agreed with the maintainer on 2026-11-14.

## Calibration resources

| Resource | Answer |
| --- | --- |
| Chart | ColorChecker SG (140 patches). Define the neutral, skin and saturated groups from its patch IDs in the committed groups file. |
| Reference values | Published X-Rite values only, no spectrophotometer. Use the values for the chart's formulation (record the chart's batch or purchase date and which value set you used). Expect roughly 0.5 to 1 ΔE00 of extra uncertainty from batch variation and aging, and say so in every calibration report. |
| D50/D65 lighting | None at present. |
| Illuminant A lighting | A tungsten or halogen bulb. |

Because only tungsten light is available, a dual-illuminant DCP is not possible yet. Build a single-illuminant profile calibrated under the bulb, and label it that way. Do not extend it to a daylight illuminant by guessing. Report that the profile is unvalidated for daylight scenes, and keep the calibration gate blocked for daylight until daylight chart captures exist.

The held-out chart capture must be a separate session: re-position the chart and light, and re-expose, rather than reuse frames from the training session.

## Lens and fixed camera settings

Lens: NIKKOR Z 28mm f/2.8 for every calibration and test shot. It is a full-frame lens, so on the Z30 it gives a field of view like 42mm on full frame. Record whether it is the standard or SE version, and the lens firmware version.

Fixed settings. Record every one in each manifest, along with the Z30 firmware version. Before shooting, confirm each menu item exists on the Z30 and note any that do not.

| Setting | Value | Why |
| --- | --- | --- |
| Image quality | NEF (RAW) + JPEG fine | RAW is the measured input. The same-shot JPEG helps with pairing and sanity checks only. |
| NEF compression | Lossless compressed | No lossy step in the RAW data. |
| NEF bit depth | 14-bit (verified available on the Z30) | More tonal precision. |
| Exposure mode | Manual | Keeps exposure identical between frames. |
| ISO | 100, Auto ISO off | Base ISO, lowest noise. |
| Aperture | f/8 | Sharp across the chart, with less vignetting than wide open. |
| Shutter speed | Set so the brightest SG patch is just below clipping in the RAW. Use 1/30 s or slower under the bulb | Slow speeds average out mains-frequency flicker. Check clipping in the RAW file, because the camera's histogram is based on the JPEG. |
| Exposure brackets | 0, −1/3 EV, +1/3 EV | Lets Codex choose the frame with no clipped patches. |
| Active D-Lighting | Off | It changes exposure and tone handling. |
| Vignette control | Off | Lightroom lens corrections are also turned off for calibration renders. Uneven light is corrected with a flat-field frame instead. |
| Diffraction compensation | Off | Affects JPEG sharpening only, but keep it fixed. |
| Auto distortion control | Off, if the camera allows it | Keep geometry consistent with the RAW. |
| High ISO and long exposure noise reduction | Off | Long exposure NR can alter the RAW with a dark frame. |
| Picture Control | Neutral (NL), all adjustments at default | Affects the JPEG and Lightroom's Camera Matching profiles only. It does not change RAW data, but it must be fixed and recorded. |
| Color space | sRGB | Matches the existing comparison tooling. JPEG only. |
| White balance | Preset manual (PRE), measured off the SG's neutral area under the bulb | RAW white balance is metadata, but a measured preset makes the as-shot JPEG comparable. Keep Lightroom on "As Shot". |
| Focus | Single AF on the chart center, then switch to manual focus | Focus cannot shift between frames. |
| Release | Tripod, with self-timer or a remote | No camera shake. |

Capture setup:

1. Darken the room so the bulb is the only light. Let a halogen bulb warm up for at least 10 minutes. Record the bulb's make, model, and rated color temperature.
2. Use 45/0 geometry: light at 45 degrees to the chart, camera square to it, chart centered and filling most of the frame. Check the frame for glare on the patches.
3. Shoot one flat-field frame of an even gray or white card in the chart's position, with identical settings.
4. In Lightroom, set every develop slider to zero, turn lens corrections off, keep "As Shot" white balance, and record the process version.

# Installing and removing an experimental Z30 profile

These steps never touch a Lightroom catalog. Follow them in order and record
each result in `docs/z30/install_record_template.json`.

## 1. Back up

Quit Lightroom and Photoshop. Copy these folders somewhere safe and note the
copy's location in the record:

- macOS: `~/Library/Application Support/Adobe/CameraRaw/Settings/`
- Windows: `C:\Users\<you>\AppData\Roaming\Adobe\CameraRaw\Settings\`

Camera Raw stores profiles made in its Create Profile dialog in that folder.
These paths are from Adobe's usual layout; confirm them on your machine.

## 2. Install

Make the profile from the stock's `.cube` file using section 4 of
`docs/z30/LIGHTROOM_PROCEDURE.md`, or copy a profile `.xmp` someone else made
into the Settings folder. Restart Lightroom.

## 3. Read back

1. Open a Z30 NEF, open the Profile Browser and confirm the profile appears
   under the exact expected name.
2. Apply it and export with the settings in section 3 of the procedure.
3. Run `z30-lightroom evaluate` on that export, or compare it by eye with the
   reference image shipped alongside the profile. Record what you saw.

## 4. Uninstall and restore

Quit Lightroom and Photoshop, delete the profile's `.xmp`, restore the backed-up
Settings folder over the current one, restart, and confirm the profile is gone
and your own profiles are back.

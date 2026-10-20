# Phase 1 hardware validation checklist

This checklist is required before Portra 160 can be labelled camera-ready.
The current software artifacts are experimental and must not overwrite camera
settings without a backup and an explicitly selected destination.

## Nikon Zf

1. Record the Zf firmware version and confirm that Nikon NX Studio or the
   camera's supported Picture Control import workflow is available.
2. Photograph a controlled daylight chart scene in RAW+JPEG at the camera's
   neutral/base configuration. Record lens, ISO, shutter, aperture, white
   balance, exposure compensation, and lighting.
3. Back up all existing custom Picture Controls and select an expendable
   destination slot by number.
4. Import the experimental NP3 into that slot. Do not replace an existing
   slot unless its backup has been verified.
5. Read the slot back through the supported Nikon workflow and record the
   imported name and settings. A successful file copy is not sufficient.
6. Photograph the same chart and at least two held-out scenes using the
   imported control, preserving exposure and white balance.
7. Transfer the resulting JPEGs and RAWs, plus the original backup and import
   logs, into a private evidence directory. Run the comparison and fitting
   commands from `START_HERE.txt`.
8. Restore the original slot and verify that the restored readback matches the
   backup byte-for-byte or property-for-property.

## Fujifilm X100V

1. Record X100V firmware and confirm the camera is visible to the chosen USB
   transport. Do not assume that a protocol observed on another Fuji model is
   supported by the X100V.
2. Manually record all seven custom banks, or export them through a supported
   Fujifilm tool. This is the recovery backup.
3. Choose an explicit expendable destination bank (C1–C7) and record it in
   the test log. Never select a destination implicitly.
4. Perform a read-only discovery/readback first. If the transport cannot
   enumerate and read the bank, stop; do not attempt a write.
5. Write the experimental recipe only after the backup and destination have
   been confirmed. Capture the returned property values and read the bank
   back independently.
6. Photograph the same controlled chart and two held-out scenes with the
   imported bank. Preserve exposure, white balance, and film simulation
   settings in the log.
7. Restore the original bank and verify every backed-up property. If any
   property differs, stop and restore manually before proceeding.

## Acceptance evidence

The release report must include camera model/firmware, backup hashes or
property dumps, destination slot, import/readback output, original and
candidate images, held-out ΔE00 results, and restoration confirmation. Online
review photographs are acceptable for pipeline testing but cannot satisfy the
controlled-chart or hardware-acceptance gates.

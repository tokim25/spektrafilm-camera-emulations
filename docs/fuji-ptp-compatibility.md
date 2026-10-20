# Fujifilm X100V USB/PTP compatibility boundary

The X100V is an X-Trans IV body. The public `fujifilm-ptp-recipes` protocol
documentation reports the C1–C7 slot protocol as confirmed on X-Trans V bodies
but says the tested X-Pro3 (also X-Trans IV) fails on that path. Therefore this
project does not claim that the observed vendor properties work on an X100V.

The X100V manual independently confirms seven custom banks and the supported
manual workflow: `IMAGE QUALITY SETTING > EDIT/SAVE CUSTOM SETTING`, followed by
selecting a bank and saving settings. Fujifilm also documents `BACKUP RESTORE`
through X Acquire. These are the safe fallback procedures until an X100V
firmware-specific USB trace is available.

## What is implemented

`portra160_lab.fuji_safe` provides a transport-agnostic transaction guard:

1. Read and retain all C1–C7 banks.
2. Require an explicit destination bank.
3. Write only that bank through a caller-supplied transport.
4. Read back the complete bank and compare exact values.
5. Restore the original bank if write or readback fails.

The module intentionally does not encode the observed `0xD18C`–`0xD1A4`
property range or claim that it applies to X100V. Those commands are unsafe to
guess across generations and firmware versions.

## Required hardware procedure

Record the X100V firmware version, use Fujifilm X Acquire or manual menu entry
to back up C1–C7, perform read-only USB probing first, and test one expendable
bank. Capture the complete before/after property dump and restore the original
bank. Any failure stops the test; do not retry by writing another bank.

Sources:

- [Fujifilm X100V manual: custom settings](https://app.fujifilm-dsc.com/en/manual/x100v/menu_shooting/image_quality_setting/index.html)
- [Observed Fuji PTP protocol](https://github.com/ILFforever/fujifilm-ptp-recipes/blob/main/docs/protocol.md)
- [Protocol status and tested-body boundary](https://github.com/ILFforever/fujifilm-ptp-recipes/blob/main/README.md)

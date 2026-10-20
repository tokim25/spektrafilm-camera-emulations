# X100V C1–C7 tooling review

## What GitHub can and cannot do

GitHub can distribute recipe sheets, backups, documentation, and a local tool. It cannot write the X100V directly. The camera must be connected locally over PTP, and any write must be preceded by a complete backup and an explicitly selected destination bank.

Fujifilm's supported path is X Acquire/Tether for camera backup and restore. The X100V manual documents `USB RAW CONV./BACKUP RESTORE` for X Acquire and `USB CARD READER` for file copying. Fujifilm also documents that X Acquire can save and restore EDIT/SAVE CUSTOM SETTING data on the X100V.

## Candidate tools

| Project | What it offers | Status for X100V |
|---|---|---|
| [fuji-ptp-core](https://github.com/AlPeFe/fuji-ptp-core) | Direct USB/PTP read/write library and desktop test client; documents C1–C7 selector/name/property operations and reports real-camera C1–C7 reads and C7 round-trip tests. | Best technical starting point, but X100V model/firmware compatibility is not established here. Full backup/restore blobs are not implemented. |
| [FilmKit fork](https://github.com/jeffinvan/filmkit-fork) | Browser/WebUSB camera connection, RAF preview, and custom-setting read/write based on the reverse-engineered PTP protocol. | Useful local UI candidate; X100V support must be verified read-only before use. |
| [Latent](https://github.com/formray/latent) | Recipe library, backups, guarded writes, readback, and RAF preview in Chromium/WebUSB. | Safety-oriented candidate, but its published hardware validation focuses on other Fuji bodies, not this X100V. |
| [omarchy-fujifilm-recipes](https://github.com/ctl0v0/omarchy-fujifilm-recipes) | Local C1–C7 manager with backup and explicit overwrite guard. | Interesting safety pattern, but targeted at X100VI/Linux and not proven on X100V. |
| [fujifilm-ptp-recipes protocol](https://github.com/ILFforever/fujifilm-ptp-recipes/blob/main/docs/protocol.md) | Protocol reference for selector `0xD18C`, name `0xD18D`, and custom-setting properties. | Reference material, not an installer. |

## Recommended route

Use official X Acquire for the first complete backup and restoration path. Then use a local, read-only PTP inspection step to identify the X100V's seven banks and property layout. Only after that should a tool write one explicitly chosen expendable bank, read it back, and restore the backup.

The repository currently has one experimental Portra 160 C6 sheet. It does not have measured X100V values for the Phase 2 stocks, so automatically filling C1–C7 with those stocks would invent camera data. The next safe deliverable is a bank manifest and import assistant that accepts reviewed values, rather than a blind seven-bank writer.

## Required safety sequence

1. Close Image Capture, Photos, X RAW Studio, and X Acquire before a third-party PTP tool connects.
2. Set the camera to `USB RAW CONV./BACKUP RESTORE`.
3. Make and preserve a full X Acquire backup.
4. Perform read-only bank/property discovery.
5. Select one expendable bank explicitly.
6. Write one reviewed candidate, read back every field, and save the readback.
7. Restore the backup and verify restoration.

No tool in this review is treated as X100V-ready until that sequence has been completed. No camera write is performed by CI, GitHub Actions, or a release download.

#!/usr/bin/env python3
"""Download publisher-hosted camera samples for local, personal evaluation.

No downloaded image is included with or redistributed in this project.
Source URLs and camera metadata are public claims, not verification of a pair.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = HERE / "data/sources/online_samples.json"
DEFAULT_DEST = HERE / "data/raw"
MAX_BYTES = 130 * 1024 * 1024
MIN_RAW_BYTES = 1_000_000
MIN_JPEG_BYTES = 100_000


def file_magic_ok(filename: Path, fmt: str) -> bool:
    with filename.open("rb") as handle:
        header = handle.read(32)
    if fmt == "raf":
        return header.startswith(b"FUJIFILMCCD-RAW ")
    if fmt == "nef":
        return header.startswith((b"II*\x00", b"MM\x00*", b"II+\x00"))
    if fmt in {"jpg", "jpeg"}:
        return header.startswith(b"\xff\xd8\xff")
    return False


def verify_existing(filename: Path, fmt: str) -> dict:
    size = filename.stat().st_size
    minimum = MIN_RAW_BYTES if fmt in {"raf", "nef"} else MIN_JPEG_BYTES
    if size < minimum or size > MAX_BYTES or not file_magic_ok(filename, fmt):
        raise ValueError(f"Unexpected {fmt.upper()} file: size {size}, incorrect file signature or download is incomplete")
    hasher = hashlib.sha256()
    with filename.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return {"bytes": size, "sha256": hasher.hexdigest(), "magic_valid": True,
            "camera_model_verified": False, "pair_verified": False}


def download_one(sample: dict, dest: Path, *, force: bool = False,
                 timeout: int = 60, opener=urlopen) -> dict:
    """Fetch one sample into a private folder and audit it before accepting it.

    `opener` is injectable for offline unit tests. The HTTP URL is from the
    checked-in manifest, never from third-party file contents.
    """
    dest.mkdir(parents=True, exist_ok=True)
    ext = sample["format"].lower()
    target = dest / f'{sample["id"]}.{ext}'
    if target.is_file() and not force:
        return {"id": sample["id"], "status": "already_present", "path": str(target),
                **verify_existing(target, ext)}
    tmp = dest / (target.name + ".part")
    tmp.unlink(missing_ok=True)
    req = Request(sample["url"], headers={"User-Agent": "Portra160-CameraLab/0.2 (personal image evaluation)", "Accept": "*/*"})
    try:
        with opener(req, timeout=timeout) as response, tmp.open("wb") as out:
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" in content_type or "application/json" in content_type:
                raise ValueError(f"Received {content_type} instead of the original image")
            size = 0
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError(f"Refusing file larger than {MAX_BYTES} bytes")
                out.write(chunk)
        details = verify_existing(tmp, ext)
        tmp.replace(target)
        return {"id": sample["id"], "status": "downloaded", "path": str(target), **details}
    except (HTTPError, URLError, OSError, ValueError):
        tmp.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--set", choices=("core", "extended", "all"), default="core")
    parser.add_argument("--id", action="append", dest="ids", help="Download only this sample (repeatable)")
    parser.add_argument("--dry-run", action="store_true", help="Show URLs without downloading")
    parser.add_argument("--force", action="store_true", help="Redownload existing local samples")
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args(argv)
    manifest = json.loads(args.manifest.read_text())
    chosen = [s for s in manifest["samples"] if (s["id"] in args.ids if args.ids else (args.set == "all" or s["set"] == args.set))]
    if args.ids and set(args.ids) - {x["id"] for x in chosen}:
        parser.error("Unknown sample ID: " + ", ".join(sorted(set(args.ids) - {x["id"] for x in chosen})))
    if not chosen:
        parser.error("No samples selected")
    summary = {"manifest_schema": manifest["schema"], "checked_utc": datetime.now(timezone.utc).isoformat(), "samples": []}
    failures = 0
    for sample in chosen:
        if args.dry_run:
            print(f'{sample["id"]}: {sample["url"]}')
            continue
        try:
            outcome = download_one(sample, args.dest, force=args.force, timeout=args.timeout)
        except Exception as err:
            outcome = {"id": sample["id"], "status": "failed", "error": str(err)}
            failures += 1
        summary["samples"].append({**outcome, "camera": sample["camera"], "scene": sample["scene"],
                                   "source_page": sample["source_page"], "pair_id": sample["pair_id"],
                                   "pair_verification": sample["pair_verification"],
                                   "rights": sample["rights"]})
        print(f'{sample["id"]}: {outcome["status"]}' + (f' ({outcome["error"]})' if "error" in outcome else ""))
    if not args.dry_run:
        args.dest.mkdir(parents=True, exist_ok=True)
        receipt = args.dest / "acquisition_report.json"
        receipt.write_text(json.dumps(summary, indent=2) + "\n")
        print(f"Audit saved: {receipt}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

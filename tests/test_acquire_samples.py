from __future__ import annotations

import importlib.util
from io import BytesIO
from pathlib import Path

import pytest

module_path = Path(__file__).resolve().parent.parent / "scripts/acquire_samples.py"
spec = importlib.util.spec_from_file_location("acquire_samples", module_path)
acquire = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acquire)


class FakeStream(BytesIO):
    def __init__(self, payload, mime="application/octet-stream"):
        super().__init__(payload)
        self.headers = {"Content-Type": mime}


def sample(fmt="raf"):
    return {"id": "x100v-test", "format": fmt, "url": "https://example.org/a.raf"}


def test_recognizes_fuji_raf(tmp_path):
    image = tmp_path / "good.raf"
    image.write_bytes(b"FUJIFILMCCD-RAW " + b"\0" * acquire.MIN_RAW_BYTES)
    receipt = acquire.verify_existing(image, "raf")
    assert receipt["bytes"] > 1_000_000
    assert receipt["magic_valid"]
    assert not receipt["camera_model_verified"]


def test_recognizes_nikon_tiff_header(tmp_path):
    image = tmp_path / "good.nef"
    image.write_bytes(b"II*\x00" + b"\0" * acquire.MIN_RAW_BYTES)
    assert acquire.verify_existing(image, "nef")["magic_valid"]


def test_rejects_jpg_disguised_as_raw(tmp_path):
    image = tmp_path / "bad.raf"
    image.write_bytes(b"\xff\xd8\xff" + b"\0" * acquire.MIN_RAW_BYTES)
    with pytest.raises(ValueError):
        acquire.verify_existing(image, "raf")


def test_rejects_html_download_and_cleans_part(tmp_path):
    def opener(req, *, timeout):
        return FakeStream(b"<html>not an image</html>", mime="text/html")
    with pytest.raises(ValueError, match="HTML|text/html"):
        acquire.download_one(sample(), tmp_path, opener=opener)
    assert not list(tmp_path.glob("*.part"))
    assert not list(tmp_path.glob("*.raf"))


def test_good_download_is_atomic(tmp_path):
    payload = b"\xff\xd8\xff" + b"A" * acquire.MIN_JPEG_BYTES
    def opener(req, *, timeout):
        return FakeStream(payload, mime="image/jpeg")
    record = acquire.download_one(sample("jpg"), tmp_path, opener=opener)
    assert record["status"] == "downloaded"
    assert (tmp_path / "x100v-test.jpg").read_bytes() == payload
    assert not list(tmp_path.glob("*.part"))
    record2 = acquire.download_one(sample("jpg"), tmp_path, opener=opener)
    assert record2["status"] == "already_present"


def test_missing_existing_file_is_not_marked_verified(tmp_path):
    with pytest.raises(FileNotFoundError):
        acquire.verify_existing(tmp_path / "missing.nef", "nef")

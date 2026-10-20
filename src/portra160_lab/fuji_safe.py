"""Safety wrapper for Fujifilm custom-setting transactions.

This module deliberately does not guess USB/PTP command IDs.  A transport
adapter must provide the camera-specific read/write operations, while this
layer enforces explicit slot selection, complete backup, readback, and
restoration on failure.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol


SLOT_NAMES = tuple(f"C{i}" for i in range(1, 8))


class FujiTransport(Protocol):
    def read_custom_slot(self, slot: str) -> Mapping[str, object]: ...
    def write_custom_slot(self, slot: str, settings: Mapping[str, object]) -> None: ...


@dataclass(frozen=True)
class TransactionResult:
    slot: str
    backup: dict[str, object]
    requested: dict[str, object]
    readback: dict[str, object]
    restored: bool = False


def _slot(slot: str) -> str:
    if slot not in SLOT_NAMES:
        raise ValueError(f"destination must be one of {', '.join(SLOT_NAMES)}")
    return slot


def backup_custom_slots(transport: FujiTransport) -> dict[str, dict[str, object]]:
    """Read all seven banks before any write is permitted."""
    return {slot: dict(transport.read_custom_slot(slot)) for slot in SLOT_NAMES}


def write_with_readback(
    transport: FujiTransport,
    *,
    destination: str | None,
    settings: Mapping[str, object],
    backup: Mapping[str, Mapping[str, object]] | None,
) -> TransactionResult:
    """Safely write one explicitly selected bank and verify exact readback.

    `backup` must be a complete seven-bank snapshot from
    :func:`backup_custom_slots`; there is intentionally no default slot.
    On write/readback failure, the selected bank is restored from the backup.
    """
    if destination is None:
        raise ValueError("an explicit destination bank is required; refusing to choose one")
    slot = _slot(destination)
    if backup is None or set(backup) != set(SLOT_NAMES):
        raise ValueError("complete C1-C7 backup is required before writing")
    requested = dict(settings)
    original = dict(backup[slot])
    try:
        transport.write_custom_slot(slot, requested)
        readback = dict(transport.read_custom_slot(slot))
        if readback != requested:
            raise RuntimeError(f"readback mismatch for {slot}")
        return TransactionResult(slot, original, requested, readback)
    except Exception:
        transport.write_custom_slot(slot, original)
        restored = dict(transport.read_custom_slot(slot))
        if restored != original:
            raise RuntimeError(f"write failed and restoration failed for {slot}")
        raise

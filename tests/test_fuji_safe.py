import pytest

from portra160_lab.fuji_safe import backup_custom_slots, write_with_readback


class FakeFuji:
    def __init__(self):
        self.slots = {f"C{i}": {"value": i} for i in range(1, 8)}

    def read_custom_slot(self, slot):
        return dict(self.slots[slot])

    def write_custom_slot(self, slot, settings):
        self.slots[slot] = dict(settings)


def test_safe_write_requires_explicit_destination_and_full_backup():
    camera = FakeFuji()
    backup = backup_custom_slots(camera)
    with pytest.raises(ValueError, match="explicit destination"):
        write_with_readback(camera, destination=None, settings={"value": 9}, backup=backup)
    with pytest.raises(ValueError, match="complete C1-C7"):
        write_with_readback(camera, destination="C1", settings={"value": 9}, backup={})


def test_safe_write_reads_back_exactly():
    camera = FakeFuji()
    backup = backup_custom_slots(camera)
    result = write_with_readback(camera, destination="C3", settings={"value": 99}, backup=backup)
    assert result.readback == {"value": 99}
    assert camera.slots["C3"] == {"value": 99}


def test_failed_readback_restores_original_slot():
    class Mismatch(FakeFuji):
        def read_custom_slot(self, slot):
            value = super().read_custom_slot(slot)
            if slot == "C2" and value == {"value": 42}:
                return {"value": 43}
            return value

    camera = Mismatch()
    backup = backup_custom_slots(camera)
    with pytest.raises(RuntimeError, match="readback mismatch"):
        write_with_readback(camera, destination="C2", settings={"value": 42}, backup=backup)
    assert camera.slots["C2"] == {"value": 2}

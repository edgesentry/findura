"""Stub interface for Human-in-the-Loop review gate (Phase 2 / S5).

In Phase 1, all columns must be covered by approved deterministic mappings.
ReviewGate will handle unknown columns and schema drift proposals in Phase 2.
"""

from typing import Any


class ReviewGateStub:
    def __init__(self, current_mapping_version: str = "1"):
        self.current_mapping_version = current_mapping_version

    def review_diff(self, yaml_diff: str) -> tuple[bool, str]:
        """Phase 2 stub: returns (approved, new_mapping_version)."""
        return False, self.current_mapping_version

    def list_queue(self) -> list[dict[str, Any]]:
        return []

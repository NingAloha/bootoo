"""Contracts skeleton for API-facing types."""

from typing import Protocol


class ProgressSink(Protocol):
    def __call__(self, phase: str, progress: float) -> None:
        """Consume progress updates from executor steps."""

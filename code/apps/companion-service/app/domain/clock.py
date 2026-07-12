"""Injectable clocks keep timing logic authoritative and testable."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    def __init__(self, current: datetime) -> None:
        self.set(current)

    def now(self) -> datetime:
        return self._current

    def set(self, current: datetime) -> None:
        if current.tzinfo is None:
            raise ValueError("FixedClock requires a timezone-aware datetime.")
        self._current = current.astimezone(UTC)

"""Focus-session lifecycle and timing operations."""

from __future__ import annotations

from datetime import timedelta
from typing import Protocol

from app.domain.clock import Clock
from app.domain.models import FocusSession, FocusSessionStatus, UserSettings


class FocusSessionRepository(Protocol):
    def get_active(self) -> FocusSession | None: ...

    def save(self, session: FocusSession) -> None: ...


class FocusSessionService:
    def __init__(
        self,
        repository: FocusSessionRepository,
        clock: Clock,
        settings: UserSettings,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._settings = settings

    def start(self) -> FocusSession:
        current = self._repository.get_active()
        if current is not None:
            raise ValueError("A focus session is already active.")

        now = self._clock.now()
        session = FocusSession(
            started_at=now,
            initial_nudge_at=now + timedelta(minutes=self._settings.initial_nudge_minutes),
        )
        self._repository.save(session)
        return session

    def stop(self) -> FocusSession:
        session = self._repository.get_active()
        if session is None:
            raise ValueError("No active focus session exists.")

        session.ended_at = self._clock.now()
        session.status = FocusSessionStatus.ENDED
        self._repository.save(session)
        return session

    def elapsed_minutes(self) -> int:
        session = self._repository.get_active()
        if session is None:
            return 0
        return int(session.elapsed(self._clock.now()).total_seconds() // 60)

    def apply_cooldown(self, minutes: int) -> FocusSession:
        if minutes <= 0:
            raise ValueError("Cooldown must be greater than zero.")
        session = self._repository.get_active()
        if session is None:
            raise ValueError("No active focus session exists.")
        session.next_eligible_nudge_at = self._clock.now() + timedelta(minutes=minutes)
        self._repository.save(session)
        return session

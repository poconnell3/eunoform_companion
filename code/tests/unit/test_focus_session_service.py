from datetime import UTC, datetime, timedelta

from app.domain.clock import FixedClock
from app.domain.models import FocusSession, UserSettings
from app.services.focus_session_service import FocusSessionService


class MemoryFocusRepository:
    def __init__(self) -> None:
        self.session: FocusSession | None = None

    def get_active(self) -> FocusSession | None:
        return self.session if self.session and self.session.is_active else None

    def save(self, session: FocusSession) -> None:
        self.session = session


def test_start_records_authoritative_timestamp_and_threshold() -> None:
    now = datetime(2026, 7, 11, 18, 0, tzinfo=UTC)
    repo = MemoryFocusRepository()
    service = FocusSessionService(repo, FixedClock(now), UserSettings(initial_nudge_minutes=45))

    session = service.start()

    assert session.started_at == now
    assert session.initial_nudge_at == now + timedelta(minutes=45)


def test_elapsed_time_comes_from_clock_not_language_model() -> None:
    start = datetime(2026, 7, 11, 18, 0, tzinfo=UTC)
    clock = FixedClock(start)
    repo = MemoryFocusRepository()
    service = FocusSessionService(repo, clock, UserSettings())
    service.start()

    clock.set(start + timedelta(minutes=17, seconds=59))

    assert service.elapsed_minutes() == 17

from datetime import UTC, datetime

from app.domain.models import FocusSession, InteractionIntensity, NudgeEvent, UserSettings
from app.persistence.database import Database
from app.persistence.repositories import (
    SQLiteFocusSessionRepository,
    SQLiteNudgeRepository,
    SQLiteSettingsRepository,
)


def test_settings_session_and_nudge_survive_restart(tmp_path) -> None:
    path = tmp_path / "companion.sqlite3"
    first_db = Database(path)
    first_db.initialize()

    settings = UserSettings(initial_nudge_minutes=38, quiet_default_minutes=75)
    session = FocusSession(started_at=datetime(2026, 7, 11, 18, 0, tzinfo=UTC))
    event = NudgeEvent(
        focus_session_id=session.id,
        created_at=datetime(2026, 7, 11, 18, 45, tzinfo=UTC),
        policy_reason="allowed_wellness_threshold",
        threshold_minutes=38,
        elapsed_minutes=45,
        interaction_intensity=InteractionIntensity.GENTLE,
    )

    SQLiteSettingsRepository(first_db).save(settings)
    SQLiteFocusSessionRepository(first_db).save(session)
    SQLiteNudgeRepository(first_db).save(event)

    # A new Database object represents an application restart.
    restarted_db = Database(path)
    restarted_db.initialize()

    restored_settings = SQLiteSettingsRepository(restarted_db).get()
    restored_session = SQLiteFocusSessionRepository(restarted_db).get(session.id)
    restored_event = SQLiteNudgeRepository(restarted_db).get(event.id)

    assert restored_settings.initial_nudge_minutes == 38
    assert restored_settings.quiet_default_minutes == 75
    assert restored_session is not None and restored_session.started_at == session.started_at
    assert restored_event is not None and restored_event.elapsed_minutes == 45

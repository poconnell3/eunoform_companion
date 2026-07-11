"""SQLite repositories with explicit commits and no hidden persistence claims."""

from __future__ import annotations

from datetime import datetime

from app.domain.models import (
    Deferral,
    FocusSession,
    FocusSessionStatus,
    InteractionIntensity,
    NudgeEvent,
    NudgeOutcome,
    QuietInterval,
    UserSettings,
)
from app.persistence.database import Database


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value is not None else None


class SQLiteSettingsRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, settings: UserSettings) -> None:
        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT INTO settings (
                    singleton_id, initial_nudge_minutes, repeat_nudge_minutes,
                    after_dismiss_cooldown_minutes, after_accept_cooldown_minutes,
                    after_irritation_cooldown_minutes, quiet_default_minutes,
                    interaction_intensity, visual_lead_in_seconds, maximum_nudge_words,
                    wellness_nudges_enabled, muted
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(singleton_id) DO UPDATE SET
                    initial_nudge_minutes=excluded.initial_nudge_minutes,
                    repeat_nudge_minutes=excluded.repeat_nudge_minutes,
                    after_dismiss_cooldown_minutes=excluded.after_dismiss_cooldown_minutes,
                    after_accept_cooldown_minutes=excluded.after_accept_cooldown_minutes,
                    after_irritation_cooldown_minutes=excluded.after_irritation_cooldown_minutes,
                    quiet_default_minutes=excluded.quiet_default_minutes,
                    interaction_intensity=excluded.interaction_intensity,
                    visual_lead_in_seconds=excluded.visual_lead_in_seconds,
                    maximum_nudge_words=excluded.maximum_nudge_words,
                    wellness_nudges_enabled=excluded.wellness_nudges_enabled,
                    muted=excluded.muted
                """,
                (
                    settings.initial_nudge_minutes,
                    settings.repeat_nudge_minutes,
                    settings.after_dismiss_cooldown_minutes,
                    settings.after_accept_cooldown_minutes,
                    settings.after_irritation_cooldown_minutes,
                    settings.quiet_default_minutes,
                    settings.interaction_intensity.value,
                    settings.visual_lead_in_seconds,
                    settings.maximum_nudge_words,
                    int(settings.wellness_nudges_enabled),
                    int(settings.muted),
                ),
            )

    def get(self) -> UserSettings:
        with self._database.connect() as connection:
            row = connection.execute("SELECT * FROM settings WHERE singleton_id = 1").fetchone()
        if row is None:
            return UserSettings()
        return UserSettings(
            initial_nudge_minutes=row["initial_nudge_minutes"],
            repeat_nudge_minutes=row["repeat_nudge_minutes"],
            after_dismiss_cooldown_minutes=row["after_dismiss_cooldown_minutes"],
            after_accept_cooldown_minutes=row["after_accept_cooldown_minutes"],
            after_irritation_cooldown_minutes=row["after_irritation_cooldown_minutes"],
            quiet_default_minutes=row["quiet_default_minutes"],
            interaction_intensity=InteractionIntensity(row["interaction_intensity"]),
            visual_lead_in_seconds=row["visual_lead_in_seconds"],
            maximum_nudge_words=row["maximum_nudge_words"],
            wellness_nudges_enabled=bool(row["wellness_nudges_enabled"]),
            muted=bool(row["muted"]),
        )


class SQLiteFocusSessionRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, session: FocusSession) -> None:
        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT INTO focus_sessions (
                    id, started_at, ended_at, status, initial_nudge_at,
                    last_nudge_at, next_eligible_nudge_at, wellness_nudges_enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    started_at=excluded.started_at,
                    ended_at=excluded.ended_at,
                    status=excluded.status,
                    initial_nudge_at=excluded.initial_nudge_at,
                    last_nudge_at=excluded.last_nudge_at,
                    next_eligible_nudge_at=excluded.next_eligible_nudge_at,
                    wellness_nudges_enabled=excluded.wellness_nudges_enabled
                """,
                (
                    session.id,
                    session.started_at.isoformat(),
                    session.ended_at.isoformat() if session.ended_at else None,
                    session.status.value,
                    session.initial_nudge_at.isoformat() if session.initial_nudge_at else None,
                    session.last_nudge_at.isoformat() if session.last_nudge_at else None,
                    session.next_eligible_nudge_at.isoformat()
                    if session.next_eligible_nudge_at
                    else None,
                    int(session.wellness_nudges_enabled),
                ),
            )

    def get_active(self) -> FocusSession | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM focus_sessions WHERE status = 'active' LIMIT 1"
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def get(self, session_id: str) -> FocusSession | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM focus_sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return self._from_row(row) if row is not None else None

    @staticmethod
    def _from_row(row: object) -> FocusSession:
        return FocusSession(
            id=row["id"],  # type: ignore[index]
            started_at=_dt(row["started_at"]),  # type: ignore[index,arg-type]
            ended_at=_dt(row["ended_at"]),  # type: ignore[index,arg-type]
            status=FocusSessionStatus(row["status"]),  # type: ignore[index]
            initial_nudge_at=_dt(row["initial_nudge_at"]),  # type: ignore[index,arg-type]
            last_nudge_at=_dt(row["last_nudge_at"]),  # type: ignore[index,arg-type]
            next_eligible_nudge_at=_dt(row["next_eligible_nudge_at"]),  # type: ignore[index,arg-type]
            wellness_nudges_enabled=bool(row["wellness_nudges_enabled"]),  # type: ignore[index]
        )


class SQLiteNudgeRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, event: NudgeEvent) -> None:
        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT INTO nudge_events (
                    id, focus_session_id, created_at, policy_reason,
                    threshold_minutes, elapsed_minutes, interaction_intensity,
                    expression_name, gesture_name, outcome
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET outcome=excluded.outcome
                """,
                (
                    event.id,
                    event.focus_session_id,
                    event.created_at.isoformat(),
                    event.policy_reason,
                    event.threshold_minutes,
                    event.elapsed_minutes,
                    event.interaction_intensity.value,
                    event.expression_name,
                    event.gesture_name,
                    event.outcome.value,
                ),
            )

    def get(self, event_id: str) -> NudgeEvent | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM nudge_events WHERE id = ?", (event_id,)
            ).fetchone()
        if row is None:
            return None
        return NudgeEvent(
            id=row["id"],
            focus_session_id=row["focus_session_id"],
            created_at=_dt(row["created_at"]),  # type: ignore[arg-type]
            policy_reason=row["policy_reason"],
            threshold_minutes=row["threshold_minutes"],
            elapsed_minutes=row["elapsed_minutes"],
            interaction_intensity=InteractionIntensity(row["interaction_intensity"]),
            expression_name=row["expression_name"],
            gesture_name=row["gesture_name"],
            outcome=NudgeOutcome(row["outcome"]),
        )


class SQLiteDeferralRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, deferral: Deferral) -> None:
        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT INTO deferrals (
                    id, nudge_event_id, created_at, duration_minutes, expires_at, status
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    duration_minutes=excluded.duration_minutes,
                    expires_at=excluded.expires_at,
                    status=excluded.status
                """,
                (
                    deferral.id,
                    deferral.nudge_event_id,
                    deferral.created_at.isoformat(),
                    deferral.duration_minutes,
                    deferral.expires_at.isoformat(),
                    deferral.status,
                ),
            )

    def get_active(self, now: datetime) -> Deferral | None:
        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM deferrals
                WHERE status = 'active' AND expires_at > ?
                ORDER BY expires_at DESC LIMIT 1
                """,
                (now.isoformat(),),
            ).fetchone()
        if row is None:
            return None
        return Deferral(
            id=row["id"],
            nudge_event_id=row["nudge_event_id"],
            created_at=_dt(row["created_at"]),  # type: ignore[arg-type]
            duration_minutes=row["duration_minutes"],
            expires_at=_dt(row["expires_at"]),  # type: ignore[arg-type]
            status=row["status"],
        )


class SQLiteQuietIntervalRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, interval: QuietInterval) -> None:
        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT INTO quiet_intervals (id, started_at, ends_at, source, status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET ends_at=excluded.ends_at, status=excluded.status
                """,
                (
                    interval.id,
                    interval.started_at.isoformat(),
                    interval.ends_at.isoformat(),
                    interval.source,
                    interval.status,
                ),
            )

    def get_active(self, now: datetime) -> QuietInterval | None:
        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM quiet_intervals
                WHERE status = 'active' AND started_at <= ? AND ends_at > ?
                ORDER BY ends_at DESC LIMIT 1
                """,
                (now.isoformat(), now.isoformat()),
            ).fetchone()
        if row is None:
            return None
        return QuietInterval(
            id=row["id"],
            started_at=_dt(row["started_at"]),  # type: ignore[arg-type]
            ends_at=_dt(row["ends_at"]),  # type: ignore[arg-type]
            source=row["source"],
            status=row["status"],
        )

"""Core domain entities for the Eunoform Companion service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4

from app.domain.interaction_state import InteractionState


def new_id() -> str:
    return str(uuid4())


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Timestamps must be timezone-aware.")
    return value.astimezone(UTC)


class FocusSessionStatus(StrEnum):
    ACTIVE = "active"
    ENDED = "ended"


class InteractionIntensity(StrEnum):
    SUBTLE = "subtle"
    GENTLE = "gentle"
    NOTICEABLE = "noticeable"


class NudgeOutcome(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DEFERRED = "deferred"
    DISMISSED = "dismissed"
    QUIETED = "quieted"
    FREQUENCY_REDUCED = "frequency_reduced"


@dataclass(slots=True)
class UserSettings:
    initial_nudge_minutes: int = 45
    repeat_nudge_minutes: int = 30
    after_dismiss_cooldown_minutes: int = 30
    after_accept_cooldown_minutes: int = 30
    after_irritation_cooldown_minutes: int = 120
    quiet_default_minutes: int = 60
    interaction_intensity: InteractionIntensity = InteractionIntensity.GENTLE
    visual_lead_in_seconds: int = 3
    maximum_nudge_words: int = 20
    wellness_nudges_enabled: bool = True
    muted: bool = False

    def __post_init__(self) -> None:
        positive_fields = {
            "initial_nudge_minutes": self.initial_nudge_minutes,
            "repeat_nudge_minutes": self.repeat_nudge_minutes,
            "after_dismiss_cooldown_minutes": self.after_dismiss_cooldown_minutes,
            "after_accept_cooldown_minutes": self.after_accept_cooldown_minutes,
            "after_irritation_cooldown_minutes": self.after_irritation_cooldown_minutes,
            "quiet_default_minutes": self.quiet_default_minutes,
            "maximum_nudge_words": self.maximum_nudge_words,
        }
        for name, value in positive_fields.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero.")
        if self.visual_lead_in_seconds < 0:
            raise ValueError("visual_lead_in_seconds cannot be negative.")


@dataclass(slots=True)
class FocusSession:
    started_at: datetime
    id: str = field(default_factory=new_id)
    ended_at: datetime | None = None
    status: FocusSessionStatus = FocusSessionStatus.ACTIVE
    initial_nudge_at: datetime | None = None
    last_nudge_at: datetime | None = None
    next_eligible_nudge_at: datetime | None = None
    wellness_nudges_enabled: bool = True

    def __post_init__(self) -> None:
        self.started_at = ensure_utc(self.started_at)
        for name in ("ended_at", "initial_nudge_at", "last_nudge_at", "next_eligible_nudge_at"):
            value = getattr(self, name)
            if value is not None:
                setattr(self, name, ensure_utc(value))

    @property
    def is_active(self) -> bool:
        return self.status is FocusSessionStatus.ACTIVE and self.ended_at is None

    def elapsed(self, now: datetime) -> timedelta:
        end = self.ended_at or ensure_utc(now)
        return max(end - self.started_at, timedelta(0))


@dataclass(slots=True)
class NudgeEvent:
    focus_session_id: str
    created_at: datetime
    policy_reason: str
    threshold_minutes: int
    elapsed_minutes: int
    interaction_intensity: InteractionIntensity
    expression_name: str = "gentle_attention"
    gesture_name: str = "wave_small"
    outcome: NudgeOutcome = NudgeOutcome.PENDING
    id: str = field(default_factory=new_id)

    def __post_init__(self) -> None:
        self.created_at = ensure_utc(self.created_at)


@dataclass(slots=True)
class Deferral:
    nudge_event_id: str
    created_at: datetime
    duration_minutes: int
    expires_at: datetime
    status: str = "active"
    id: str = field(default_factory=new_id)

    def __post_init__(self) -> None:
        self.created_at = ensure_utc(self.created_at)
        self.expires_at = ensure_utc(self.expires_at)
        if self.duration_minutes <= 0:
            raise ValueError("Deferral duration must be greater than zero.")
        if self.expires_at <= self.created_at:
            raise ValueError("Deferral expiration must be after creation time.")

    def is_active_at(self, now: datetime) -> bool:
        return self.status == "active" and ensure_utc(now) < self.expires_at


@dataclass(slots=True)
class QuietInterval:
    started_at: datetime
    ends_at: datetime
    source: str = "user"
    status: str = "active"
    id: str = field(default_factory=new_id)

    def __post_init__(self) -> None:
        self.started_at = ensure_utc(self.started_at)
        self.ends_at = ensure_utc(self.ends_at)
        if self.ends_at <= self.started_at:
            raise ValueError("Quiet interval must end after it begins.")

    def is_active_at(self, now: datetime) -> bool:
        moment = ensure_utc(now)
        return self.status == "active" and self.started_at <= moment < self.ends_at


@dataclass(frozen=True, slots=True)
class ExplanationFacts:
    focus_started_at: datetime
    elapsed_minutes: int
    threshold_minutes: int
    last_nudge_at: datetime | None
    suggestion_kind: str = "general_wellness"


@dataclass(slots=True)
class CompanionState:
    interaction_state: InteractionState = InteractionState.IDLE
    active_focus_session: FocusSession | None = None
    active_deferral: Deferral | None = None
    active_quiet_interval: QuietInterval | None = None
    current_nudge: NudgeEvent | None = None

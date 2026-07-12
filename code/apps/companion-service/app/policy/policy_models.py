"""Inputs and outputs for the deterministic Humane Policy Engine."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from app.domain.interaction_state import InteractionState
from app.domain.models import Deferral, FocusSession, QuietInterval, UserSettings

class PolicyReason(StrEnum):
    ALLOWED_EXPLICIT_REMINDER = "allowed_explicit_reminder"
    ALLOWED_WELLNESS_THRESHOLD = "allowed_wellness_threshold"
    BLOCKED_MUTED = "blocked_muted"
    BLOCKED_QUIET_MODE = "blocked_quiet_mode"
    BLOCKED_USER_CANCELLATION = "blocked_user_cancellation"
    BLOCKED_ACTIVE_DEFERRAL = "blocked_active_deferral"
    BLOCKED_INTERACTION_LOCK = "blocked_interaction_lock"
    BLOCKED_COOLDOWN = "blocked_cooldown"
    BLOCKED_NO_ACTIVE_SESSION = "blocked_no_active_session"
    BLOCKED_NUDGES_DISABLED = "blocked_nudges_disabled"
    BLOCKED_THRESHOLD_NOT_REACHED = "blocked_threshold_not_reached"

@dataclass(frozen=True, slots=True)
class PolicyContext:
    now: datetime
    settings: UserSettings
    interaction_state: InteractionState
    focus_session: FocusSession | None = None
    active_deferral: Deferral | None = None
    active_quiet_interval: QuietInterval | None = None
    explicit_reminder_due: bool = False
    user_cancelled: bool = False

@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: PolicyReason
    elapsed_minutes: int = 0
    threshold_minutes: int = 0
    next_eligible_at: datetime | None = None
    @classmethod
    def allow(cls, reason: PolicyReason, *, elapsed_minutes: int, threshold_minutes: int) -> "PolicyDecision":
        return cls(True, reason, elapsed_minutes, threshold_minutes)
    @classmethod
    def block(cls, reason: PolicyReason, *, elapsed_minutes: int = 0, threshold_minutes: int = 0, next_eligible_at: datetime | None = None) -> "PolicyDecision":
        return cls(False, reason, elapsed_minutes, threshold_minutes, next_eligible_at)

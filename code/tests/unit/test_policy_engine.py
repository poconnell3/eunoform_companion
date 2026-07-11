from datetime import UTC, datetime, timedelta

from app.domain.interaction_state import InteractionState
from app.domain.models import Deferral, FocusSession, QuietInterval, UserSettings
from app.policy.humane_policy_engine import HumanePolicyEngine
from app.policy.policy_models import PolicyContext, PolicyReason

NOW = datetime(2026, 7, 11, 18, 0, tzinfo=UTC)


def session_started(minutes_ago: int) -> FocusSession:
    return FocusSession(started_at=NOW - timedelta(minutes=minutes_ago))


def evaluate(**changes: object):
    values = {
        "now": NOW,
        "settings": UserSettings(),
        "interaction_state": InteractionState.FOCUSING,
        "focus_session": session_started(45),
    }
    values.update(changes)
    return HumanePolicyEngine().evaluate(PolicyContext(**values))


def test_threshold_allows_wellness_nudge() -> None:
    decision = evaluate()
    assert decision.allowed is True
    assert decision.reason is PolicyReason.ALLOWED_WELLNESS_THRESHOLD
    assert decision.elapsed_minutes == 45


def test_nudge_is_blocked_before_threshold() -> None:
    decision = evaluate(focus_session=session_started(44))
    assert decision.allowed is False
    assert decision.reason is PolicyReason.BLOCKED_THRESHOLD_NOT_REACHED
    assert decision.next_eligible_at == NOW + timedelta(minutes=1)


def test_mute_has_highest_precedence() -> None:
    settings = UserSettings(muted=True)
    quiet = QuietInterval(started_at=NOW - timedelta(minutes=5), ends_at=NOW + timedelta(hours=1))
    decision = evaluate(settings=settings, active_quiet_interval=quiet)
    assert decision.reason is PolicyReason.BLOCKED_MUTED


def test_quiet_mode_blocks_visual_and_text_nudge() -> None:
    quiet = QuietInterval(started_at=NOW - timedelta(minutes=5), ends_at=NOW + timedelta(hours=1))
    decision = evaluate(active_quiet_interval=quiet)
    assert decision.reason is PolicyReason.BLOCKED_QUIET_MODE
    assert decision.next_eligible_at == quiet.ends_at


def test_active_deferral_blocks_equivalent_nudge() -> None:
    deferral = Deferral(
        nudge_event_id="nudge-1",
        created_at=NOW - timedelta(minutes=2),
        duration_minutes=10,
        expires_at=NOW + timedelta(minutes=8),
    )
    decision = evaluate(active_deferral=deferral)
    assert decision.reason is PolicyReason.BLOCKED_ACTIVE_DEFERRAL
    assert decision.next_eligible_at == deferral.expires_at


def test_cooldown_blocks_explicit_reminder_due() -> None:
    session = session_started(90)
    session.next_eligible_nudge_at = NOW + timedelta(minutes=15)
    decision = evaluate(focus_session=session, explicit_reminder_due=True)
    assert decision.reason is PolicyReason.BLOCKED_COOLDOWN


def test_explicit_reminder_is_allowed_after_user_controls_clear() -> None:
    decision = evaluate(focus_session=session_started(5), explicit_reminder_due=True)
    assert decision.allowed is True
    assert decision.reason is PolicyReason.ALLOWED_EXPLICIT_REMINDER


def test_disabling_wellness_nudges_does_not_cancel_explicit_reminder() -> None:
    settings = UserSettings(wellness_nudges_enabled=False)
    decision = evaluate(settings=settings, explicit_reminder_due=True)
    assert decision.allowed is True
    assert decision.reason is PolicyReason.ALLOWED_EXPLICIT_REMINDER


def test_awaiting_response_prevents_duplicate_nudge() -> None:
    decision = evaluate(interaction_state=InteractionState.AWAITING_RESPONSE)
    assert decision.reason is PolicyReason.BLOCKED_INTERACTION_LOCK


def test_no_active_session_blocks_nudge() -> None:
    decision = evaluate(focus_session=None)
    assert decision.reason is PolicyReason.BLOCKED_NO_ACTIVE_SESSION

from datetime import UTC, datetime, timedelta

from app.domain.interaction_state import InteractionState
from app.domain.models import Deferral, ExplanationFacts, FocusSession, QuietInterval, UserSettings
from app.policy.humane_policy_engine import HumanePolicyEngine
from app.policy.policy_models import PolicyContext, PolicyReason
from app.services.explanation_service import ExplanationService

NOW = datetime(2026, 7, 11, 18, 0, tzinfo=UTC)


def test_not_now_deferral_is_respected_for_full_duration() -> None:
    session = FocusSession(started_at=NOW - timedelta(minutes=60))
    deferral = Deferral(
        nudge_event_id="nudge-1",
        created_at=NOW,
        duration_minutes=10,
        expires_at=NOW + timedelta(minutes=10),
    )
    engine = HumanePolicyEngine()

    during = engine.evaluate(
        PolicyContext(
            now=NOW + timedelta(minutes=9, seconds=59),
            settings=UserSettings(),
            interaction_state=InteractionState.DEFERRED,
            focus_session=session,
            active_deferral=deferral,
        )
    )
    after = engine.evaluate(
        PolicyContext(
            now=NOW + timedelta(minutes=10),
            settings=UserSettings(),
            interaction_state=InteractionState.FOCUSING,
            focus_session=session,
            active_deferral=deferral,
        )
    )

    assert during.reason is PolicyReason.BLOCKED_ACTIVE_DEFERRAL
    assert after.allowed is True


def test_quiet_mode_cannot_be_bypassed_by_threshold() -> None:
    session = FocusSession(started_at=NOW - timedelta(hours=4))
    quiet = QuietInterval(started_at=NOW, ends_at=NOW + timedelta(hours=1))

    decision = HumanePolicyEngine().evaluate(
        PolicyContext(
            now=NOW + timedelta(minutes=30),
            settings=UserSettings(),
            interaction_state=InteractionState.FOCUSING,
            focus_session=session,
            active_quiet_interval=quiet,
        )
    )

    assert decision.allowed is False
    assert decision.reason is PolicyReason.BLOCKED_QUIET_MODE


def test_explanation_uses_only_authoritative_facts() -> None:
    message = ExplanationService.format(
        ExplanationFacts(
            focus_started_at=NOW - timedelta(minutes=52),
            elapsed_minutes=52,
            threshold_minutes=45,
            last_nudge_at=None,
        )
    )

    assert message == (
        "You started this focus session 52 minutes ago, "
        "and your break-check interval is 45 minutes."
    )
    forbidden_claims = ("posture", "tired", "emotion", "concentration", "fatigue")
    assert all(word not in message.lower() for word in forbidden_claims)

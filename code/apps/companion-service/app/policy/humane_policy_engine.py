"""Deterministic policy authority for nudges and reminders."""

from __future__ import annotations

from datetime import UTC, timedelta

from app.domain.interaction_state import InteractionState
from app.policy.policy_models import PolicyContext, PolicyDecision, PolicyReason


_LOCKED_STATES = {
    InteractionState.POLICY_EVALUATION,
    InteractionState.ATTRACTING_ATTENTION,
    InteractionState.AWAITING_RESPONSE,
    InteractionState.EXPLAINING,
}


class HumanePolicyEngine:
    """Apply user-control precedence before threshold or reminder logic.

    The engine returns facts and reason codes. It never phrases a nudge and never
    performs an action itself.
    """

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        now = context.now.astimezone(UTC)
        session = context.focus_session
        threshold = context.settings.initial_nudge_minutes
        elapsed = 0
        if session is not None:
            elapsed = int(session.elapsed(now).total_seconds() // 60)

        # Highest-priority user controls.
        if context.settings.muted:
            return PolicyDecision.block(PolicyReason.BLOCKED_MUTED)

        if (
            context.active_quiet_interval is not None
            and context.active_quiet_interval.is_active_at(now)
        ):
            return PolicyDecision.block(
                PolicyReason.BLOCKED_QUIET_MODE,
                next_eligible_at=context.active_quiet_interval.ends_at,
            )

        if context.user_cancelled:
            return PolicyDecision.block(PolicyReason.BLOCKED_USER_CANCELLATION)

        if context.active_deferral is not None and context.active_deferral.is_active_at(now):
            return PolicyDecision.block(
                PolicyReason.BLOCKED_ACTIVE_DEFERRAL,
                next_eligible_at=context.active_deferral.expires_at,
            )

        if context.interaction_state in _LOCKED_STATES:
            return PolicyDecision.block(PolicyReason.BLOCKED_INTERACTION_LOCK)

        if session is not None and session.next_eligible_nudge_at is not None:
            if now < session.next_eligible_nudge_at:
                return PolicyDecision.block(
                    PolicyReason.BLOCKED_COOLDOWN,
                    elapsed_minutes=elapsed,
                    threshold_minutes=threshold,
                    next_eligible_at=session.next_eligible_nudge_at,
                )

        # Lower-priority eligibility checks.
        if session is None or not session.is_active:
            return PolicyDecision.block(PolicyReason.BLOCKED_NO_ACTIVE_SESSION)

        # An explicit reminder is still subject to mute, quiet, cancellation,
        # deferral, interaction locks, and cooldowns above, but it is distinct
        # from optional general-wellness suggestions.
        if context.explicit_reminder_due:
            return PolicyDecision.allow(
                PolicyReason.ALLOWED_EXPLICIT_REMINDER,
                elapsed_minutes=elapsed,
                threshold_minutes=threshold,
            )

        if not context.settings.wellness_nudges_enabled or not session.wellness_nudges_enabled:
            return PolicyDecision.block(
                PolicyReason.BLOCKED_NUDGES_DISABLED,
                elapsed_minutes=elapsed,
                threshold_minutes=threshold,
            )

        if elapsed < threshold:
            return PolicyDecision.block(
                PolicyReason.BLOCKED_THRESHOLD_NOT_REACHED,
                elapsed_minutes=elapsed,
                threshold_minutes=threshold,
                next_eligible_at=session.started_at
                + context.settings.initial_nudge_minutes * _ONE_MINUTE,
            )

        return PolicyDecision.allow(
            PolicyReason.ALLOWED_WELLNESS_THRESHOLD,
            elapsed_minutes=elapsed,
            threshold_minutes=threshold,
        )


_ONE_MINUTE = timedelta(minutes=1)

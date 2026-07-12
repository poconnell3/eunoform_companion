"""Application orchestration for the local API; policy remains deterministic."""

from __future__ import annotations

from dataclasses import asdict
from datetime import timedelta

from app.domain.clock import Clock
from app.domain.interaction_state import (
    InteractionCommand,
    InteractionState,
    InteractionStateMachine,
)
from app.domain.models import (
    Deferral,
    ExplanationFacts,
    NudgeEvent,
    NudgeOutcome,
    QuietInterval,
    UserSettings,
)
from app.persistence.repositories import (
    SQLiteDeferralRepository,
    SQLiteFocusSessionRepository,
    SQLiteNudgeRepository,
    SQLiteQuietIntervalRepository,
    SQLiteSettingsRepository,
)
from app.policy.humane_policy_engine import HumanePolicyEngine
from app.policy.policy_models import PolicyContext
from app.services.explanation_service import ExplanationService
from app.services.focus_session_service import FocusSessionService


class CompanionApplicationService:
    def __init__(
        self,
        *,
        clock: Clock,
        settings_repo: SQLiteSettingsRepository,
        focus_repo: SQLiteFocusSessionRepository,
        nudge_repo: SQLiteNudgeRepository,
        deferral_repo: SQLiteDeferralRepository,
        quiet_repo: SQLiteQuietIntervalRepository,
    ):
        self.clock = clock
        self.settings_repo = settings_repo
        self.focus_repo = focus_repo
        self.nudge_repo = nudge_repo
        self.deferral_repo = deferral_repo
        self.quiet_repo = quiet_repo
        self.settings = settings_repo.get()
        active = focus_repo.get_active()
        now = clock.now()
        active_quiet = quiet_repo.get_active(now)
        active_deferral = deferral_repo.get_active(now)
        if active is None:
            initial = InteractionState.IDLE
        elif active_quiet is not None:
            initial = InteractionState.QUIET
        elif active_deferral is not None:
            initial = InteractionState.DEFERRED
        else:
            initial = InteractionState.FOCUSING
        self.machine = InteractionStateMachine(initial)
        self.current_nudge = None
        self.policy = HumanePolicyEngine()

    def _focus_service(self):
        return FocusSessionService(self.focus_repo, self.clock, self.settings)

    def start_focus(self):
        s = self._focus_service().start()
        self.machine.transition(InteractionCommand.START_FOCUS)
        return s

    def stop_focus(self):
        if self.current_nudge is not None and self.current_nudge.outcome is NudgeOutcome.PENDING:
            self.current_nudge.outcome = NudgeOutcome.SESSION_ENDED
            self.nudge_repo.save(self.current_nudge)
        s = self._focus_service().stop()
        self.machine.transition(InteractionCommand.STOP_FOCUS)
        self.current_nudge = None
        return s

    def resume_focus(self):
        self.machine.transition(InteractionCommand.RESUME_FOCUS)
        return self.status()

    def evaluate(self, explicit_reminder_due=False):
        self.reconcile_timed_state()
        if self.machine.state is InteractionState.DEFERRED:
            d = self.deferral_repo.get_active(self.clock.now())
            if d is not None:
                raise ValueError("The active deferral has not expired.")
            self.machine.transition(InteractionCommand.DEFERRAL_EXPIRES)
        elif self.machine.state is InteractionState.FOCUSING:
            self.machine.transition(InteractionCommand.THRESHOLD_REACHED)
        else:
            raise ValueError(
                f"Policy evaluation is unavailable while in state {self.machine.state.value!r}."
            )
        now = self.clock.now()
        session = self.focus_repo.get_active()
        decision = self.policy.evaluate(
            PolicyContext(
                now=now,
                settings=self.settings,
                interaction_state=InteractionState.FOCUSING,
                focus_session=session,
                active_deferral=self.deferral_repo.get_active(now),
                active_quiet_interval=self.quiet_repo.get_active(now),
                explicit_reminder_due=explicit_reminder_due,
            )
        )
        if not decision.allowed:
            self.machine.transition(InteractionCommand.POLICY_BLOCKS)
            return decision
        self.machine.transition(InteractionCommand.POLICY_ALLOWS)
        assert session is not None
        event = NudgeEvent(
            focus_session_id=session.id,
            created_at=now,
            policy_reason=decision.reason.value,
            threshold_minutes=decision.threshold_minutes,
            elapsed_minutes=decision.elapsed_minutes,
            interaction_intensity=self.settings.interaction_intensity,
        )
        self.nudge_repo.save(event)
        session.last_nudge_at = now
        self.focus_repo.save(session)
        self.current_nudge = event
        return decision

    def attention_complete(self):
        self.machine.transition(InteractionCommand.VISUAL_CUE_COMPLETE)
        return self.status()

    def _require_nudge(self):
        if self.current_nudge is None:
            raise ValueError("No current nudge exists.")
        return self.current_nudge

    def accept(self):
        e = self._require_nudge()
        self.machine.require_transition(InteractionCommand.ACCEPT)
        e.outcome = NudgeOutcome.ACCEPTED
        self.nudge_repo.save(e)
        self._focus_service().apply_cooldown(self.settings.after_accept_cooldown_minutes)
        self.machine.transition(InteractionCommand.ACCEPT)
        return self.status()

    def defer(self, minutes: int):
        e = self._require_nudge()
        self.machine.require_transition(InteractionCommand.DEFER)
        now = self.clock.now()
        d = Deferral(
            nudge_event_id=e.id,
            created_at=now,
            duration_minutes=minutes,
            expires_at=now + timedelta(minutes=minutes),
        )
        self.deferral_repo.save(d)
        e.outcome = NudgeOutcome.DEFERRED
        self.nudge_repo.save(e)
        self.machine.transition(InteractionCommand.DEFER)
        return d

    def dismiss(self):
        e = self._require_nudge()
        self.machine.require_transition(InteractionCommand.DISMISS)
        e.outcome = NudgeOutcome.DISMISSED
        self.nudge_repo.save(e)
        self._focus_service().apply_cooldown(self.settings.after_dismiss_cooldown_minutes)
        self.machine.transition(InteractionCommand.DISMISS)
        return self.status()

    def quiet(self, minutes: int):
        self.machine.require_transition(InteractionCommand.ENTER_QUIET)
        now = self.clock.now()
        q = QuietInterval(started_at=now, ends_at=now + timedelta(minutes=minutes))
        self.quiet_repo.save(q)
        if self.current_nudge:
            self.current_nudge.outcome = NudgeOutcome.QUIETED
            self.nudge_repo.save(self.current_nudge)
        self.machine.transition(InteractionCommand.ENTER_QUIET)
        return q

    def exit_quiet(self):
        self.machine.require_transition(InteractionCommand.EXIT_QUIET)
        self.quiet_repo.end_active(self.clock.now())
        self.machine.transition(InteractionCommand.EXIT_QUIET)
        return self.status()

    def reduce_frequency(self, additional_minutes: int):
        e = self._require_nudge()
        self.machine.require_transition(InteractionCommand.REDUCE_FREQUENCY)
        self.settings.repeat_nudge_minutes += additional_minutes
        self.settings_repo.save(self.settings)
        e.outcome = NudgeOutcome.FREQUENCY_REDUCED
        self.nudge_repo.save(e)
        self.machine.transition(InteractionCommand.REDUCE_FREQUENCY)
        return self.settings

    def explanation(self):
        e = self._require_nudge()
        session = self.focus_repo.get(e.focus_session_id)
        if session is None:
            raise ValueError("The focus session for this nudge no longer exists.")
        was_awaiting = self.machine.state is InteractionState.AWAITING_RESPONSE
        if was_awaiting:
            self.machine.transition(InteractionCommand.ASK_WHY)
        facts = ExplanationFacts(
            session.started_at,
            e.elapsed_minutes,
            e.threshold_minutes,
            session.last_nudge_at,
            "explicit_reminder" if "explicit" in e.policy_reason else "general_wellness",
        )
        text = ExplanationService.format(facts)
        if was_awaiting:
            self.machine.transition(InteractionCommand.EXPLANATION_COMPLETE)
        return facts, text

    def patch_settings(self, changes: dict):
        data = asdict(self.settings)
        data.update({k: v for k, v in changes.items() if v is not None})
        self.settings = UserSettings(**data)
        self.settings_repo.save(self.settings)
        return self.settings

    def reconcile_timed_state(self):
        if self.machine.state is not InteractionState.QUIET:
            return
        now = self.clock.now()
        if self.quiet_repo.get_active(now) is not None:
            return
        self.machine.transition(InteractionCommand.EXIT_QUIET)
        if self.focus_repo.get_active() is None and self.machine.state is not InteractionState.IDLE:
            self.machine.transition(InteractionCommand.STOP_FOCUS)

    def status(self):
        self.reconcile_timed_state()
        now = self.clock.now()
        session = self.focus_repo.get_active()
        return {
            "interaction_state": self.machine.state,
            "focus_session": session,
            "elapsed_minutes": 0
            if session is None
            else int(session.elapsed(now).total_seconds() // 60),
            "active_deferral": self.deferral_repo.get_active(now),
            "active_quiet_interval": self.quiet_repo.get_active(now),
            "current_nudge": self.current_nudge,
            "settings": self.settings,
        }

    def events(self, limit=100):
        return self.nudge_repo.list_recent(limit)

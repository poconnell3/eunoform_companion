"""Interaction states and deterministic state transitions."""

from __future__ import annotations

from enum import StrEnum


class InteractionState(StrEnum):
    IDLE = "idle"
    FOCUSING = "focusing"
    POLICY_EVALUATION = "policy_evaluation"
    ATTRACTING_ATTENTION = "attracting_attention"
    AWAITING_RESPONSE = "awaiting_response"
    EXPLAINING = "explaining"
    DEFERRED = "deferred"
    ON_BREAK = "on_break"
    QUIET = "quiet"


class InteractionCommand(StrEnum):
    START_FOCUS = "start_focus"
    STOP_FOCUS = "stop_focus"
    THRESHOLD_REACHED = "threshold_reached"
    POLICY_ALLOWS = "policy_allows"
    POLICY_BLOCKS = "policy_blocks"
    VISUAL_CUE_COMPLETE = "visual_cue_complete"
    ACCEPT = "accept"
    DEFER = "defer"
    DISMISS = "dismiss"
    ASK_WHY = "ask_why"
    EXPLANATION_COMPLETE = "explanation_complete"
    REDUCE_FREQUENCY = "reduce_frequency"
    ENTER_QUIET = "enter_quiet"
    EXIT_QUIET = "exit_quiet"
    DEFERRAL_EXPIRES = "deferral_expires"
    RESUME_FOCUS = "resume_focus"
    CANCEL = "cancel"


class InvalidTransitionError(ValueError):
    """Raised when a command is invalid for the current state."""


_TRANSITIONS: dict[tuple[InteractionState, InteractionCommand], InteractionState] = {
    (InteractionState.IDLE, InteractionCommand.START_FOCUS): InteractionState.FOCUSING,
    (
        InteractionState.FOCUSING,
        InteractionCommand.THRESHOLD_REACHED,
    ): InteractionState.POLICY_EVALUATION,
    (InteractionState.FOCUSING, InteractionCommand.STOP_FOCUS): InteractionState.IDLE,
    (InteractionState.POLICY_EVALUATION, InteractionCommand.STOP_FOCUS): InteractionState.IDLE,
    (InteractionState.ATTRACTING_ATTENTION, InteractionCommand.STOP_FOCUS): InteractionState.IDLE,
    (InteractionState.AWAITING_RESPONSE, InteractionCommand.STOP_FOCUS): InteractionState.IDLE,
    (InteractionState.EXPLAINING, InteractionCommand.STOP_FOCUS): InteractionState.IDLE,
    (InteractionState.QUIET, InteractionCommand.STOP_FOCUS): InteractionState.IDLE,
    (InteractionState.FOCUSING, InteractionCommand.ENTER_QUIET): InteractionState.QUIET,
    (
        InteractionState.POLICY_EVALUATION,
        InteractionCommand.POLICY_ALLOWS,
    ): InteractionState.ATTRACTING_ATTENTION,
    (
        InteractionState.POLICY_EVALUATION,
        InteractionCommand.POLICY_BLOCKS,
    ): InteractionState.FOCUSING,
    (
        InteractionState.ATTRACTING_ATTENTION,
        InteractionCommand.VISUAL_CUE_COMPLETE,
    ): InteractionState.AWAITING_RESPONSE,
    (InteractionState.ATTRACTING_ATTENTION, InteractionCommand.CANCEL): InteractionState.FOCUSING,
    (InteractionState.ATTRACTING_ATTENTION, InteractionCommand.ENTER_QUIET): InteractionState.QUIET,
    (InteractionState.AWAITING_RESPONSE, InteractionCommand.ACCEPT): InteractionState.ON_BREAK,
    (InteractionState.AWAITING_RESPONSE, InteractionCommand.DEFER): InteractionState.DEFERRED,
    (InteractionState.AWAITING_RESPONSE, InteractionCommand.DISMISS): InteractionState.FOCUSING,
    (InteractionState.AWAITING_RESPONSE, InteractionCommand.ASK_WHY): InteractionState.EXPLAINING,
    (
        InteractionState.AWAITING_RESPONSE,
        InteractionCommand.REDUCE_FREQUENCY,
    ): InteractionState.FOCUSING,
    (InteractionState.AWAITING_RESPONSE, InteractionCommand.ENTER_QUIET): InteractionState.QUIET,
    (
        InteractionState.EXPLAINING,
        InteractionCommand.EXPLANATION_COMPLETE,
    ): InteractionState.AWAITING_RESPONSE,
    (
        InteractionState.DEFERRED,
        InteractionCommand.DEFERRAL_EXPIRES,
    ): InteractionState.POLICY_EVALUATION,
    (InteractionState.DEFERRED, InteractionCommand.STOP_FOCUS): InteractionState.IDLE,
    (InteractionState.DEFERRED, InteractionCommand.ENTER_QUIET): InteractionState.QUIET,
    (InteractionState.ON_BREAK, InteractionCommand.RESUME_FOCUS): InteractionState.FOCUSING,
    (InteractionState.ON_BREAK, InteractionCommand.STOP_FOCUS): InteractionState.IDLE,
}


class InteractionStateMachine:
    """Small explicit state machine; no UI may bypass this transition table."""

    def __init__(self, initial_state: InteractionState = InteractionState.IDLE) -> None:
        self._state = initial_state
        self._state_before_quiet = (
            InteractionState.FOCUSING
            if initial_state is InteractionState.QUIET
            else InteractionState.IDLE
        )

    @property
    def state(self) -> InteractionState:
        return self._state

    def can_transition(self, command: InteractionCommand) -> bool:
        if self._state is InteractionState.QUIET and command is InteractionCommand.EXIT_QUIET:
            return True
        return (self._state, command) in _TRANSITIONS

    def require_transition(self, command: InteractionCommand) -> None:
        if not self.can_transition(command):
            raise InvalidTransitionError(
                f"Command {command.value!r} is invalid while in state {self._state.value!r}."
            )

    def transition(self, command: InteractionCommand) -> InteractionState:
        self.require_transition(command)
        if command is InteractionCommand.ENTER_QUIET and self._state is not InteractionState.QUIET:
            self._state_before_quiet = self._safe_quiet_return_state(self._state)
        if self._state is InteractionState.QUIET and command is InteractionCommand.EXIT_QUIET:
            self._state = self._state_before_quiet
            return self._state
        self._state = _TRANSITIONS[(self._state, command)]
        return self._state

    @staticmethod
    def _safe_quiet_return_state(state: InteractionState) -> InteractionState:
        if state in {
            InteractionState.FOCUSING,
            InteractionState.DEFERRED,
            InteractionState.ON_BREAK,
        }:
            return state
        if state is InteractionState.IDLE:
            return InteractionState.IDLE
        return InteractionState.FOCUSING

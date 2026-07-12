import pytest
from app.domain.interaction_state import (
    InteractionCommand,
    InteractionState,
    InteractionStateMachine,
    InvalidTransitionError,
)


def test_complete_acceptance_path() -> None:
    machine = InteractionStateMachine()

    assert machine.transition(InteractionCommand.START_FOCUS) is InteractionState.FOCUSING
    assert (
        machine.transition(InteractionCommand.THRESHOLD_REACHED)
        is InteractionState.POLICY_EVALUATION
    )
    assert (
        machine.transition(InteractionCommand.POLICY_ALLOWS)
        is InteractionState.ATTRACTING_ATTENTION
    )
    assert (
        machine.transition(InteractionCommand.VISUAL_CUE_COMPLETE)
        is InteractionState.AWAITING_RESPONSE
    )
    assert machine.transition(InteractionCommand.ACCEPT) is InteractionState.ON_BREAK
    assert machine.transition(InteractionCommand.RESUME_FOCUS) is InteractionState.FOCUSING


def test_invalid_transition_leaves_state_unchanged() -> None:
    machine = InteractionStateMachine()

    with pytest.raises(InvalidTransitionError):
        machine.transition(InteractionCommand.ACCEPT)

    assert machine.state is InteractionState.IDLE


def test_quiet_mode_returns_to_safe_previous_state() -> None:
    machine = InteractionStateMachine(InteractionState.FOCUSING)

    assert machine.transition(InteractionCommand.ENTER_QUIET) is InteractionState.QUIET
    assert machine.transition(InteractionCommand.EXIT_QUIET) is InteractionState.FOCUSING


def test_quiet_entered_from_deferred_returns_to_deferred() -> None:
    machine = InteractionStateMachine(InteractionState.DEFERRED)

    assert machine.transition(InteractionCommand.ENTER_QUIET) is InteractionState.QUIET
    assert machine.transition(InteractionCommand.EXIT_QUIET) is InteractionState.DEFERRED

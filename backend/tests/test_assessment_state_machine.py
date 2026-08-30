import pytest

from app.clinical_engine.state_machine import (
    AssessmentState,
    AssessmentStateMachine,
    AssessmentTransitionError,
)


def test_every_valid_workflow_transition() -> None:
    machine = AssessmentStateMachine()
    assert machine.transition(AssessmentState.ANALYZED, "PHYSICIAN") is AssessmentState.ANALYZED
    assert (
        machine.transition(AssessmentState.PENDING_PHARMACIST_REVIEW, "PHYSICIAN")
        is AssessmentState.PENDING_PHARMACIST_REVIEW
    )
    assert (
        machine.transition(AssessmentState.IN_PHARMACIST_REVIEW, "CLINICAL_PHARMACIST")
        is AssessmentState.IN_PHARMACIST_REVIEW
    )
    assert (
        machine.transition(AssessmentState.PHARMACIST_RECOMMENDED, "CLINICAL_PHARMACIST")
        is AssessmentState.PHARMACIST_RECOMMENDED
    )
    assert (
        machine.transition(AssessmentState.RETURNED_TO_PHYSICIAN, "CLINICAL_PHARMACIST")
        is AssessmentState.RETURNED_TO_PHYSICIAN
    )
    assert machine.transition(AssessmentState.FINALIZED, "PHYSICIAN") is AssessmentState.FINALIZED


def test_direct_finalization_and_cancellation_policy() -> None:
    machine = AssessmentStateMachine()
    machine.transition(AssessmentState.ANALYZED, "PHYSICIAN")
    with pytest.raises(AssessmentTransitionError):
        machine.transition(AssessmentState.FINALIZED, "PHYSICIAN", pharmacist_review_requested=True)

    direct = AssessmentStateMachine()
    direct.transition(AssessmentState.ANALYZED, "PHYSICIAN")
    assert direct.transition(AssessmentState.FINALIZED, "PHYSICIAN") is AssessmentState.FINALIZED

    cancelled = AssessmentStateMachine()
    assert (
        cancelled.transition(AssessmentState.CANCELLED, "HOSPITAL_ADMIN")
        is AssessmentState.CANCELLED
    )


def test_invalid_transitions_and_role_restrictions_are_rejected() -> None:
    invalid = [
        (AssessmentState.DRAFT, AssessmentState.FINALIZED, "PHYSICIAN"),
        (AssessmentState.DRAFT, AssessmentState.IN_PHARMACIST_REVIEW, "CLINICAL_PHARMACIST"),
        (AssessmentState.ANALYZED, AssessmentState.IN_PHARMACIST_REVIEW, "PHYSICIAN"),
        (
            AssessmentState.PENDING_PHARMACIST_REVIEW,
            AssessmentState.IN_PHARMACIST_REVIEW,
            "PHYSICIAN",
        ),
        (AssessmentState.IN_PHARMACIST_REVIEW, AssessmentState.FINALIZED, "CLINICAL_PHARMACIST"),
        (AssessmentState.RETURNED_TO_PHYSICIAN, AssessmentState.FINALIZED, "CLINICAL_PHARMACIST"),
        (AssessmentState.DRAFT, AssessmentState.CANCELLED, "CLINICAL_PHARMACIST"),
    ]
    for current, target, role in invalid:
        machine = AssessmentStateMachine(current)
        assert not machine.can_transition(target, role)
        with pytest.raises(AssessmentTransitionError):
            machine.transition(target, role)

    after_recommendation = AssessmentStateMachine(AssessmentState.PHARMACIST_RECOMMENDED)
    assert (
        after_recommendation.transition(AssessmentState.FINALIZED, "PHYSICIAN")
        is AssessmentState.FINALIZED
    )


@pytest.mark.parametrize("terminal", [AssessmentState.FINALIZED, AssessmentState.CANCELLED])
def test_terminal_states_reject_all_mutations(terminal: AssessmentState) -> None:
    machine = AssessmentStateMachine(terminal)
    assert machine.allowed_transitions("PHYSICIAN") == ()
    with pytest.raises(AssessmentTransitionError):
        machine.transition(AssessmentState.DRAFT, "PHYSICIAN")

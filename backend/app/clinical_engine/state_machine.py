"""Assessment workflow state machine and role policy."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class AssessmentState(StrEnum):
    DRAFT = "DRAFT"
    ANALYZED = "ANALYZED"
    PENDING_PHARMACIST_REVIEW = "PENDING_PHARMACIST_REVIEW"
    IN_PHARMACIST_REVIEW = "IN_PHARMACIST_REVIEW"
    PHARMACIST_RECOMMENDED = "PHARMACIST_RECOMMENDED"
    RETURNED_TO_PHYSICIAN = "RETURNED_TO_PHYSICIAN"
    FINALIZED = "FINALIZED"
    CANCELLED = "CANCELLED"


class AssessmentTransitionError(ValueError):
    """Raised when a workflow transition violates the assessment policy."""


PHYSICIAN_ROLES = {"PHYSICIAN", "HOSPITAL_ADMIN", "PLATFORM_ADMIN"}
PHARMACIST_ROLES = {"CLINICAL_PHARMACIST", "HOSPITAL_ADMIN", "PLATFORM_ADMIN"}


@dataclass
class AssessmentStateMachine:
    """Enforce legal transitions and role ownership for an assessment.

    Policy:
    - Physicians create/analyze assessments and may request pharmacist review.
    - Pharmacists claim reviews and submit recommendations.
    - A pharmacist recommendation returns the assessment to a physician.
    - A physician may finalize an analyzed assessment directly when review is not requested.
    - Administrators may perform either professional transition for operational recovery.
    - Any non-terminal assessment may be cancelled by a physician or administrator.
    - FINALIZED and CANCELLED are terminal states.
    """

    state: AssessmentState = AssessmentState.DRAFT

    def can_transition(
        self,
        target: AssessmentState | str,
        actor_role: Any,
        *,
        pharmacist_review_requested: bool = False,
    ) -> bool:
        try:
            self._validate(target, actor_role, pharmacist_review_requested)
        except AssessmentTransitionError:
            return False
        return True

    def transition(
        self,
        target: AssessmentState | str,
        actor_role: Any,
        *,
        pharmacist_review_requested: bool = False,
    ) -> AssessmentState:
        target = _state(target)
        self._validate(target, actor_role, pharmacist_review_requested)
        self.state = target
        return self.state

    def allowed_transitions(self, actor_role: Any) -> tuple[AssessmentState, ...]:
        return tuple(
            target for target in AssessmentState if self.can_transition(target, actor_role)
        )

    def _validate(
        self,
        target: AssessmentState | str,
        actor_role: Any,
        pharmacist_review_requested: bool,
    ) -> None:
        target = _state(target)
        role = _role(actor_role)
        if self.state in {AssessmentState.FINALIZED, AssessmentState.CANCELLED}:
            raise AssessmentTransitionError(f"{self.state} is terminal")
        if target is AssessmentState.CANCELLED:
            if role not in PHYSICIAN_ROLES:
                raise AssessmentTransitionError("Only a physician or administrator may cancel")
            return
        allowed_roles = {
            (AssessmentState.DRAFT, AssessmentState.ANALYZED): PHYSICIAN_ROLES,
            (AssessmentState.ANALYZED, AssessmentState.PENDING_PHARMACIST_REVIEW): PHYSICIAN_ROLES,
            (
                AssessmentState.PENDING_PHARMACIST_REVIEW,
                AssessmentState.IN_PHARMACIST_REVIEW,
            ): PHARMACIST_ROLES,
            (
                AssessmentState.IN_PHARMACIST_REVIEW,
                AssessmentState.PHARMACIST_RECOMMENDED,
            ): PHARMACIST_ROLES,
            (
                AssessmentState.PHARMACIST_RECOMMENDED,
                AssessmentState.RETURNED_TO_PHYSICIAN,
            ): PHARMACIST_ROLES,
            (AssessmentState.PHARMACIST_RECOMMENDED, AssessmentState.FINALIZED): PHYSICIAN_ROLES,
            (AssessmentState.RETURNED_TO_PHYSICIAN, AssessmentState.FINALIZED): PHYSICIAN_ROLES,
            (AssessmentState.ANALYZED, AssessmentState.FINALIZED): PHYSICIAN_ROLES,
        }.get((self.state, target))
        if allowed_roles is None:
            raise AssessmentTransitionError(f"Invalid transition: {self.state} -> {target}")
        if role not in allowed_roles:
            raise AssessmentTransitionError(f"Role {role} cannot perform {self.state} -> {target}")
        if (
            self.state is AssessmentState.ANALYZED
            and target is AssessmentState.FINALIZED
            and pharmacist_review_requested
        ):
            raise AssessmentTransitionError("This assessment requires pharmacist review")


def _state(value: AssessmentState | str) -> AssessmentState:
    try:
        return value if isinstance(value, AssessmentState) else AssessmentState(str(value))
    except ValueError as exc:
        raise AssessmentTransitionError(f"Unknown assessment state: {value}") from exc


def _role(value: Any) -> str:
    raw = getattr(value, "value", value)
    return str(raw)


__all__ = ["AssessmentState", "AssessmentStateMachine", "AssessmentTransitionError"]

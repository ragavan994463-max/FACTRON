"""Controlled improvement proposal engine for FACTRON."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable
from uuid import UUID, uuid4

from .evaluator import Evaluation, EvaluationStatus
from .experience import Experience


class ImprovementStatus(str, Enum):
    """Improvement proposal lifecycle."""

    PROPOSED = "proposed"
    VALIDATED = "validated"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ImprovementProposal:
    """Immutable and auditable improvement proposal.

    The proposal describes a possible improvement. It does not execute
    code, alter system configuration, or claim successful learning.
    """

    proposal_id: UUID = field(default_factory=uuid4)
    experience_id: str = ""
    status: ImprovementStatus = (
        ImprovementStatus.PROPOSED
    )
    priority: float = 0.0
    target: str = ""
    reason: str = ""
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.proposal_id, UUID):
            raise TypeError(
                "proposal_id must be a UUID"
            )

        if not self.experience_id.strip():
            raise ValueError(
                "experience_id cannot be empty"
            )

        if not self.target.strip():
            raise ValueError(
                "target cannot be empty"
            )

        if not 0.0 <= self.priority <= 1.0:
            raise ValueError(
                "priority must be between 0 and 1"
            )

        if not isinstance(
            self.status,
            ImprovementStatus,
        ):
            raise TypeError(
                "status must be an ImprovementStatus"
            )

        object.__setattr__(
            self,
            "evidence",
            tuple(self.evidence),
        )


class ImprovementEngine:
    """Generate controlled proposals from evaluation evidence."""

    def __init__(
        self,
        minimum_priority: float = 0.35,
    ) -> None:
        if not 0.0 <= minimum_priority <= 1.0:
            raise ValueError(
                "minimum_priority must be between 0 and 1"
            )

        self._minimum_priority = (
            float(minimum_priority)
        )

    @property
    def minimum_priority(self) -> float:
        """Return configured proposal threshold."""

        return self._minimum_priority

    def propose(
        self,
        experience: Experience,
        evaluation: Evaluation,
    ) -> ImprovementProposal | None:
        """Generate a proposal when weaknesses are measurable."""

        if not isinstance(experience, Experience):
            raise TypeError(
                "experience must be an Experience"
            )

        if not isinstance(evaluation, Evaluation):
            raise TypeError(
                "evaluation must be an Evaluation"
            )

        if (
            str(experience.experience_id)
            != evaluation.experience_id
        ):
            raise ValueError(
                "experience and evaluation IDs do not match"
            )

        weaknesses = tuple(
            evaluation.weaknesses
        )

        if not weaknesses:
            return None

        priority = max(
            self._minimum_priority,
            min(
                1.0,
                1.0 - evaluation.overall_score,
            ),
        )

        if evaluation.status is EvaluationStatus.REJECTED:
            priority = max(
                priority,
                0.75,
            )

        if "task_success" in weaknesses:
            target = "decision_and_execution_strategy"
        elif "reward_quality" in weaknesses:
            target = "outcome_optimization"
        elif "execution_efficiency" in weaknesses:
            target = "execution_efficiency"
        else:
            target = "general_reasoning_quality"

        return ImprovementProposal(
            experience_id=evaluation.experience_id,
            status=ImprovementStatus.PROPOSED,
            priority=priority,
            target=target,
            reason=(
                "Measured evaluation weaknesses justify a "
                "controlled improvement cycle."
            ),
            evidence=weaknesses,
        )

    def propose_batch(
        self,
        pairs: Iterable[
            tuple[Experience, Evaluation]
        ],
    ) -> tuple[ImprovementProposal, ...]:
        """Generate proposals for multiple evaluations."""

        proposals: list[ImprovementProposal] = []

        for experience, evaluation in pairs:
            proposal = self.propose(
                experience,
                evaluation,
            )

            if proposal is not None:
                proposals.append(proposal)

        return tuple(proposals)

    @staticmethod
    def validate(
        proposal: ImprovementProposal,
    ) -> ImprovementProposal:
        """Mark a structurally valid proposal as validated.

        This validates the proposal contract only. It does not establish
        that applying the proposal will improve FACTRON.
        """

        if not isinstance(
            proposal,
            ImprovementProposal,
        ):
            raise TypeError(
                "proposal must be an ImprovementProposal"
            )

        return ImprovementProposal(
            proposal_id=proposal.proposal_id,
            experience_id=proposal.experience_id,
            status=ImprovementStatus.VALIDATED,
            priority=proposal.priority,
            target=proposal.target,
            reason=proposal.reason,
            evidence=proposal.evidence,
        )

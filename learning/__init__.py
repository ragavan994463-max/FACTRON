"""FACTRON Omega learning subsystem.

The learning subsystem transforms execution experiences into measurable
evaluations and controlled improvement proposals.

Pipeline:

    Experience
        |
        v
    Evaluation
        |
        v
    Learning Signal
        |
        v
    Improvement Proposal
        |
        v
    Validation Boundary

This layer is deliberately provider-independent and dependency-free.
It does not execute generated code, mutate system policy, retrain models,
or fabricate model output.
"""

from .experience import (
    Experience,
    ExperienceOutcome,
    ExperienceStore,
)
from .evaluator import (
    Evaluation,
    EvaluationDimension,
    EvaluationStatus,
    LearningEvaluator,
)
from .improvement import (
    ImprovementEngine,
    ImprovementProposal,
    ImprovementStatus,
)

__all__ = [
    "Experience",
    "ExperienceOutcome",
    "ExperienceStore",
    "Evaluation",
    "EvaluationDimension",
    "EvaluationStatus",
    "LearningEvaluator",
    "ImprovementEngine",
    "ImprovementProposal",
    "ImprovementStatus",
]

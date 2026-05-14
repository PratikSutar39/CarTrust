"""Phase 3: Trust scoring engine. Pure Python, deterministic."""

from typing import List, Tuple

from cartrust.constants import DIMENSION_WEIGHTS
from cartrust.reasoning.schemas import DimensionAssessment


def compute_trust_score(
    assessments: List[DimensionAssessment],
) -> Tuple[float, bool, str]:
    """
    Deterministic scoring. Same inputs always produce same outputs.

    Returns (composite_score, has_hard_stop, confidence_level).
    """
    has_hard_stop = any(a.state == "critical" for a in assessments)
    coverage = compute_coverage(assessments)

    if has_hard_stop:
        return 0.0, True, "high"

    weighted_sum = 0.0
    weight_sum = 0.0
    for assessment in assessments:
        weight = DIMENSION_WEIGHTS.get(assessment.dimension, 0.10)
        if assessment.state != "unverifiable":
            weighted_sum += assessment.score * weight
            weight_sum += weight

    raw_score = weighted_sum / weight_sum if weight_sum > 0 else 0.0
    composite = round(max(0.0, min(1.0, raw_score * coverage)), 2)

    if coverage >= 0.8:
        confidence = "high"
    elif coverage >= 0.5:
        confidence = "moderate"
    else:
        confidence = "low"

    return composite, False, confidence


def compute_coverage(assessments: List[DimensionAssessment]) -> float:
    total = len(assessments)
    verifiable = sum(1 for a in assessments if a.state != "unverifiable")
    return verifiable / total if total > 0 else 0.0

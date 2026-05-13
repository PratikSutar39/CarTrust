"""Phase 3: Verdict and action checklist generator. Pure Python, deterministic."""

from typing import List

from cartrust.reasoning.schemas import Contradiction, DimensionAssessment


def determine_verdict(
    composite_score: float,
    has_hard_stop: bool,
    assessments: List[DimensionAssessment],
) -> str:
    """Deterministic verdict from trust score and assessment states."""

    if has_hard_stop:
        return "WALK_AWAY"

    has_resolvable = any(a.state == "active_resolvable" for a in assessments)
    if has_resolvable:
        return "NEGOTIATE_WITH_SAFEGUARDS"

    if composite_score >= 0.80:
        return "BUY"
    if composite_score >= 0.50:
        return "NEGOTIATE"
    return "WALK_AWAY"


def generate_action_checklist(
    assessments: List[DimensionAssessment],
    contradictions: List[Contradiction],
) -> List[str]:
    """Generate deduplicated action checklist ordered by severity."""

    actions = []
    for severity in ("critical", "high", "medium", "low"):
        for assessment in assessments:
            for flag in assessment.flags:
                if flag.severity == severity:
                    actions.extend(flag.suggested_actions)

    for c in contradictions:
        if c.severity in ("critical", "high"):
            actions.append(f"Investigate: {c.evidence_summary[:150]}")

    # Deduplicate preserving order
    seen = set()
    unique = []
    for action in actions:
        key = action.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(action)

    return unique

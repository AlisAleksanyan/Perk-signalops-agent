from __future__ import annotations

from signalops.framework import AgentStep, RunContext
from signalops.models import EnrichedAccount, FitScore, ResearchBrief


class ScoringStep(AgentStep[tuple[EnrichedAccount, ResearchBrief], FitScore]):
    name = "scoring"

    def run(self, value: tuple[EnrichedAccount, ResearchBrief], context: RunContext) -> FitScore:
        account, research = value
        score = 0
        matches: list[str] = []
        gaps: list[str] = []

        employee_count = account.employee_count or 0
        if employee_count >= 1000:
            score += 25
            matches.append("enterprise or upper-midmarket headcount")
        elif employee_count >= 200:
            score += 18
            matches.append("midmarket headcount")
        elif employee_count >= 50:
            score += 8
            gaps.append("smaller account, likely lower urgency")
        else:
            gaps.append("headcount is missing or below target")

        signal_blob = " ".join(research.recent_signals + research.likely_pains).lower()
        unclear_fit = "unclear fit" in signal_blob or "weak or conflicting" in signal_blob
        if not unclear_fit and (
            "cross-border" in signal_blob or "international" in signal_blob or "distributed" in signal_blob
        ):
            score += 25
            matches.append("international travel or distributed workforce signal")
        if not unclear_fit and ("expense" in signal_blob or "invoice" in signal_blob or "spend" in signal_blob):
            score += 20
            matches.append("finance, expense, invoice, or spend-management pain")
        if not unclear_fit and ("event" in signal_blob or "offsite" in signal_blob):
            score += 12
            matches.append("events or group travel pain")
        if not unclear_fit and ("growth" in signal_blob or "hiring" in signal_blob):
            score += 10
            matches.append("growth or hiring signal")

        if account.data_quality_notes:
            score -= 8
            gaps.append("data quality issues: " + ", ".join(account.data_quality_notes))

        score = max(0, min(100, score))
        primary_pain = research.likely_pains[0] if research.likely_pains else "unclear"
        confidence = round(min(research.confidence, 0.95 if not account.data_quality_notes else 0.72), 2)
        return FitScore(
            score=score,
            confidence=confidence,
            icp_matches=matches,
            icp_gaps=gaps,
            primary_pain=primary_pain,
            rationale=(
                f"Score {score}/100 based on headcount, signal strength, Perk-relevant pains, "
                f"and data quality. Primary pain: {primary_pain}."
            ),
        )

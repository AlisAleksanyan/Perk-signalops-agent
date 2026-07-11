from __future__ import annotations

from signalops.framework import AgentStep, RunContext
from signalops.models import EnrichedAccount, FitScore, ResearchBrief, RouteDecision, RouteResult


class RoutingStep(AgentStep[tuple[EnrichedAccount, ResearchBrief, FitScore], RouteResult]):
    name = "routing"

    def __init__(self, auto_threshold: int = 70, reject_threshold: int = 35, confidence_threshold: float = 0.72):
        self.auto_threshold = auto_threshold
        self.reject_threshold = reject_threshold
        self.confidence_threshold = confidence_threshold

    def run(self, value: tuple[EnrichedAccount, ResearchBrief, FitScore], context: RunContext) -> RouteResult:
        account, research, score = value
        segment = self._segment(account.employee_count)
        region = self._region(account.country)
        sales_motion = self._sales_motion(score.primary_pain)

        if score.confidence < self.confidence_threshold:
            decision = RouteDecision.HUMAN_REVIEW
            reason = f"confidence {score.confidence} below threshold {self.confidence_threshold}"
        elif score.score >= self.auto_threshold:
            decision = RouteDecision.AUTO_QUALIFY
            reason = ""
        elif score.score < self.reject_threshold:
            decision = RouteDecision.REJECT
            reason = "fit score below reject threshold"
        else:
            decision = RouteDecision.HUMAN_REVIEW
            reason = "medium-fit account needs human judgment"

        owner_queue = f"{region}_{segment}_{sales_motion}".lower().replace(" ", "_")
        persona = research.buyer_personas[0] if research.buyer_personas else "Operations Lead"
        return RouteResult(
            decision=decision,
            segment=segment,
            region=region,
            sales_motion=sales_motion,
            owner_queue=owner_queue,
            next_best_action=self._next_action(decision, persona, score.primary_pain),
            human_review_reason=reason,
        )

    def _segment(self, employee_count: int | None) -> str:
        if not employee_count:
            return "unknown_segment"
        if employee_count >= 1000:
            return "enterprise"
        if employee_count >= 200:
            return "mid_market"
        return "smb"

    def _region(self, country: str) -> str:
        normalized = country.lower()
        if any(term in normalized for term in ("united states", "usa", "us")):
            return "us"
        if any(term in normalized for term in ("united kingdom", "uk")):
            return "uk"
        if normalized:
            return "emea"
        return "unknown_region"

    def _sales_motion(self, primary_pain: str) -> str:
        pain = primary_pain.lower()
        if "unclear fit" in pain:
            return "general_outbound"
        if "event" in pain or "offsite" in pain:
            return "events_led"
        if "travel" in pain or "cross-border" in pain:
            return "travel_led"
        if "expense" in pain or "invoice" in pain or "spend" in pain:
            return "finance_led"
        return "general_outbound"

    def _next_action(self, decision: RouteDecision, persona: str, pain: str) -> str:
        if decision == RouteDecision.AUTO_QUALIFY:
            return f"Create Salesforce task: enrich {persona} contacts and draft outreach around {pain}."
        if decision == RouteDecision.HUMAN_REVIEW:
            return f"Send to RevOps review queue before CRM writeback; verify {persona} and pain hypothesis."
        return "Reject from active outbound; keep in nurture if future stronger signals appear."

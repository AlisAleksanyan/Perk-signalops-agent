from __future__ import annotations

from dataclasses import asdict

from signalops.framework import AgentStep, RunContext
from signalops.llm import LLMProvider
from signalops.models import EnrichedAccount, ResearchBrief


class ResearchStep(AgentStep[EnrichedAccount, ResearchBrief]):
    name = "research"

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def run(self, value: EnrichedAccount, context: RunContext) -> ResearchBrief:
        response = self.llm.structured_research(asdict(value))
        return ResearchBrief(
            company_summary=response["company_summary"],
            recent_signals=list(response["recent_signals"]),
            likely_pains=list(response["likely_pains"]),
            buyer_personas=list(response["buyer_personas"]),
            evidence=list(response["evidence"]),
            confidence=float(response["confidence"]),
        )

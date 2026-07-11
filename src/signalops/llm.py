from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class LLMProvider(ABC):
    @abstractmethod
    def structured_research(self, account: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class ReplayLLMProvider(LLMProvider):
    def __init__(self, replay_path: Path):
        self.replay_path = replay_path
        with replay_path.open("r", encoding="utf-8") as handle:
            self.responses = json.load(handle)

    def structured_research(self, account: dict[str, Any]) -> dict[str, Any]:
        domain = account["domain"].lower()
        response = self.responses.get(domain)
        if response:
            return response
        return HeuristicLLMProvider().structured_research(account)


class HeuristicLLMProvider(LLMProvider):
    """Deterministic stand-in for an LLM during local demos and tests."""

    def structured_research(self, account: dict[str, Any]) -> dict[str, Any]:
        signal = account.get("signal_text", "").lower()
        company = account.get("company_name", "The company")
        pains: list[str] = []
        personas: list[str] = []
        signals: list[str] = []

        weak_negative_signal = any(
            phrase in signal
            for phrase in (
                "no clear travel",
                "no clear",
                "unclear growth",
                "limited current evidence",
            )
        )
        if weak_negative_signal:
            return {
                "company_summary": (
                    f"{company} has insufficient evidence of urgent travel, expense, invoice, "
                    "or spend-management pain for automated qualification."
                ),
                "recent_signals": ["weak or conflicting signal"],
                "likely_pains": ["unclear fit for travel and spend automation"],
                "buyer_personas": ["Operations Lead"],
                "evidence": [account.get("signal_text", "")[:280] or "No signal text provided."],
                "confidence": 0.63,
            }

        if any(term in signal for term in ("international", "global", "office", "expansion", "us expansion")):
            pains.append("travel policy and cross-border spend control")
            personas.extend(["CFO", "Head of Finance Operations", "Travel Manager"])
            signals.append("international expansion or distributed operations")
        if any(term in signal for term in ("expense", "invoice", "finance transformation", "procurement", "spend")):
            pains.append("expense, invoice, and spend visibility")
            personas.extend(["CFO", "Finance Director", "Procurement Lead"])
            signals.append("finance operations complexity")
        if any(term in signal for term in ("offsite", "event", "summit", "kickoff")):
            pains.append("event and group travel coordination")
            personas.extend(["People Operations Lead", "Workplace Lead", "Travel Manager"])
            signals.append("company events or offsites")
        if any(term in signal for term in ("hiring", "headcount", "growth", "funding", "series")):
            pains.append("scaling admin workload")
            personas.extend(["COO", "Revenue Operations", "Finance Operations"])
            signals.append("growth or hiring signal")

        if not pains:
            pains.append("unclear fit for travel and spend automation")
            signals.append("weak or generic signal")
            personas.append("Operations Lead")

        unique_personas = list(dict.fromkeys(personas))
        confidence = 0.82 if len(signals) >= 2 else 0.58
        return {
            "company_summary": (
                f"{company} appears to be a B2B account requiring qualification against Perk's "
                "travel, expense, invoice, and spend-management ICP."
            ),
            "recent_signals": signals,
            "likely_pains": list(dict.fromkeys(pains)),
            "buyer_personas": unique_personas,
            "evidence": [account.get("signal_text", "")[:280] or "No signal text provided."],
            "confidence": confidence,
        }

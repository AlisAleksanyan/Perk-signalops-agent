from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RouteDecision(str, Enum):
    AUTO_QUALIFY = "auto_qualify"
    HUMAN_REVIEW = "human_review"
    REJECT = "reject"


@dataclass
class LeadInput:
    company_name: str
    domain: str
    country: str = ""
    employee_count: int | None = None
    source: str = "csv"
    raw_signal: str = ""


@dataclass
class EnrichedAccount:
    company_name: str
    domain: str
    country: str
    employee_count: int | None
    industry: str
    headquarters: str
    signal_text: str
    source_urls: list[str] = field(default_factory=list)
    data_quality_notes: list[str] = field(default_factory=list)


@dataclass
class ResearchBrief:
    company_summary: str
    recent_signals: list[str]
    likely_pains: list[str]
    buyer_personas: list[str]
    evidence: list[str]
    confidence: float


@dataclass
class FitScore:
    score: int
    confidence: float
    icp_matches: list[str]
    icp_gaps: list[str]
    primary_pain: str
    rationale: str


@dataclass
class RouteResult:
    decision: RouteDecision
    segment: str
    region: str
    sales_motion: str
    owner_queue: str
    next_best_action: str
    human_review_reason: str


@dataclass
class CRMRecord:
    account_id: str
    company_name: str
    domain: str
    perk_fit_score: int
    confidence: float
    primary_pain: str
    route_decision: str
    segment: str
    region: str
    sales_motion: str
    owner_queue: str
    next_best_action: str
    human_review_reason: str
    research_summary: str
    updated_at: str = field(default_factory=utc_now)


@dataclass
class AgentRun:
    run_id: str
    lead: LeadInput
    enriched: EnrichedAccount | None = None
    research: ResearchBrief | None = None
    score: FitScore | None = None
    route: RouteResult | None = None
    crm_record: CRMRecord | None = None
    errors: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=utc_now)
    finished_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

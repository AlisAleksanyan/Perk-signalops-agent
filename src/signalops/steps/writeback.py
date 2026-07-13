from __future__ import annotations

import hashlib
from pathlib import Path

from signalops.framework import AgentStep, RunContext
from signalops.models import CRMRecord, EnrichedAccount, FitScore, ResearchBrief, RouteResult
from signalops.storage import AccountStore, make_account_store


class CRMWriter(AgentStep[tuple[EnrichedAccount, ResearchBrief, FitScore, RouteResult], CRMRecord]):
    name = "crm_writeback"

    def __init__(self, db_path: Path, database_url: str | None = None):
        self.store: AccountStore = make_account_store(db_path, database_url)

    def run(self, value: tuple[EnrichedAccount, ResearchBrief, FitScore, RouteResult], context: RunContext) -> CRMRecord:
        account, research, score, route = value
        record = CRMRecord(
            account_id=self._account_id(account.domain or account.company_name),
            company_name=account.company_name,
            domain=account.domain,
            perk_fit_score=score.score,
            confidence=score.confidence,
            primary_pain=score.primary_pain,
            route_decision=route.decision.value,
            segment=route.segment,
            region=route.region,
            sales_motion=route.sales_motion,
            owner_queue=route.owner_queue,
            next_best_action=route.next_best_action,
            human_review_reason=route.human_review_reason,
            research_summary=research.company_summary,
        )
        self.store.upsert_account(record)
        return record

    def _account_id(self, key: str) -> str:
        return "acct_" + hashlib.sha1(key.lower().encode("utf-8")).hexdigest()[:12]


SQLiteCRMWriter = CRMWriter

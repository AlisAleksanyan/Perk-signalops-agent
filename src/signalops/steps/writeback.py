from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from signalops.framework import AgentStep, RunContext
from signalops.models import CRMRecord, EnrichedAccount, FitScore, ResearchBrief, RouteResult


class SQLiteCRMWriter(AgentStep[tuple[EnrichedAccount, ResearchBrief, FitScore, RouteResult], CRMRecord]):
    name = "crm_writeback"

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

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
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                insert into accounts (
                    account_id, company_name, domain, perk_fit_score, confidence,
                    primary_pain, route_decision, segment, region, sales_motion,
                    owner_queue, next_best_action, human_review_reason,
                    research_summary, updated_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(account_id) do update set
                    company_name=excluded.company_name,
                    domain=excluded.domain,
                    perk_fit_score=excluded.perk_fit_score,
                    confidence=excluded.confidence,
                    primary_pain=excluded.primary_pain,
                    route_decision=excluded.route_decision,
                    segment=excluded.segment,
                    region=excluded.region,
                    sales_motion=excluded.sales_motion,
                    owner_queue=excluded.owner_queue,
                    next_best_action=excluded.next_best_action,
                    human_review_reason=excluded.human_review_reason,
                    research_summary=excluded.research_summary,
                    updated_at=excluded.updated_at
                """,
                (
                    record.account_id,
                    record.company_name,
                    record.domain,
                    record.perk_fit_score,
                    record.confidence,
                    record.primary_pain,
                    record.route_decision,
                    record.segment,
                    record.region,
                    record.sales_motion,
                    record.owner_queue,
                    record.next_best_action,
                    record.human_review_reason,
                    record.research_summary,
                    record.updated_at,
                ),
            )
        return record

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                create table if not exists accounts (
                    account_id text primary key,
                    company_name text not null,
                    domain text not null,
                    perk_fit_score integer not null,
                    confidence real not null,
                    primary_pain text not null,
                    route_decision text not null,
                    segment text not null,
                    region text not null,
                    sales_motion text not null,
                    owner_queue text not null,
                    next_best_action text not null,
                    human_review_reason text not null,
                    research_summary text not null,
                    updated_at text not null
                )
                """
            )

    def _account_id(self, key: str) -> str:
        return "acct_" + hashlib.sha1(key.lower().encode("utf-8")).hexdigest()[:12]

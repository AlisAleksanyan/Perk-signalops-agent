from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from signalops.models import CRMRecord


ACCOUNT_COLUMNS = [
    "account_id",
    "company_name",
    "domain",
    "perk_fit_score",
    "confidence",
    "primary_pain",
    "route_decision",
    "segment",
    "region",
    "sales_motion",
    "owner_queue",
    "next_best_action",
    "human_review_reason",
    "research_summary",
    "updated_at",
]


CREATE_TABLE_SQL = """
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


class AccountStore:
    def list_accounts(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def list_domains(self) -> set[str]:
        raise NotImplementedError

    def upsert_account(self, record: CRMRecord) -> None:
        raise NotImplementedError

    def update_review_decision(self, account_id: str, *, decision: str, reason: str, next_action: str) -> None:
        raise NotImplementedError

    def delete_account(self, account_id: str) -> None:
        raise NotImplementedError


class SQLiteAccountStore(AccountStore):
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def list_accounts(self) -> list[dict[str, Any]]:
        if not self.db_path.exists():
            return []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"""
                select {", ".join(ACCOUNT_COLUMNS)}
                from accounts
                order by updated_at desc
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def list_domains(self) -> set[str]:
        if not self.db_path.exists():
            return set()
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("select lower(domain) from accounts").fetchall()
        return {row[0] for row in rows}

    def upsert_account(self, record: CRMRecord) -> None:
        values = record_values(record)
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
                values,
            )

    def update_review_decision(self, account_id: str, *, decision: str, reason: str, next_action: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                update accounts
                set route_decision = ?,
                    human_review_reason = ?,
                    next_best_action = ?,
                    updated_at = datetime('now')
                where account_id = ?
                """,
                (decision, reason, next_action, account_id),
            )

    def delete_account(self, account_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("delete from accounts where account_id = ?", (account_id,))

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(CREATE_TABLE_SQL)


class PostgresAccountStore(AccountStore):
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._init_db()

    def list_accounts(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                select {", ".join(ACCOUNT_COLUMNS)}
                from accounts
                order by updated_at desc
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def list_domains(self) -> set[str]:
        with self._connect() as conn:
            rows = conn.execute("select lower(domain) as domain from accounts").fetchall()
        return {row["domain"] for row in rows}

    def upsert_account(self, record: CRMRecord) -> None:
        values = record_values(record)
        with self._connect() as conn:
            conn.execute(
                """
                insert into accounts (
                    account_id, company_name, domain, perk_fit_score, confidence,
                    primary_pain, route_decision, segment, region, sales_motion,
                    owner_queue, next_best_action, human_review_reason,
                    research_summary, updated_at
                )
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                values,
            )

    def update_review_decision(self, account_id: str, *, decision: str, reason: str, next_action: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                update accounts
                set route_decision = %s,
                    human_review_reason = %s,
                    next_best_action = %s,
                    updated_at = now()
                where account_id = %s
                """,
                (decision, reason, next_action, account_id),
            )

    def delete_account(self, account_id: str) -> None:
        with self._connect() as conn:
            conn.execute("delete from accounts where account_id = %s", (account_id,))

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(CREATE_TABLE_SQL)

    def _connect(self):
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(self.database_url, row_factory=dict_row)


def make_account_store(db_path: Path | None = None, database_url: str | None = None) -> AccountStore:
    url = database_url or os.environ.get("DATABASE_URL")
    if url:
        return PostgresAccountStore(url)
    if db_path is None:
        raise ValueError("db_path is required when DATABASE_URL is not set")
    return SQLiteAccountStore(db_path)


def record_values(record: CRMRecord) -> tuple[Any, ...]:
    return tuple(getattr(record, column) for column in ACCOUNT_COLUMNS)

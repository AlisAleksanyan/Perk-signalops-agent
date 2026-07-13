from __future__ import annotations

import csv
import uuid
from pathlib import Path
from typing import Callable

from .framework import JsonlLogger, RunContext
from .llm import LLMProvider
from .models import AgentRun, LeadInput, utc_now
from .steps.enrichment import EnrichmentStep
from .steps.research import ResearchStep
from .steps.routing import RoutingStep
from .steps.scoring import ScoringStep
from .steps.writeback import CRMWriter


class AccountQualificationPipeline:
    def __init__(self, *, llm: LLMProvider, db_path: Path, log_path: Path):
        self.logger = JsonlLogger(log_path)
        self.enrichment = EnrichmentStep()
        self.research = ResearchStep(llm)
        self.scoring = ScoringStep()
        self.routing = RoutingStep()
        self.writeback = CRMWriter(db_path)

    def run_one(self, lead: LeadInput, writeback_filter: Callable[[AgentRun], bool] | None = None) -> AgentRun:
        run = AgentRun(run_id=str(uuid.uuid4()), lead=lead)
        context = RunContext(run.run_id, self.logger)
        context.log("pipeline", "started", {"lead": lead})
        try:
            run.enriched = self.enrichment(lead, context)
            run.research = self.research(run.enriched, context)
            run.score = self.scoring((run.enriched, run.research), context)
            run.route = self.routing((run.enriched, run.research, run.score), context)
            if writeback_filter is None or writeback_filter(run):
                run.crm_record = self.writeback((run.enriched, run.research, run.score, run.route), context)
            else:
                context.log(
                    "crm_writeback",
                    "skipped",
                    {
                        "company_name": lead.company_name,
                        "domain": lead.domain,
                        "score": run.score.score,
                        "confidence": run.score.confidence,
                        "decision": run.route.decision.value,
                    },
                )
        except Exception as exc:
            run.errors.append(str(exc))
            context.log("pipeline", "failed", {"error": str(exc)})
        finally:
            run.finished_at = utc_now()
            context.log("pipeline", "finished", {"run": run})
        return run


def load_leads_csv(path: Path) -> list[LeadInput]:
    with path.open("r", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        return [
            LeadInput(
                company_name=row["company_name"].strip(),
                domain=row["domain"].strip(),
                country=row.get("country", "").strip(),
                employee_count=_int_or_none(row.get("employee_count", "")),
                source=row.get("source", "csv").strip() or "csv",
                raw_signal=row.get("raw_signal", "").strip(),
            )
            for row in rows
        ]


def _int_or_none(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None

from __future__ import annotations

import argparse
import json
from pathlib import Path

from signalops.framework import to_jsonable
from signalops.llm import ReplayLLMProvider
from signalops.pipeline import AccountQualificationPipeline, load_leads_csv


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Perk SignalOps account qualification pipeline.")
    parser.add_argument("--input", default=str(ROOT / "data" / "sample_leads.csv"))
    parser.add_argument("--db", default=str(ROOT / "data" / "signalops_crm.sqlite"))
    parser.add_argument("--logs", default=str(ROOT / "data" / "agent_runs.jsonl"))
    parser.add_argument("--replay", default=str(ROOT / "data" / "replay_llm_responses.json"))
    args = parser.parse_args()

    pipeline = AccountQualificationPipeline(
        llm=ReplayLLMProvider(Path(args.replay)),
        db_path=Path(args.db),
        log_path=Path(args.logs),
    )
    runs = [pipeline.run_one(lead) for lead in load_leads_csv(Path(args.input))]
    print(json.dumps([to_jsonable(run) for run in runs], indent=2))


if __name__ == "__main__":
    main()

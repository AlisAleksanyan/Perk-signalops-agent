import unittest
import tempfile
from pathlib import Path

from signalops.llm import ReplayLLMProvider
from signalops.models import LeadInput, RouteDecision
from signalops.pipeline import AccountQualificationPipeline


class PipelineTests(unittest.TestCase):
    def test_pipeline_replays_llm_and_writes_crm_record(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            pipeline = AccountQualificationPipeline(
                llm=ReplayLLMProvider(Path("data/replay_llm_responses.json")),
                db_path=tmp_path / "crm.sqlite",
                log_path=tmp_path / "runs.jsonl",
            )

            run = pipeline.run_one(
                LeadInput(
                    company_name="Mistral AI",
                    domain="mistral.ai",
                    country="France",
                    employee_count=1200,
                    raw_signal="Hiring finance operations and workplace roles while expanding internationally.",
                )
            )

            self.assertFalse(run.errors)
            self.assertIsNotNone(run.score)
            self.assertGreaterEqual(run.score.score, 70)
            self.assertIsNotNone(run.route)
            self.assertEqual(run.route.decision, RouteDecision.AUTO_QUALIFY)
            self.assertIsNotNone(run.crm_record)
            self.assertEqual(run.crm_record.route_decision, "auto_qualify")
            self.assertTrue((tmp_path / "runs.jsonl").exists())

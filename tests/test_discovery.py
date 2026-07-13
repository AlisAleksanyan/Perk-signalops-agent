import unittest
import tempfile
from pathlib import Path

from signalops.discovery import WebDiscovery
from signalops.llm import ReplayLLMProvider
from signalops.pipeline import AccountQualificationPipeline


class ManualEnrichmentTests(unittest.TestCase):
    def test_known_company_name_enriches_without_extra_inputs(self):
        lead = WebDiscovery().enrich_company("Factorial")

        self.assertEqual(lead.domain, "factorialhr.com")
        self.assertEqual(lead.country, "Spain")
        self.assertGreaterEqual(lead.employee_count or 0, 1000)
        self.assertIn("travel", lead.raw_signal.lower())

    def test_known_company_name_scores_as_qualified_account(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            lead = WebDiscovery().enrich_company("Legora")
            pipeline = AccountQualificationPipeline(
                llm=ReplayLLMProvider(Path("data/replay_llm_responses.json")),
                db_path=tmp_path / "crm.sqlite",
                log_path=tmp_path / "runs.jsonl",
            )

            run = pipeline.run_one(lead)

            self.assertFalse(run.errors)
            self.assertIsNotNone(run.score)
            self.assertGreaterEqual(run.score.score, 70)
            self.assertIsNotNone(run.crm_record)


if __name__ == "__main__":
    unittest.main()

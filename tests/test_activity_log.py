import unittest

from app import simplify_logs


class ActivityLogTests(unittest.TestCase):
    def test_scoring_message_uses_run_company_name(self):
        logs = [
            {
                "timestamp": "2026-07-15T19:25:37+00:00",
                "run_id": "run-1",
                "step": "pipeline",
                "event_type": "started",
                "payload": {"lead": {"company_name": "ElevenLabs"}},
            },
            {
                "timestamp": "2026-07-15T19:25:41+00:00",
                "run_id": "run-1",
                "step": "scoring",
                "event_type": "finished",
                "payload": {"output": {"score": 75}},
            },
        ]

        messages = [event["message"] for event in simplify_logs(logs)]

        self.assertEqual(messages, ["ElevenLabs: fit score calculated: 75."])

    def test_crm_writeback_message_names_company_and_persisted_score(self):
        logs = [
            {
                "timestamp": "2026-07-15T19:25:45+00:00",
                "run_id": "run-2",
                "step": "crm_writeback",
                "event_type": "finished",
                "payload": {"output": {"company_name": "Legora", "perk_fit_score": 92}},
            }
        ]

        messages = [event["message"] for event in simplify_logs(logs)]

        self.assertEqual(messages, ["Legora: CRM record updated with score 92."])

    def test_stale_score_events_are_hidden_when_card_score_changed(self):
        logs = [
            {
                "timestamp": "2026-07-15T19:25:37+00:00",
                "run_id": "run-3",
                "step": "pipeline",
                "event_type": "started",
                "payload": {"lead": {"company_name": "Legora"}},
            },
            {
                "timestamp": "2026-07-15T19:25:41+00:00",
                "run_id": "run-3",
                "step": "scoring",
                "event_type": "finished",
                "payload": {"output": {"score": 75}},
            },
            {
                "timestamp": "2026-07-15T19:25:45+00:00",
                "run_id": "run-3",
                "step": "crm_writeback",
                "event_type": "finished",
                "payload": {"output": {"company_name": "Legora", "perk_fit_score": 75}},
            },
        ]
        accounts = [{"company_name": "Legora", "perk_fit_score": 92}]

        messages = [event["message"] for event in simplify_logs(logs, accounts)]

        self.assertEqual(messages, [])


if __name__ == "__main__":
    unittest.main()

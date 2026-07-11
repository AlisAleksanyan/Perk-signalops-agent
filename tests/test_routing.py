import unittest

from signalops.models import EnrichedAccount, FitScore, ResearchBrief, RouteDecision
from signalops.steps.routing import RoutingStep


class RoutingTests(unittest.TestCase):
    def test_high_score_high_confidence_auto_qualifies(self):
        route = RoutingStep().run(
            (
                EnrichedAccount("DeepL", "deepl.com", "Germany", 1000, "AI", "Germany", ""),
                ResearchBrief("summary", ["distributed offices"], ["expense, invoice, and spend visibility"], ["CFO"], [], 0.88),
                FitScore(88, 0.88, ["match"], [], "expense, invoice, and spend visibility", "strong fit"),
            ),
            FakeContext(),
        )

        self.assertEqual(route.decision, RouteDecision.AUTO_QUALIFY)
        self.assertEqual(route.sales_motion, "finance_led")
        self.assertEqual(route.region, "emea")

    def test_low_confidence_goes_to_human_review_even_with_medium_score(self):
        route = RoutingStep().run(
            (
                EnrichedAccount("Pleo", "pleo.io", "Denmark", 900, "Spend", "Denmark", ""),
                ResearchBrief("summary", ["possible product overlap"], ["travel policy and cross-border spend control"], ["Travel Manager"], [], 0.6),
                FitScore(72, 0.6, ["match"], ["product overlap"], "travel policy and cross-border spend control", "uncertain"),
            ),
            FakeContext(),
        )

        self.assertEqual(route.decision, RouteDecision.HUMAN_REVIEW)
        self.assertIn("confidence", route.human_review_reason)

    def test_low_score_rejects_when_confidence_is_sufficient(self):
        route = RoutingStep().run(
            (
                EnrichedAccount("Small Co", "small.example", "United States", 20, "Unknown", "US", ""),
                ResearchBrief("summary", ["weak signal"], ["unclear fit"], ["Operations Lead"], [], 0.8),
                FitScore(10, 0.8, [], ["too small"], "unclear fit", "weak fit"),
            ),
            FakeContext(),
        )

        self.assertEqual(route.decision, RouteDecision.REJECT)
        self.assertEqual(route.region, "us")


class FakeContext:
    run_id = "test"

    def log(self, step, event_type, payload):
        return None

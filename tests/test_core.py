import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze import local_sentiment, classify_aspects


class TestRestaurantReviewIntelligence(unittest.TestCase):

    def setUp(self):
        self.taxonomy = {
            "keywords": {
                "Food Quality": [
                    "food",
                    "fresh",
                    "cold",
                    "stale"
                ],
                "Service": [
                    "service",
                    "server",
                    "staff"
                ],
                "Wait Time": [
                    "wait",
                    "waiting",
                    "slow",
                    "late"
                ]
            }
        }

    def test_positive_sentiment(self):
        sentiment, confidence = local_sentiment(
            "The food was amazing and delicious.",
            5
        )

        self.assertEqual(sentiment, "Positive")
        self.assertGreater(confidence, 0)

    def test_negative_sentiment(self):
        sentiment, confidence = local_sentiment(
            "The service was terrible and very slow.",
            1
        )

        self.assertEqual(sentiment, "Negative")
        self.assertGreater(confidence, 0)

    def test_aspect_classification(self):
        result = classify_aspects(
            "The food was delicious but the service was very slow.",
            self.taxonomy,
            3
        )

        categories = [x["category"] for x in result]

        self.assertIn("Food Quality", categories)
        self.assertIn("Service", categories)
        self.assertIn("Wait Time", categories)


if __name__ == "__main__":
    unittest.main()

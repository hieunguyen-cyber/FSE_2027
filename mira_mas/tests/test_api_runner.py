import unittest
import tempfile
import json
from pathlib import Path
from mira_mas.evaluation.api_runner import run_openrouter_card
from mira_mas.models import DefectCard
from mira_mas.evaluation.preflight import verify_campaign_inputs


class ApiRunnerTests(unittest.TestCase):
    def test_unknown_victim_is_rejected_before_network(self):
        card = DefectCard("d", "p", "c", None, None, "before", "after")
        with self.assertRaisesRegex(ValueError, "victim"):
            run_openrouter_card(card, "unknown", "/private/tmp/unused")

    def test_preflight_rejects_placeholder_split(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cards, split = root / "cards.jsonl", root / "split.json"
            cards.write_text('{"defect_id":"d"}\n')
            split.write_text(json.dumps({"groups": []}))
            with self.assertRaisesRegex(ValueError, "no preregistered"):
                verify_campaign_inputs(cards, split)

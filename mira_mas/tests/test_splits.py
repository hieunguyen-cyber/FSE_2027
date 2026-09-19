import unittest
import tempfile
import json
from pathlib import Path
from mira_mas.data.splits import grouped_split, write_split_manifest
from mira_mas.models import DefectCard


class GroupedSplitTests(unittest.TestCase):
    def test_a_group_never_spans_partitions(self):
        cards = [DefectCard(str(i), "repo", str(i), None, "CWE-1", "old", "new", clone_cluster="same") for i in range(3)]
        partitions = grouped_split(cards)
        self.assertEqual(sum(bool(v) for v in partitions.values()), 1)

    def test_manifest_records_one_split_per_group(self):
        with tempfile.TemporaryDirectory() as directory:
            cards, manifest = Path(directory) / "cards.jsonl", Path(directory) / "split.json"
            cards.write_text("\n".join(json.dumps({"project": "r", "cwe": "CWE-1", "clone_cluster": "c"}) for _ in range(2)) + "\n")
            result = write_split_manifest(cards, manifest)
            self.assertEqual(len(result["groups"]), 1)

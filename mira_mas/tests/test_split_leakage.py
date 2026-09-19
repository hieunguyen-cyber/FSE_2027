import unittest
from mira_mas.models import DefectCard


def group_key(card: DefectCard) -> tuple[str, str, str]:
    return card.project, card.cwe or "unknown", card.clone_cluster


def assert_disjoint_splits(splits: dict[str, list[DefectCard]]) -> None:
    memberships = {}
    commits = {}
    for split, cards in splits.items():
        for card in cards:
            memberships.setdefault(group_key(card), set()).add(split)
            commits.setdefault((card.project, card.commit), set()).add(split)
    leaked = [key for key, values in {**memberships, **commits}.items() if len(values) > 1]
    if leaked:
        raise ValueError(f"split leakage: {leaked}")


class SplitLeakageTests(unittest.TestCase):
    def test_repository_cwe_clone_group_cannot_cross_split(self):
        card = DefectCard("a", "repo", "commit", None, "CWE-1", "a", "b", clone_cluster="cluster-1")
        with self.assertRaises(ValueError):
            assert_disjoint_splits({"train": [card], "test": [card]})

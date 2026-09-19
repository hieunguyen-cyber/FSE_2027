import json
import unittest
from mira_mas.models import EpisodeState, VisibleFact
from mira_mas.policy.surrogate_prior import FrozenSurrogatePrior


class NoTargetMemoryTests(unittest.TestCase):
    def test_episode_and_prior_have_no_identity_or_raw_response(self):
        episode = EpisodeState("d1", [VisibleFact("f1", "diff", "visible", "line")], 1)
        serialized = episode.to_public_json().lower()
        prior = json.dumps(FrozenSurrogatePrior.default().utilities).lower()
        for forbidden in ("target", "rationale", "model_id", "raw", "audit"):
            self.assertNotIn(forbidden, serialized)
            self.assertNotIn(forbidden, prior)

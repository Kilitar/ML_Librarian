import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/librarian"))
from hybrid import LexicalIndex, fuse_scores


class HybridTests(unittest.TestCase):
    def test_unknown_vocabulary_preserves_semantic_scores(self):
        scores = np.array([0.82, 0.91, 0.80])
        np.testing.assert_array_equal(fuse_scores(scores, np.zeros(3)), scores)

    def test_lexical_evidence_can_recover_semantically_missed_candidate(self):
        fused = fuse_scores(np.array([0.95, 0.9, 0.85]), np.array([0.0, 0.0, 0.8]))
        self.assertEqual(int(np.argmax(fused)), 2)
        self.assertLessEqual(float(fused.max()), 1)

    def test_zero_matches_have_no_lexical_vote(self):
        fused = fuse_scores(np.array([0.9, 0.8]), np.array([1.0, 0.0]))
        self.assertEqual(fused[0], 1)
        self.assertLess(fused[1], 0.5)

    def test_actual_tfidf_param_and_accent_matching(self):
        index = LexicalIndex([{"text": "RBF gamma C regularizace"}, {"text": "škálování příznaků"}])
        self.assertGreater(index.scores("gamma")[0], index.scores("gamma")[1])
        self.assertGreater(index.scores("skalovani")[1], 0)
        np.testing.assert_array_equal(index.scores("xyzunknown"), np.zeros(2))

    def test_spaced_ocr_does_not_match_individual_query_letters(self):
        index = LexicalIndex([{"text": "K m e a n s x y gamma"}, {"text": "KMeans clustering"}])
        np.testing.assert_array_equal(index.scores("k"), np.zeros(2))


if __name__ == "__main__":
    unittest.main()

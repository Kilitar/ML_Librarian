import copy
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/librarian"))
from score_quality import score


class QualityScoringTests(unittest.TestCase):
    def setUp(self):
        self.results = {"questions_sha256": "q", "search_sha256": "s",
                        "index_manifest": {"corpus_fingerprint": "c"}, "results": []}
        self.judgments = {"questions_sha256": "q", "search_sha256": "s",
                          "corpus_fingerprint": "c", "reviewer": "test", "queries": {}}
        for name, answerable, grades in [("supported", True, [0, 2, 1, 0, 2]),
                                         ("absent", False, [0, 0, 0, 0, 0])]:
            passages = [{"chunk_id": str(i), "text": str(i)} for i in range(5)]
            self.results["results"].append({"id": name, "answerable": answerable, "top5": passages})
            self.judgments["queries"][name] = [
                {"chunk_id": p["chunk_id"], "text_sha256": hashlib.sha256(p["text"].encode()).hexdigest(),
                 "grade": grade} for p, grade in zip(passages, grades)]

    def test_metrics_exclude_absent_questions(self):
        result = score(self.results, self.judgments)
        self.assertEqual(result["mrr_at_5"], 0.5)
        self.assertEqual(result["precision_at_5"], 0.4)
        self.assertEqual(result["unanswerable_with_useful_evidence"], 0)

    def test_changed_passage_cannot_reuse_judgment(self):
        self.results["results"][0]["top5"][0]["text"] = "changed"
        with self.assertRaises(ValueError):
            score(self.results, self.judgments)

    def test_incomplete_or_stale_review_is_rejected(self):
        stale = copy.deepcopy(self.judgments)
        stale["search_sha256"] = "different"
        with self.assertRaises(ValueError):
            score(self.results, stale)
        stale = copy.deepcopy(self.judgments)
        stale["ranking_files_sha256"] = {"constraints.py": "different"}
        with self.assertRaises(ValueError):
            score(self.results, stale)
        del self.judgments["queries"]["absent"]
        with self.assertRaises(ValueError):
            score(self.results, self.judgments)


if __name__ == "__main__":
    unittest.main()

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/librarian"))
from render_quality_review import render


class ReviewTests(unittest.TestCase):
    def test_untrusted_source_html_is_escaped(self):
        text = '<script>alert("source")</script>'
        passages = [{"chunk_id": str(i), "text": text, "source_path": "<source>", "ranking_score": 0.8} for i in range(5)]
        results = {"questions_sha256": "q", "search_sha256": "s", "index_manifest": {"corpus_fingerprint": "c"},
                   "results": [{"id": "test", "answerable": True, "query": '<img onerror="bad">',
                                "required_evidence": "criterion", "top5": passages}]}
        judgments = {"questions_sha256": "q", "search_sha256": "s", "corpus_fingerprint": "c", "reviewer": "test",
                     "queries": {"test": [{"chunk_id": str(i), "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                                           "grade": 2, "reason": "reason"} for i in range(5)]}}
        page = render(results, judgments)
        self.assertNotIn('<script>', page)
        self.assertNotIn('<img onerror=', page)
        self.assertIn('&lt;script&gt;', page)
        self.assertEqual(page.count('<article>'), 5)
        self.assertEqual(page.count('<details open>'), 1)


if __name__ == "__main__":
    unittest.main()

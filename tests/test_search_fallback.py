import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/librarian'))
from search import E5SearchIndex


class SearchFallbackTests(unittest.TestCase):
    def setUp(self):
        model = Mock()
        model.encode.return_value = np.array([[1.0]])
        documents = [{'chunk_id': str(i), 'source_path': f'theory/{i}.md',
                      'text': 'Alpha theory explanation and beta parameters.'} for i in range(2)]
        # Different texts are necessary to verify all evidence identities survive.
        documents[1]['text'] = 'Beta practical example with alpha coefficient.'
        self.index = E5SearchIndex(documents, np.array([[.9], [.8]]), model)

    def test_e5_default_does_not_load_reranker(self):
        with patch('search.PassageReranker') as loader:
            results = self.index.search('What is alpha?')
        loader.assert_not_called()
        self.assertTrue(all(r['retrieval_mode'] == 'e5' for r in results))

    def test_missing_offline_model_has_visible_e5_fallback(self):
        with patch('search.PassageReranker', side_effect=OSError('missing cache')):
            results = self.index.search('What is alpha?', mode='rerank')
        self.assertTrue(results)
        self.assertTrue(all(r['retrieval_mode'] == 'e5' and r['retrieval_warning'] for r in results))

    def test_prediction_error_does_not_break_search(self):
        self.index.passage_reranker = Mock()
        self.index.passage_reranker.score_details.side_effect = RuntimeError('inference unavailable')
        results = self.index.search('What is alpha?', mode='rerank')
        self.assertEqual(results[0]['chunk_id'], '0')
        self.assertIn('retrieval_warning', results[0])

    def test_comparison_failure_preserves_original_e5_question(self):
        with patch('search.PassageReranker', side_effect=OSError('missing cache')):
            results = self.index.search('What is the difference between alpha and beta?', mode='rerank', comparison_tuning=True, comparison_experiment=True)
        self.assertTrue(all(r['retrieval_mode']=='e5' and not r['comparison_aspects'] for r in results))
        self.assertIn('difference between alpha and beta', self.index.model.encode.call_args[0][0][0])


if __name__ == '__main__':
    unittest.main()

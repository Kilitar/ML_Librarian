import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/librarian"))
from rerank import candidate_union, passage_input, expand_neighbors, parameter_queries
from diversify import select_distinct


class RerankTests(unittest.TestCase):
    def test_union_keeps_both_retrievers_without_duplicate_indices(self):
        result = candidate_union(np.array([.9, .8, .7, .6]), np.array([0, .8, 0, 1]), per_retriever=2)
        self.assertEqual(result, [0, 1, 3])
        self.assertEqual(candidate_union(np.array([.9, .8]), np.zeros(2), 1), [0])

    def test_context_is_real_provenance_not_a_generated_answer(self):
        document = {"source_path": "svm_theory.md", "text": "C controls regularization"}
        text = passage_input(document)
        self.assertIn("svm_theory.md", text)
        self.assertIn(document['text'], text)

    def test_complementary_passages_can_share_a_source(self):
        docs = [{'source_path': 'svm', 'text': 'C explanation'},
                {'source_path': 'svm', 'text': 'gamma explanation'},
                {'source_path': 'other', 'text': 'less useful'}]
        self.assertEqual(select_distinct(docs, [0, 1, 2], 2, max_per_source=2), [0, 1])
        self.assertEqual(select_distinct(docs, [0, 1, 2], 2), [0, 2])

    def test_neighbors_never_cross_source_boundary(self):
        docs = [{'source_path': path} for path in ['other', 'svm', 'svm', 'svm', 'other']]
        self.assertEqual(set(expand_neighbors(docs, [2])), {1, 2, 3})
        self.assertLessEqual(len(expand_neighbors(docs, [2], maximum=2)), 2)

    def test_parameter_decomposition_keeps_question_without_invented_content(self):
        queries = parameter_queries('How do C and gamma affect overfitting in SVM?')
        self.assertEqual(len(queries), 2)
        self.assertNotIn('gamma', queries[0])
        self.assertNotRegex(queries[1], r'\bC\b')
        self.assertTrue(all('overfitting in SVM' in q for q in queries))
        self.assertEqual(parameter_queries('What is PCA?'), [])


if __name__ == '__main__':
    unittest.main()

import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/librarian'))
from evidence_gate import assess_evidence
from rerank import REVISION


class GateTests(unittest.TestCase):
    def passage(self, score):
        return {'retrieval_mode': 'rerank', 'reranker_revision': REVISION,
                'whole_query_score': score, 'ranking_score': 100}

    def test_bonus_and_subquestion_scores_cannot_supply_support(self):
        result = self.passage(.02)
        result['passage_score'] = .99
        self.assertEqual(assess_evidence([result])['status'], 'no_support')

    def test_boundaries(self):
        for value, status in ((.099, 'no_support'), (.10, 'uncertain'), (.199, 'uncertain'), (.20, 'supported')):
            self.assertEqual(assess_evidence([self.passage(value)])['status'], status)

    def test_related_concept_is_visible_but_not_claimed_as_definition(self):
        result = self.passage(.002)
        result.update(canonical_query='What is deep learning?', concept_evidence=2)
        self.assertEqual(assess_evidence([result])['status'], 'uncertain')
        result['retrieval_mode'] = 'e5'
        self.assertEqual(assess_evidence([result])['status'], 'unassessed')

    def test_explicit_definition_supplies_support_only_with_valid_model(self):
        result = self.passage(.02)
        result.update(requested_acronym='ML', acronym_definition=True)
        self.assertEqual(assess_evidence([result], 'Co znamená zkratka ML')['status'], 'supported')
        result['reranker_revision'] = 'different'
        self.assertEqual(assess_evidence([result])['status'], 'unassessed')

    def test_ambiguous_questions_need_topic_but_short_named_topics_are_allowed(self):
        self.assertEqual(assess_evidence([self.passage(.99)], 'Jak to funguje?')['status'], 'uncertain')
        self.assertEqual(assess_evidence([self.passage(.99)], 'PCA')['status'], 'supported')

    def test_fallback_or_unknown_model_cannot_be_classified_by_its_score(self):
        result = self.passage(.99)
        result['retrieval_mode'] = 'e5'
        self.assertEqual(assess_evidence([result])['status'], 'unassessed')
        result = self.passage(.99)
        result['reranker_revision'] = 'different'
        self.assertEqual(assess_evidence([result])['status'], 'unassessed')

    def test_nonfinite_or_missing_score_is_unassessed(self):
        for value in (float('nan'), float('inf'), -1, 2, None):
            self.assertEqual(assess_evidence([self.passage(value)])['status'], 'unassessed')


if __name__ == '__main__':
    unittest.main()

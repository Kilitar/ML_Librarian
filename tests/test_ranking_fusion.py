import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/librarian'))
from ranking_fusion import weak_fusion
from search import E5SearchIndex
from unittest.mock import Mock
from evidence_gate import assess_evidence


class FusionTests(unittest.TestCase):
    def test_either_rank_can_rescue_a_candidate(self):
        result = weak_fusion([.9,.8,.7], [.01,.09,.02], [.01,.09,.02])
        self.assertEqual(list(np.argsort(-result)), [1,0,2])

    def test_uncertain_or_strong_candidate_disables_fusion_even_if_not_first(self):
        self.assertIsNone(weak_fusion([.9,.8], [.01,.10], [.01,.10]))
        self.assertIsNone(weak_fusion([.9,.8], [.1,.2], [.1,.2]))

    def test_invalid_metadata_cannot_activate_fusion(self):
        for a,b,c in [([],[],[]), ([.9],[.1,.2],[.1]), ([.9],[float('nan')],[.1]),
                      ([.9],[.1],[1.1]), ([[.9]],[[.1]],[[.1]])]:
            self.assertIsNone(weak_fusion(a,b,c))

    def test_does_not_mutate_model_scores_and_ties_stable(self):
        scores=np.array([.09,.09]); before=scores.copy()
        result=weak_fusion([.8,.8],scores,scores)
        np.testing.assert_array_equal(scores,before)
        self.assertGreater(result[0],result[1])


class SearchFusionTests(unittest.TestCase):
    def index(self, values):
        model=Mock()
        model.encode.return_value=np.array([[1.]])
        docs=[{'chunk_id':str(i),'source_path':f'{i}.md','text':f'Long general explanation {i} about a specific topic. '*5} for i in range(3)]
        index=E5SearchIndex(docs,np.array([[.9],[.8],[.7]]),model)
        index.passage_reranker=Mock()
        index.passage_reranker.score_details.return_value={'relevance':np.array(values),'whole_query':np.array(values)}
        return index

    def test_rank_fusion_preserves_evidence_and_does_not_supply_support(self):
        index=self.index([.01,.09,.02])
        before=index.search('Alpha topic',mode='rerank',ranking_strategy='reranker')
        after=index.search('Alpha topic',mode='rerank',ranking_strategy='weak_fusion')
        self.assertNotEqual([r['chunk_id'] for r in before],[r['chunk_id'] for r in after])
        self.assertTrue(all(r['ranking_policy']=='weak-fusion-v2' for r in after))
        self.assertEqual({r['chunk_id']:r['whole_query_score'] for r in before},
                         {r['chunk_id']:r['whole_query_score'] for r in after})
        self.assertEqual(assess_evidence(after)['status'],'no_support')

    def test_strong_results_are_identical_and_unknown_strategy_rejected(self):
        index=self.index([.01,.8,.02])
        self.assertEqual(index.search('Alpha topic',mode='rerank',ranking_strategy='reranker'),
                         index.search('Alpha topic',mode='rerank',ranking_strategy='weak_fusion'))
        with self.assertRaises(ValueError):
            index.search('Alpha',ranking_strategy='unknown')

    def test_filter_view_forwards_strategy_without_leaking_hidden_group(self):
        index=self.index([.01,.09,.02])
        # Even when no documents are excluded, constructing the filtered view
        # must preserve strategy and leave the shared corpus intact.
        after=index.search('Alpha topic',mode='rerank',ranking_strategy='weak_fusion',excluded_origins=['Coderslab PDF'])
        self.assertTrue(all(r['ranking_policy']=='weak-fusion-v2' for r in after))
        self.assertEqual(len(index.documents),3)

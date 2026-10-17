import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/librarian'))
from result_presentation import partition_results
from rerank import REVISION


class PresentationTests(unittest.TestCase):
    def rows(self):
        context={'axis':'prediction_target','query':'compare target'}
        return [dict(text=text, context_score=score, comparison_context=context,
                     comparison_aspects=['What is regression?','What is classification?'],
                     retrieval_mode='rerank',reranker_revision=REVISION)
                for text,score in [('Regrese má spojitý cíl, klasifikace kategoriální.',.9),
                                   ('Regrese a klasifikace: další vysvětlení.',.4),
                                   ('Škálování v regresi.',.43),
                                   ('Regrese versus klasifikace: pouhá zmínka.',.1)]]

    def test_grouping_preserves_ranks_and_all_original_objects(self):
        rows=self.rows();main,extra=partition_results(rows,'supported')
        self.assertEqual([i for i,_ in main],[1,2])
        self.assertEqual([i for i,_ in extra],[3,4])
        self.assertTrue(all(r is rows[i-1] for i,r in main+extra))

    def test_partial_first_needs_complementary_results_visible(self):
        rows=self.rows();rows[0]['text']='Regrese má spojitý cíl.'
        self.assertEqual(len(partition_results(rows,'supported')[0]),4)

    def test_uncertain_unsupported_and_fallback_remain_unchanged(self):
        for status in ('uncertain','no_support','unassessed'):
            self.assertFalse(partition_results(self.rows(),status)[1])
        rows=self.rows();rows[1]['retrieval_mode']='e5'
        self.assertFalse(partition_results(rows,'supported')[1])

    def test_missing_invalid_or_unknown_context_fails_open(self):
        for value in (None,float('nan'),float('inf'),-1,2):
            rows=self.rows();rows[1]['context_score']=value
            self.assertFalse(partition_results(rows,'supported')[1])
        rows=self.rows();rows[0]['comparison_context']={'axis':'unknown'}
        self.assertFalse(partition_results(rows,'supported')[1])

    def test_normal_queries_keep_all_results(self):
        self.assertEqual(partition_results([{'text':'ML'}],'supported'), ([(1,{'text':'ML'})],[]))

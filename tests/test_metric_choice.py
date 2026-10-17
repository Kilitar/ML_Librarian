import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/librarian'))
from metric_choice import plan, eligible, coverage_order
from search import E5SearchIndex
from evidence_gate import assess_evidence

QUERY='When is precision more important than recall in a spam filter?'


class MetricPlanTests(unittest.TestCase):
    def test_explicit_priority_languages_and_reverse_error_class(self):
        for q in (QUERY,'Kdy je precision důležitější než recall při filtrování spamu?',
                  'Kiedy precision jest ważniejsza od recall w filtrze spamu?',
                  'Why should we prefer precision over recall for an automated spam filter?'):
            self.assertEqual(plan(q)['error_code'],'FP')
        self.assertEqual(plan('When is recall more important than precision for medical screening?')['error_code'],'FN')

    def test_no_unbounded_rewrite_or_inferred_priority(self):
        for q in ('What is precision?','Compare precision and recall','When is precision more important than recall?',
                  'Why is precision not more important than recall in spam?','When is precision more important than precision in spam?'):
            self.assertIsNone(plan(q))

    def test_context_requires_error_class_and_scenario_body_anchor(self):
        request=plan(QUERY)
        self.assertTrue(eligible({'text':'Precision reduces FP in spam filters.'},request))
        self.assertFalse(eligible({'text':'FP matters for medical screening.'},request))
        self.assertFalse(eligible({'text':'Recall reduces FN in spam filters.'},request))

    def test_only_missing_context_is_inserted_and_first_is_preserved(self):
        ranked=[0,1,2,3]
        self.assertEqual(coverage_order(ranked,[0,1,2],{3:.8}),([0,3,1,2],3))
        self.assertEqual(coverage_order(ranked,[0,1,3],{3:.8}),(ranked,None))
        self.assertEqual(coverage_order(ranked,[0,1,2],{3:.19}),(ranked,None))


class MetricSearchTests(unittest.TestCase):
    def index(self,whole=(.8,.6,.5,.01),facet=.9):
        model=Mock();model.encode.return_value=np.array([[1.]])
        docs=[{'chunk_id':str(i),'source_path':f'{i}.md',
               'text':f'General explanation {i} of a metric and its use. '*5} for i in range(4)]
        docs[3]['text']='Precision minimizes FP in spam filtering to avoid losing an important email. '*3
        index=E5SearchIndex(docs,np.array([[.9],[.8],[.7],[.6]]),model)
        index.passage_reranker=Mock()
        base={'whole_query':np.array(whole),'relevance':np.array(whole)}
        extra={'whole_query':np.array([facet])}
        index.passage_reranker.score_details.side_effect=[base,extra]
        return index

    def test_adds_error_cost_without_changing_whole_query_support(self):
        index=self.index();results=index.search(QUERY,mode='rerank',limit=3)
        self.assertEqual([r['chunk_id'] for r in results],['0','3','1'])
        self.assertTrue(results[1]['metric_choice_context'])
        self.assertEqual(results[1]['whole_query_score'],.01)
        self.assertEqual(results[1]['metric_choice_facet_score'],.9)
        self.assertEqual(assess_evidence(results,QUERY)['status'],'supported')

    def test_facet_never_supplies_support_to_weak_original_query(self):
        index=self.index(whole=(.09,.08,.07,.01))
        results=index.search(QUERY,mode='rerank',limit=3)
        self.assertEqual(index.passage_reranker.score_details.call_count,1)
        self.assertFalse(any(r['metric_choice_context'] for r in results))
        self.assertEqual(assess_evidence(results,QUERY)['status'],'no_support')

    def test_optional_facet_failure_and_disable_keep_original_ranking(self):
        index=self.index();base=index.passage_reranker.score_details.side_effect
        index.passage_reranker.score_details.side_effect=[{'whole_query':np.array([.8,.6,.5,.01]),'relevance':np.array([.8,.6,.5,.01])},RuntimeError('unavailable')]
        results=index.search(QUERY,mode='rerank',limit=3)
        self.assertEqual([r['chunk_id'] for r in results],['0','1','2'])
        index=self.index()
        results=index.search(QUERY,mode='rerank',limit=3,metric_choice_tuning=False,excluded_origins=['Coderslab PDF'])
        self.assertEqual([r['chunk_id'] for r in results],['0','1','2'])
        self.assertTrue(all(r['metric_choice_plan'] is None for r in results))
        self.assertEqual(index.passage_reranker.score_details.call_count,1)

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/librarian'))
from domain_guard import DomainGuard,VERSION,MODEL_ID,ENCODER_REVISION,DIMENSION
from evidence_gate import assess_evidence
from rerank import REVISION
from search import E5SearchIndex

QUERY='A fixed unrelated question'


def artifact(**changes):
    data={'version':VERSION,'encoder_id':MODEL_ID,'encoder_revision':ENCODER_REVISION,
          'dimension':DIMENSION,'training_sha256':'training','query_prefix':'query: ',
          'normalized':True,'threshold':.5,'coefficients':[1.]+[0.]*(DIMENSION-1),'intercept':-2.}
    return json.dumps({**data,**changes}).encode()


def guard():return DomainGuard(artifact(),'training')


def vector():return np.array([1.]+[0.]*(DIMENSION-1))


class DomainArtifactTests(unittest.TestCase):
    def test_revision_training_shape_and_nonfinite_coefficients_are_checked(self):
        for changes in ({'encoder_revision':'other'},{'training_sha256':'stale'},
                        {'coefficients':[1.]},{'coefficients':[float('nan')]*DIMENSION}):
            with self.assertRaises(ValueError):DomainGuard(artifact(**changes),'training')
        with self.assertRaises(ValueError):DomainGuard(b'[]','training')

    def test_invalid_or_incompatible_vectors_cannot_generate_signal(self):
        g=guard()
        for v,rev in [(np.array([1.]),ENCODER_REVISION),(vector()*2,ENCODER_REVISION),
                      (vector()*float('nan'),ENCODER_REVISION),(vector(),'unknown')]:
            self.assertIsNone(g.signal(v,QUERY,rev))

    def test_signal_is_bound_to_query_artifact_and_model(self):
        g=guard();s=g.signal(vector(),QUERY,ENCODER_REVISION)
        self.assertTrue(g.outside(s,QUERY))
        self.assertFalse(g.outside(s,'another question'))
        self.assertTrue(g.outside(s,'  A   fixed unrelated question  '))
        for changes in ({'artifact_sha256':'other'},{'encoder_revision':'other'},
                        {'score':float('nan')},{'score':True},{'score':-.1},{'score':.5}):
            self.assertFalse(g.outside({**s,**changes},QUERY))


class DomainGateTests(unittest.TestCase):
    def passage(self,value):
        return {'retrieval_mode':'rerank','reranker_revision':REVISION,'whole_query_score':value,
                'domain_signal':guard().signal(vector(),QUERY,ENCODER_REVISION)}

    def test_only_grey_band_can_be_rejected_and_original_score_stays_visible(self):
        with patch('domain_guard.load_guard',return_value=guard()):
            for value in (.10,.15,.199):
                d=assess_evidence([self.passage(value)],QUERY)
                self.assertEqual(d['status'],'no_support');self.assertEqual(d['score'],value)
                self.assertEqual(d['reason'],'out_of_domain_grey_band')
            self.assertEqual(assess_evidence([self.passage(.2)],QUERY)['status'],'supported')
            self.assertEqual(assess_evidence([self.passage(.099)],QUERY)['status'],'no_support')

    def test_unknown_reranker_fallback_or_stale_query_keep_previous_rules(self):
        with patch('domain_guard.load_guard',return_value=guard()):
            self.assertEqual(assess_evidence([self.passage(.15)],'different')['status'],'uncertain')
            for key,value in [('retrieval_mode','e5'),('reranker_revision','other')]:
                r=self.passage(.15);r[key]=value
                self.assertEqual(assess_evidence([r],QUERY)['status'],'unassessed')

    def test_structural_partial_related_acronym_and_ambiguity_precede_guard(self):
        with patch('domain_guard.load_guard',return_value=guard()):
            r=self.passage(.15);r.update(comparison_aspects=['A','B'],aspect_scores=[.9,.9])
            self.assertEqual(assess_evidence([r],QUERY)['status'],'uncertain')
            r=self.passage(.15);r['related_evidence_only']=True
            self.assertEqual(assess_evidence([r],QUERY)['status'],'uncertain')
            r=self.passage(.15);r.update(requested_acronym='ML',acronym_definition=True)
            self.assertEqual(assess_evidence([r],QUERY)['status'],'supported')
            self.assertEqual(assess_evidence([self.passage(.15)],'Jak to funguje?')['status'],'uncertain')

    def test_missing_mixed_or_unavailable_artifact_fails_open_to_uncertain(self):
        r=self.passage(.15);other=self.passage(.14);other.pop('domain_signal')
        with patch('domain_guard.load_guard',return_value=guard()):
            self.assertEqual(assess_evidence([r,other],QUERY)['status'],'uncertain')
        with patch('domain_guard.load_guard',side_effect=FileNotFoundError()):
            self.assertEqual(assess_evidence([r],QUERY)['status'],'uncertain')


class DomainSearchTests(unittest.TestCase):
    def index(self,values=(.15,.13)):
        model=Mock();model.encode.return_value=np.array([vector()])
        docs=[{'chunk_id':str(i),'source_path':f'{i}.md','text':f'General explanation {i}. '*20} for i in range(2)]
        index=E5SearchIndex(docs,np.array([vector()*.9,vector()*.8]),model,encoder_revision=ENCODER_REVISION)
        index.passage_reranker=Mock()
        index.passage_reranker.score_details.return_value={'whole_query':np.array(values),'relevance':np.array(values)}
        return index

    def test_reuses_original_query_vector_and_preserves_rank_and_scores(self):
        index=self.index()
        before=index.search(QUERY,mode='rerank',domain_guard_tuning=False)
        index.model.encode.reset_mock()
        with patch('domain_guard.load_guard',return_value=guard()):
            after=index.search(QUERY,mode='rerank',domain_guard_tuning=True)
            self.assertEqual(assess_evidence(after,QUERY)['status'],'no_support')
        self.assertEqual([r['chunk_id'] for r in before],[r['chunk_id'] for r in after])
        self.assertEqual([r['whole_query_score'] for r in before],[r['whole_query_score'] for r in after])
        self.assertEqual(index.model.encode.call_count,1)

    def test_strong_results_do_not_load_classifier_and_filters_keep_binding(self):
        index=self.index(values=(.8,.7))
        with patch('search.make_signal') as signal:
            after=index.search(QUERY,mode='rerank',domain_guard_tuning=True)
        signal.assert_not_called();self.assertTrue(all('domain_signal' not in r for r in after))
        index=self.index()
        with patch('domain_guard.load_guard',return_value=guard()):
            after=index.search(QUERY,mode='rerank',domain_guard_tuning=True,excluded_origins=['Coderslab PDF'])
            self.assertEqual(assess_evidence(after,QUERY)['status'],'no_support')

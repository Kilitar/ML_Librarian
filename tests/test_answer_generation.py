import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
import urllib.error
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src/librarian'))
from answer_generation import generate_answer, prepare_context, validate_answer, GenerationError, NoRedirect


class AnswerTests(unittest.TestCase):
    def setUp(self):
        self.rows=[dict(chunk_id='abc',source_path='notes.md',locator='line:4',text='Precision is the fraction of predicted positives that are correct.')]
        self.evidence={'status':'supported'}
        self.context=prepare_context('What is precision?',self.rows,self.evidence)
        self.answer=dict(status='answered',claims=[dict(text='Precision measures correctness of positive predictions.',citations=[dict(source_id='S1',quote=self.rows[0]['text'])])],limitation='')

    def test_missing_consent_and_weak_evidence_make_no_request(self):
        transport=Mock()
        for status,consent in [('supported',False),('no_support',True),('unassessed',True)]:
            with self.assertRaises(GenerationError):
                generate_answer('Question',self.rows,{'status':status},'fake','test-model',consent=consent,transport=transport)
        transport.assert_not_called()

    def test_nonexistent_or_invented_citation_is_rejected(self):
        for citation in [dict(source_id='S9',quote=self.rows[0]['text']),dict(source_id='S1',quote='Invented quotation not present in any passage')]:
            self.answer['claims'][0]['citations']=[citation]
            with self.assertRaises(GenerationError): validate_answer(self.answer,self.context)

    def test_uncited_claim_and_inconsistent_refusal_are_rejected(self):
        self.answer['claims'][0]['citations']=[]
        with self.assertRaises(GenerationError): validate_answer(self.answer,self.context)
        self.answer['status']='insufficient'
        with self.assertRaises(GenerationError): validate_answer(self.answer,self.context)
        self.assertEqual(validate_answer(dict(status='insufficient',claims=[],limitation='No definition in sources.'),self.context)['status'],'insufficient')

    def test_uncertain_retrieval_cannot_become_unqualified_answer(self):
        context=prepare_context('Question',self.rows,{'status':'uncertain'})
        self.assertEqual(validate_answer(self.answer,context)['status'],'partial')

    def test_request_is_bounded_and_uses_only_supplied_sources(self):
        response=io.BytesIO(json.dumps({'choices':[{'finish_reason':'stop','message':{'content':json.dumps(self.answer)}}]}).encode())
        transport=Mock(return_value=response)
        result=generate_answer('What is precision?',self.rows,self.evidence,'fake-secret','test-model',consent=True,transport=transport)
        request=transport.call_args.args[0];payload=json.loads(request.data)
        self.assertEqual(result['status'],'answered')
        self.assertEqual(request.get_header('User-agent'),'ML-Librarian/1.0')
        self.assertFalse(payload['store']);self.assertEqual(payload['max_completion_tokens'],1800)
        self.assertNotIn('fake-secret',request.data.decode())
        self.assertEqual(transport.call_args.kwargs['timeout'],45)
        rows=self.rows*7
        for r in rows:r['text']='X'*5000
        bounded=prepare_context('Question',rows,self.evidence)
        self.assertEqual(len(bounded['sources']),5)
        self.assertTrue(all(len(s['text'])==4000 and s['truncated'] for s in bounded['sources']))

    def test_provider_failure_redacts_body_and_credentials(self):
        transport=Mock(side_effect=urllib.error.HTTPError('secret-url',429,'fake-secret',{},None))
        with self.assertRaises(GenerationError) as exc:
            generate_answer('Question',self.rows,self.evidence,'fake-secret','test-model',consent=True,transport=transport)
        self.assertIn('429',str(exc.exception));self.assertNotIn('secret',str(exc.exception))
        self.assertIsNone(NoRedirect().redirect_request(None,None,None,None,None,None))

    def test_invalid_quote_gets_only_one_correction_with_same_sources(self):
        bad=json.loads(json.dumps(self.answer))
        bad['claims'][0]['citations'][0]['quote']='Invented quotation not present in source.'
        def wire(answer):
            return io.BytesIO(json.dumps({'choices':[{'finish_reason':'stop','message':{'content':json.dumps(answer)}}]}).encode())
        transport=Mock(side_effect=[wire(bad),wire(self.answer)])
        result=generate_answer('Question',self.rows,self.evidence,'fake','test-model',consent=True,transport=transport)
        self.assertEqual(result['status'],'answered')
        self.assertEqual(transport.call_count,2)
        first,second=[json.loads(c.args[0].data) for c in transport.call_args_list]
        self.assertEqual(first['messages'][:2],second['messages'][:2])
        self.assertIsNone(transport.call_args_list[1].args[0].get_header('Content-length'))
        transport=Mock(side_effect=[wire(bad),wire(bad)])
        with self.assertRaises(GenerationError):
            generate_answer('Question',self.rows,self.evidence,'fake','test-model',consent=True,transport=transport)
        self.assertEqual(transport.call_count,2)

    def test_diagnostic_categories_do_not_expose_exception_details(self):
        cases=[(urllib.error.URLError('fake-secret'), 'spojení'),
               (json.JSONDecodeError('fake-secret','',0), 'JSON'),
               (KeyError('fake-secret'), 'strukturu')]
        for error, expected in cases:
            with self.subTest(expected=expected):
                with self.assertRaises(GenerationError) as caught:
                    generate_answer('Question',self.rows,self.evidence,'fake-secret','test-model',consent=True,transport=Mock(side_effect=error))
                self.assertIn(expected,str(caught.exception))
                self.assertNotIn('fake-secret',str(caught.exception))

    def test_truncated_output_is_not_displayed(self):
        transport=Mock(return_value=io.BytesIO(json.dumps({'choices':[{'finish_reason':'length','message':{'content':json.dumps(self.answer)}}]}).encode()))
        with self.assertRaises(GenerationError):
            generate_answer('Question',self.rows,self.evidence,'fake','test-model',consent=True,transport=transport)


if __name__=='__main__':unittest.main()

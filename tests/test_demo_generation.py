import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/librarian'))
from demo_generation import demo_config,generate_demo_answer,DEFAULT_MODEL
from answer_generation import generate_answer,GenerationError


class DemoGenerationTests(unittest.TestCase):
    def test_operator_config_only_no_openai_fallback(self):
        self.assertFalse(demo_config({}, {'OPENAI_API_KEY':'unused'})['api_key'])
        config=demo_config({'GROQ_API_KEY':'server-test-key'}, {})
        self.assertEqual(config['api_key'],'server-test-key')
        self.assertEqual(config['model'],DEFAULT_MODEL)

    def test_missing_config_does_not_call_api(self):
        with patch('demo_generation.generate_answer') as call:
            with self.assertRaises(GenerationError):generate_demo_answer('q',[],{},demo_config({},{}),consent=True)
            call.assert_not_called()

    def test_groq_wire_format_uses_fixed_endpoint_no_store(self):
        rows=[dict(chunk_id='c1',source_path='notes.md',text='A sufficiently long supporting source passage.')]
        reply={'status':'insufficient','claims':[],'limitation':'Source does not answer the question.'}
        wire={'choices':[{'finish_reason':'stop','message':{'content':json.dumps(reply)}}]}
        def transport(request,timeout):
            self.assertEqual(request.full_url,'https://api.groq.com/openai/v1/chat/completions')
            payload=json.loads(request.data)
            self.assertNotIn('store',payload)
            self.assertNotIn('tools',payload)
            self.assertEqual(payload['model'],DEFAULT_MODEL)
            self.assertNotIn('server-test-key',request.data.decode())
            return io.BytesIO(json.dumps(wire).encode())
        result=generate_answer('Question',rows,{'status':'supported'},'server-test-key',DEFAULT_MODEL,provider='groq',consent=True,transport=transport)
        self.assertEqual(result['status'],'insufficient')


if __name__=='__main__':unittest.main()

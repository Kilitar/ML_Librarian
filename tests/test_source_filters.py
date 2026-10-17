import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/librarian'))
from search import E5SearchIndex
from source_filters import SOURCE_ROLES, SOURCE_ORIGINS


class SourceFilterTests(unittest.TestCase):
    def setUp(self):
        self.model=Mock();self.model.encode.return_value=np.array([[1.]])
        self.docs=[{'chunk_id':str(i),'source_path':f'Resources/Day PDF/{i}.txt' if i<5 else f'notes/theory/{i}.md',
                    'source_kind':'pdf' if i<5 else 'markdown','text':f'Unique explanatory material passage {i}.'} for i in range(10)]
        self.index=E5SearchIndex(self.docs,np.array([[1-i*.05] for i in range(10)]),self.model)

    def test_hidden_pdf_is_replaced_from_full_allowed_corpus(self):
        results=self.index.search('What is ML?',excluded_origins=['Coderslab PDF'])
        self.assertEqual(len(results),5)
        self.assertTrue(all(r['source_origin']!='Coderslab PDF' for r in results))
        self.assertEqual(len(self.index.documents),10)

    def test_role_and_origin_exclusions_are_combined(self):
        self.assertEqual(self.index.search('ML',excluded_roles=['Teorie / analýza'],excluded_origins=['Coderslab PDF']),[])
        self.model.encode.assert_not_called()

    def test_fallback_cannot_reintroduce_hidden_groups(self):
        with patch('search.PassageReranker',side_effect=OSError('missing model')):
            results=self.index.search('ML',mode='rerank',excluded_origins=['Coderslab PDF'])
        self.assertTrue(results)
        self.assertTrue(all(r['source_origin']!='Coderslab PDF' and r['retrieval_warning'] for r in results))

    def test_empty_filters_preserve_baseline_and_do_not_leak(self):
        baseline=self.index.search('ML')
        self.index.search('ML',excluded_origins=['Coderslab PDF'])
        self.assertEqual(self.index.search('ML',excluded_roles=[],excluded_origins=[]),baseline)

    def test_all_hidden_and_invalid_groups(self):
        self.assertEqual(self.index.search('ML',excluded_roles=SOURCE_ROLES),[])
        self.assertEqual(self.index.search('ML',excluded_origins=SOURCE_ORIGINS),[])
        for value in (['unknown'],'Coderslab PDF'):
            with self.assertRaises(ValueError):self.index.search('ML',excluded_origins=value)

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/librarian'))
from heading_context import AdjacentHeadings
from rerank import PassageReranker


class HeadingTests(unittest.TestCase):
    def test_only_one_standalone_latex_part_may_bridge_heading_and_body(self):
        def row(n,call,text):return {'source_path':'a.py','source_kind':'streamlit_literal','locator':f'line:{n}:st.{call}','text':text}
        rows=[row(10,'markdown','#### Precision'),row(11,'latex','TP/(TP+FP)'),row(12,'markdown','Cost of false alarms'),
              row(20,'markdown','#### Other heading'),row(21,'code','intervening code'),row(22,'markdown','Unrelated body')]
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'parts.jsonl';p.write_text('\n'.join(json.dumps(r) for r in rows),encoding='utf-8')
            old=AdjacentHeadings(p,allow_formula=False);new=AdjacentHeadings(p)
        self.assertIsNone(old.for_document(rows[2]))
        context=new.for_document(rows[2])
        self.assertEqual(context['text'],'#### Precision')
        self.assertEqual(context['intervening_formula_locator'],'line:11:st.latex')
        self.assertIsNone(new.for_document(rows[5]))

    def test_source_order_adjacency_and_boundaries(self):
        def row(line,text,path='a.py',kind='streamlit_literal'):
            return {'source_path':path,'source_kind':kind,'locator':f'line:{line}:st.markdown','text':text}
        rows=[row(11,'Body'),row(10,'#### Real heading'),row(14,'Second body'),
              row(16,'#### Distant'),row(25,'Far away'),row(11,'Other source','b.py'),
              row(30,'#### Another heading'),row(31,'intervening code'),row(32,'not a direct child'),
              row(40,'#### Fake\nParagraph'),row(41,'No heading')]
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'parts.jsonl';p.write_text('\n'.join(json.dumps(r) for r in rows),encoding='utf-8')
            catalog=AdjacentHeadings(p)
        h=catalog.for_document(rows[0])
        self.assertEqual(h['text'],'#### Real heading')
        self.assertEqual(h['locator'],'line:10:st.markdown')
        for n in (2,4,5,8,10):self.assertIsNone(catalog.for_document(rows[n]))
        self.assertIsNone(catalog.for_document({**rows[0],'source_kind':'notebook_markdown'}))

    def test_context_preserves_original_scores_when_lower(self):
        reranker=PassageReranker.__new__(PassageReranker)
        reranker.heading_catalog=Mock()
        reranker.heading_catalog.for_document.return_value={'text':'#### Original heading','locator':'line:1:st.markdown'}
        reranker.model=Mock();reranker.model.predict.return_value=np.array([.02])
        base={'whole_query':np.array([.09]),'relevance':np.array([.09])}
        result=reranker.add_heading_context('Question',[{'source_path':'a','text':'Body'}],base)
        self.assertEqual(result['whole_query'][0],.09)
        self.assertEqual(result['base_whole_query'][0],.09)
        self.assertEqual(result['heading_scores'][0],.02)
        self.assertEqual(base['whole_query'][0],.09)
        self.assertIn('Original heading',reranker.model.predict.call_args[0][0][0][1])

    def test_strong_passage_does_not_get_rescored(self):
        reranker=PassageReranker.__new__(PassageReranker)
        reranker.heading_catalog=Mock();reranker.model=Mock()
        base={'whole_query':np.array([.2]),'relevance':np.array([.2])}
        self.assertIs(reranker.add_heading_context('Q',[{}],base),base)
        reranker.model.predict.assert_not_called()

    def test_invalid_new_scores_rejected_and_original_not_mutated(self):
        for value in (float('nan'),1.1,-.1):
            reranker=PassageReranker.__new__(PassageReranker)
            reranker.heading_catalog=Mock();reranker.heading_catalog.for_document.return_value={'text':'# H'}
            reranker.model=Mock();reranker.model.predict.return_value=np.array([value])
            base={'whole_query':np.array([.02]),'relevance':np.array([.02])}
            with self.assertRaises(ValueError):reranker.add_heading_context('Q',[{'source_path':'a','text':'Body'}],base)
            self.assertEqual(base['whole_query'][0],.02)

    def test_missing_optional_catalog_keeps_original_reranking(self):
        reranker=PassageReranker.__new__(PassageReranker)
        base={'whole_query':np.array([.02]),'relevance':np.array([.02])}
        with patch('heading_context.AdjacentHeadings',side_effect=FileNotFoundError()):
            self.assertIs(reranker.add_heading_context('Q',[{}],base),base)

    def test_invalid_base_score_cannot_be_rescued_by_context(self):
        reranker=PassageReranker.__new__(PassageReranker)
        base={'whole_query':np.array([-.02]),'relevance':np.array([.02])}
        with self.assertRaises(ValueError):reranker.add_heading_context('Q',[{}],base)

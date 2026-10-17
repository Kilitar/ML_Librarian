import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/librarian'))
from semantic_layer import analyze, CONCEPTS


class SemanticTests(unittest.TestCase):
    def test_multilingual_concepts(self):
        for q in ('Co je přeučení?', 'What is overfitting?', 'Co to jest przeuczenie?'):
            self.assertEqual(analyze(q)['concept_id'], 'overfitting')

    def test_relations_are_not_synonyms(self):
        deep = analyze('Co je hluboké učení')
        neural = analyze('Co jsou neuronové sítě')
        self.assertNotEqual(deep['canonical_query'], neural['canonical_query'])
        self.assertIn({'type':'uses', 'target':'neural_networks'}, deep['relations'])
        self.assertFalse(neural['related_evidence_only'])

    def test_ambiguity_negation_and_complex_intent_are_preserved(self):
        for q in ('Co je ML', 'Co je regrese a klasifikace', 'Co není přeučení', 'Jak omezit přeučení?', 'Co je deep learning v medicíně'):
            self.assertIsNone(analyze(q))

    def test_acronyms_are_separate_from_aliases(self):
        self.assertIn('ML', CONCEPTS['machine_learning']['abbreviations'])
        self.assertNotIn('MLM', CONCEPTS['machine_learning']['abbreviations'])

    def test_experimental_rewrites_do_not_change_production(self):
        self.assertIsNone(analyze('Co je klasifikace', production_only=True))
        self.assertIsNotNone(analyze('Co je klasifikace'))
        self.assertIsNotNone(analyze('Co je přeučení', production_only=True))

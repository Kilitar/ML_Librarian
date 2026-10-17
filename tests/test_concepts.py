import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/librarian'))
from concepts import definition_query, concept_strength


class ConceptTests(unittest.TestCase):
    def test_equivalent_definitions(self):
        for q in ('Co je hluboké učení?', 'Co je deep learning', 'What is deep learning?', 'Czym jest głębokie uczenie?'):
            self.assertEqual(definition_query(q), 'What is deep learning?')

    def test_complex_intent_and_distinct_topics_unchanged(self):
        for q in ('Co je hluboké učení a kdy ho nepoužívat?', 'Co jsou neuronové sítě', 'Co je neřízené učení', 'kolik je hodin'):
            self.assertIsNone(definition_query(q))

    def test_explanation_above_mentions(self):
        self.assertGreater(concept_strength('Neuronové sítě obsahují skryté vrstvy s nelineárními aktivacemi.', 'neural_networks.md'),
                           concept_strength('Knihy: Deep Learning'))
        self.assertEqual(concept_strength('Shlukování je neřízené učení.'), 0)
        self.assertEqual(concept_strength('```\nNeural networks consists of hidden layers\n```'), 0)

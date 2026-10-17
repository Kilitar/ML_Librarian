import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/librarian'))
from acronyms import requested_acronym, exact_token, definition_strength


class AcronymTests(unittest.TestCase):
    def test_multilingual_questions(self):
        for query in ('Co znamená zkratka ML', 'What does ML stand for?', 'Co oznacza skrót ML?'):
            self.assertEqual(requested_acronym(query), 'ML')
        self.assertIsNone(requested_acronym('How does a model learn?'))

    def test_whole_token_not_similar_acronyms(self):
        self.assertFalse(exact_token('Masked Language Model (MLM)', 'ML'))
        self.assertFalse(exact_token('Maximum Likelihood Estimation (MLE)', 'ML'))
        self.assertTrue(exact_token('Machine Learning (ML)', 'ML'))

    def test_expansions_both_directions_and_translation(self):
        for text in ('Machine Learning (ML)', 'ML (Machine Learning)', '**Machine Learning (Strojové učení – ML)**'):
            self.assertEqual(definition_strength(text, 'ML'), 2)
        self.assertEqual(definition_strength('We use ML models.', 'ML'), 0)
        self.assertEqual(definition_strength('Training data for ML (Data Preprocessing)', 'ML'), 0)
        self.assertEqual(definition_strength('Masked Language Model (MLM)', 'ML'), -1)
        self.assertEqual(definition_strength('```text\nMACHINE LEARNING (ML)\n```', 'ML'), 1)


if __name__ == '__main__':
    unittest.main()

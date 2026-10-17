import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/librarian'))
from comparisons import comparison_aspects, coverage_order, aspect_query, approved_pair, comparison_context, contextual_score


class ComparisonTests(unittest.TestCase):
    def test_comparison_axis_requires_shared_reviewed_relation(self):
        context = comparison_context(comparison_aspects('Jaký je rozdíl mezi regresí a klasifikací?'))
        self.assertEqual(context['axis'], 'prediction_target')
        self.assertEqual(context['version'], 'domain-v2')
        self.assertEqual(len(context['vocabulary_sha256']),64)
        self.assertIn('the type of prediction target',context['query'])
        self.assertIsNone(comparison_context(['What is machine learning?','What is overfitting?']))
        self.assertIsNone(comparison_context(['What is regression?','What is regression?']))

    def test_joint_score_limits_one_strong_side(self):
        self.assertGreater(contextual_score(.3,.9,[.4,.4]), contextual_score(.3,.1,[.99,.001]))
    def test_multilingual_comparison_and_unchanged_noncomparison(self):
        for q in ('Jaký je rozdíl mezi regresí a klasifikací?', 'What is the difference between regression and classification?', 'Jaka jest różnica między regresją a klasyfikacją?'):
            self.assertEqual(len(comparison_aspects(q)), 2)
        for q in ('Co je regrese', 'kolik je hodin', 'What is machine learning?', 'difference between x and x'):
            self.assertEqual(comparison_aspects(q), [])

    def test_uncovered_side_is_selected_before_redundant_evidence(self):
        ranked = [0,1,2]
        scores = {0:[.95,.01],1:[.90,.02],2:[.01,.8]}
        self.assertEqual(coverage_order(ranked,scores,{0:.95,1:.9,2:.8})[:2],[0,2])

    def test_label_presence_does_not_reverse_learning_paradigms(self):
        self.assertEqual(aspect_query('uczenie z etykietami'), 'What is supervised learning?')
        self.assertEqual(aspect_query('szukania grup bez etykiet'), 'What is unsupervised learning?')
        self.assertEqual(aspect_query('learning without labels'), 'What is unsupervised learning?')
        self.assertEqual(aspect_query('price labels'), 'price labels')
        self.assertTrue(approved_pair(['What is supervised learning?', 'What is unsupervised learning?']))
        self.assertFalse(approved_pair(['regression','classification']))

    def test_no_forced_weak_side_and_joint_evidence_covers_both(self):
        self.assertEqual(coverage_order([0,1],{0:[.1,.1],1:[.1,.1]},{0:.8,1:.7}),[0,1])
        self.assertEqual(coverage_order([0,1],{0:[.9,.9],1:[.8,.1]},{0:.9,1:.8}),[0,1])

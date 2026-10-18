import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/librarian'))
from calibration_data import group_pairs,select_threshold,coverage


class CalibrationIntegrityTests(unittest.TestCase):
    def test_transitive_query_source_and_copy_connections_carry_fit_status(self):
        rows=[dict(query='Q1',source_path='A.md',text='alpha',fitted_versions=['v2']),
              dict(query=' q1 ',source_path='B.md',text='beta'),
              dict(query='Q2',source_path='b.MD',text='gamma'),
              dict(query='Q3',source_path='C.md',text='gamma'),
              dict(query='Q4',source_path='D.md',text='delta')]
        out=group_pairs(rows)
        self.assertEqual(len({r['component'] for r in out[:4]}),1)
        self.assertTrue(all(r['component_fitted_versions']==['v2'] for r in out[:4]))
        self.assertNotEqual(out[0]['component'],out[-1]['component'])
        self.assertEqual(out[-1]['role'],'calibration_candidate_development')

    def row(self,y,s):return {'role':'calibration','target':y,'score':s}

    def test_no_tied_score_can_separate_conflicting_labels(self):
        result=select_threshold([self.row(1,.8),self.row(0,.8)],min_recall=1,max_fpr=0)
        self.assertEqual(result['status'],'infeasible');self.assertIsNone(result['threshold'])

    def test_threshold_boundary_uses_greater_or_equal_and_preserves_recall(self):
        result=select_threshold([self.row(1,.9),self.row(1,.8),self.row(0,.7)])
        self.assertEqual(result['threshold'],.8);self.assertEqual(result['recall'],1)
        self.assertEqual(result['false_positives'],0)
        self.assertAlmostEqual(result['zero_fp_upper95_iid_diagnostic'],.95)

    def test_test_rows_fit_components_invalid_scores_and_single_class_are_rejected(self):
        for change in [{'role':'test_locked'},{'role':'fit_connected_development'},
                       {'component_fitted_versions':['v1']},{'score':float('nan')},
                       {'score':True},{'score':1.1},{'target':None}]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                select_threshold([{**self.row(1,.9),**change},self.row(0,.2)])
        with self.assertRaises(ValueError):select_threshold([self.row(1,.9)])

    def test_language_count_does_not_hide_missing_positive_class(self):
        rows=[dict(label='topic_only',language=l,family='x',component=l) for l in ('cs','en','pl')]
        rows.append(dict(label='direct',language='en',family='x',component='en'))
        result=coverage(rows,{'query_languages':3})
        self.assertEqual(result['minimum_shortfalls'],{})
        self.assertFalse(result['eligible']);self.assertEqual(result['language_class_gaps'],['cs','pl'])


if __name__=='__main__':unittest.main()

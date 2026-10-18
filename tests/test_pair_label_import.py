import sys
import unittest
from pathlib import Path
from copy import deepcopy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/librarian'))
from pair_label_import import validate_export,text_sha


def fixture(label=None):
    source={'rows':[{'id':'q1','query':'Question?','results':[{'chunk_id':'c1','text':'Body',
        'source_path':'a.md','locator':'line:1','heading_context':{'text':'# Heading'}}]}]}
    row={'key':'pair_0','question_id':'q1','query':'Question?','query_sha256':text_sha('Question?'),
         'chunk_id':'c1','rank':1,'source_path':'a.md','locator':'line:1','text_sha256':text_sha('Body'),
         'input_sha256':text_sha('# Heading\n\nBody'),'label':label,'note':''}
    export={'version':'answerability-pair-review-v3','pool':'calibration','frozen_raw_sha256':'bound','pairs':[row]}
    return source,export


class PairLabelImportTests(unittest.TestCase):
    def test_unreviewed_partial_and_unjudgeable_are_never_negative_training_labels(self):
        for label,target in [(None,None),('partial',None),('unjudgeable',None),('direct',1),('topic_only',0),('irrelevant',0)]:
            source,export=fixture(label)
            result=validate_export(export,source,'bound','calibration')[0]
            self.assertEqual(result['target'],target)
            self.assertEqual(result['review_status'],'unreviewed' if label is None else 'manual_export_unverified')

    def test_changed_query_passage_context_or_provenance_are_rejected(self):
        source,export=fixture('direct')
        for key in ['query','query_sha256','chunk_id','source_path','text_sha256','input_sha256','locator']:
            altered=deepcopy(export);altered['pairs'][0][key]='tampered'
            with self.subTest(key=key),self.assertRaises(ValueError):validate_export(altered,source,'bound','calibration')

    def test_old_schema_wrong_pool_stale_hash_and_bad_labels_are_rejected(self):
        source,export=fixture('direct')
        for key,value in [('version','answerability-pair-review-v1'),('version','answerability-pair-review-v2'),('pool','original'),('frozen_raw_sha256','old')]:
            with self.subTest(key=key),self.assertRaises(ValueError):validate_export({**export,key:value},source,'bound','calibration')
        export['pairs'][0]['label']='supported'
        with self.assertRaises(ValueError):validate_export(export,source,'bound','calibration')

    def test_missing_extra_and_duplicate_pair_records_are_rejected(self):
        source,export=fixture()
        for pairs in [[],export['pairs']*2]:
            with self.assertRaises(ValueError):validate_export({**export,'pairs':pairs},source,'bound','calibration')


if __name__=='__main__':unittest.main()

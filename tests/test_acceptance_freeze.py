import sys,json,hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/librarian'))
import evaluate_acceptance
import score_acceptance


class AcceptanceFreezeTests(unittest.TestCase):
    def test_frozen_results_cannot_be_overwritten_or_reload_model(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'eval').mkdir()
            path=root/'eval/acceptance_v1_results.local.json';path.write_text('frozen',encoding='utf-8')
            with patch.object(evaluate_acceptance,'ROOT',root),patch.object(evaluate_acceptance.E5SearchIndex,'load') as loader:
                with self.assertRaises(FileExistsError):evaluate_acceptance.main()
                loader.assert_not_called()
            self.assertEqual(path.read_text(encoding='utf-8'),'frozen')

    def test_changed_criteria_are_rejected_before_source_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'eval').mkdir()
            (root/'eval/acceptance_v1_questions.json').write_text('{}',encoding='utf-8')
            (root/'eval/acceptance_v1_results.local.json').write_text(json.dumps({'questions_sha256':'old'}),encoding='utf-8')
            (root/'eval/acceptance_v1_judgments.json').write_text('{}',encoding='utf-8')
            with patch.object(score_acceptance,'ROOT',root),patch.object(score_acceptance,'SourceCatalog') as catalog:
                with self.assertRaises(ValueError):score_acceptance.main()
                catalog.assert_not_called()

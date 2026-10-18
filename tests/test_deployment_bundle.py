import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/librarian'))
from deployment_bundle import build,install,sha


class DeploymentBundleTests(unittest.TestCase):
    def bundle(self):
        directory=tempfile.TemporaryDirectory();root=Path(directory.name)
        for name,text in {'data/normalized/chunks_curated.jsonl':'{}','data/normalized/documents.jsonl':'{}',
          'data/index/multilingual_e5_curated.json':json.dumps({'index_file':'multilingual_e5_curated_fixture.npy'}),
          'data/index/multilingual_e5_curated_fixture.npy':'test-matrix'}.items():
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
        return directory,build(root)

    def test_roundtrip_and_no_unallowlisted_payload(self):
        fixture,data=self.bundle()
        with fixture,tempfile.TemporaryDirectory() as target:
            manifest=install(data,sha(data),Path(target))
            self.assertEqual(len(manifest),4)
            self.assertTrue((Path(target)/'data/normalized/documents.jsonl').exists())
            self.assertFalse((Path(target)/'.streamlit').exists())

    def test_bad_sha_rejects_before_writing(self):
        fixture,data=self.bundle()
        with fixture,tempfile.TemporaryDirectory() as target:
            with self.assertRaises(ValueError):install(data,'0'*64,Path(target))
            self.assertFalse(list(Path(target).iterdir()))

    def test_traversal_and_duplicate_members_rejected(self):
        for name in ['../outside','data/index/../../outside','.streamlit/secrets.toml']:
            out=io.BytesIO()
            with zipfile.ZipFile(out,'w') as z:
                z.writestr(name,'payload');z.writestr('bundle_manifest.json',json.dumps({name:sha(b'payload')}))
            data=out.getvalue()
            with tempfile.TemporaryDirectory() as target:
                with self.assertRaises(ValueError):install(data,sha(data),Path(target))
                self.assertFalse(list(Path(target).iterdir()))

    def test_corrupt_member_rejected(self):
        fixture,data=self.bundle()
        with fixture,zipfile.ZipFile(io.BytesIO(data)) as source:
            out=io.BytesIO()
            with zipfile.ZipFile(out,'w') as dest:
                for name in source.namelist():dest.writestr(name,b'changed' if name.endswith('documents.jsonl') else source.read(name))
        data=out.getvalue()
        with tempfile.TemporaryDirectory() as target:
            with self.assertRaises(ValueError):install(data,sha(data),Path(target))
            self.assertFalse(list(Path(target).iterdir()))

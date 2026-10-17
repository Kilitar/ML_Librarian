import sys,json,hashlib,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/librarian'))
from source_viewer import SourceCatalog,relative_source,initial_part
from unittest.mock import patch


class SourceViewerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.snapshot=self.root/'snapshot';self.snapshot.mkdir()
        self.data=b'# Full original source\n';(self.snapshot/'note.md').write_bytes(self.data)
        self.docs=self.root/'documents.jsonl'
        self.docs.write_text('\n'.join(json.dumps(dict(source_path='note.md',locator=f'page:{i}',text=f'Text {i}')) for i in (1,2)),encoding='utf-8')
        self.manifest=self.root/'manifest.json'
        self.manifest.write_text(json.dumps([dict(path='note.md',bytes=len(self.data),sha256=hashlib.sha256(self.data).hexdigest().upper())]),encoding='utf-8')
        self.catalog=SourceCatalog(self.docs)

    def test_full_parts_and_initial_locator(self):
        parts=self.catalog.parts('note.md')
        self.assertEqual(len(parts),2)
        self.assertEqual(initial_part(parts,'page:2'),1)
        self.assertEqual(initial_part(parts,'unknown'),0)

    def test_original_bytes_require_matching_hash(self):
        self.assertEqual(self.catalog.original('note.md',snapshot=self.snapshot,manifest=self.manifest),self.data)
        (self.snapshot/'note.md').write_bytes(b'changed')
        with self.assertRaises(ValueError):self.catalog.original('note.md',snapshot=self.snapshot,manifest=self.manifest)

    def test_paths_and_noncorpus_sources_rejected(self):
        for value in ('../note.md','C:/secret.txt','//server/file','a/../note.md','note.md:stream','/secret.txt'):
            with self.assertRaises(ValueError):relative_source(value)
        with self.assertRaises(ValueError):self.catalog.parts('unknown.md')

    def test_manifest_entry_required(self):
        self.manifest.write_text('[]',encoding='utf-8')
        with self.assertRaises(ValueError):self.catalog.original('note.md',snapshot=self.snapshot,manifest=self.manifest)

    def test_resolved_file_escape_is_rejected(self):
        outside=self.root/'outside.md';outside.write_bytes(self.data)
        resolve=Path.resolve
        def redirected(path,*args,**kwargs):
            return outside if path.name=='note.md' else resolve(path,*args,**kwargs)
        with patch.object(Path,'resolve',autospec=True,side_effect=redirected):
            with self.assertRaises(ValueError):self.catalog.original('note.md',snapshot=self.snapshot,manifest=self.manifest)

    def test_download_size_limit(self):
        with patch('source_viewer.MAX_DOWNLOAD',1):
            with self.assertRaises(ValueError):self.catalog.original('note.md',snapshot=self.snapshot,manifest=self.manifest)

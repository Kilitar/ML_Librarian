import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/librarian'))
from course_links import source_pages, course_link_info, RELATED_PAGES
from unittest.mock import patch

class CourseLinkTests(unittest.TestCase):
    def test_only_registered_pages_and_existing_literal_sources_are_linked(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'views').mkdir();(root/'theory').mkdir()
            (root/'theory/topic.md').write_text('Theory')
            (root/'lesson.ipynb').write_text('{}')
            (root/'app.py').write_text('import streamlit as st\na=st.Page("views/a.py")\nb=st.Page("views/unused.py")\nnav=st.navigation({"Course":[a]})')
            (root/'views/a.py').write_text('from pathlib import Path\nbase_dir=Path(__file__).resolve().parent.parent\nfolder=base_dir / "theory"\nfile=folder / "topic.md"\nnotebook="lesson.ipynb"\nmissing="missing.pdf"\nraise RuntimeError("Must never execute course pages")')
            (root/'views/unused.py').write_text('unused="other.md"')
            links=source_pages(str(root))
            self.assertEqual(links,{'views/a.py':'views/a.py','theory/topic.md':'views/a.py','lesson.ipynb':'views/a.py'})
            self.assertNotIn('../outside.md',links)

    def test_related_link_requires_registered_target(self):
        source=next(iter(RELATED_PAGES));target=RELATED_PAGES[source]
        with patch('course_links.source_pages',return_value={target:target}):
            info=course_link_info({'source_path':source},'unused')
            self.assertEqual(info['page'],target)
            self.assertEqual(info['label'],'Související stránka kurzu')
        with patch('course_links.source_pages',return_value={}):
            self.assertIsNone(course_link_info({'source_path':source},'unused')['page'])

    def test_pdf_and_its_text_extract_explain_missing_original(self):
        for source in [{'source_path':'Resources/PDF/course.pdf'},
                       {'source_path':'Resources/Day 0 Prework PDF/10-Data_preparation.txt'},
                       {'source_path':'notes.txt','source_origin':'Coderslab PDF'}]:
            with self.subTest(source=source),patch('course_links.source_pages') as mapping:
                info=course_link_info(source,'unused')
                self.assertIsNone(info['page'])
                self.assertIn('Coders Lab',info['notice'])
                self.assertIn('nejsou veřejně dostupné',info['notice'])
                mapping.assert_not_called()

if __name__=='__main__':unittest.main()

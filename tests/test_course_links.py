import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/librarian'))
from course_links import source_pages

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

if __name__=='__main__':unittest.main()

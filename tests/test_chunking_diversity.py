import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/librarian'))
from chunk_text import split_text
from diversify import content_key, select_distinct
from constraints import query_constraints


class EvidenceTests(unittest.TestCase):
    def test_fenced_whitespace_and_blank_lines_survive(self):
        block = '```text\n    ┌────┐     ┌────┐\n    │ A  │ ──>│ B  │\n\n                  v\n```'
        chunks = split_text('Before\n\n' + block + '\n\nAfter', max_chars=40)
        self.assertIn(block, chunks)
        self.assertTrue(all(c.count('```') % 2 == 0 for c in chunks))

    def test_code_indentation_is_not_collapsed(self):
        block = '~~~python\nif True:\n    x = 1\n        # indentation\n~~~'
        self.assertIn(block, '\n\n'.join(split_text(block)))

    def test_duplicates_never_return_even_in_fallback(self):
        docs = [{'source_path': 'a', 'text': 'same text'},
                {'source_path': 'b', 'text': 'same  text'},
                {'source_path': 'a', 'text': 'distinct content'}]
        self.assertEqual(select_distinct(docs, [0, 1, 2], 5), [0, 2])
        self.assertNotEqual(content_key('alpha = 1'), content_key('alpha = 2'))
        self.assertNotEqual(content_key('```python\nif x:\n    run()\n```'),
                            content_key('```python\nif x:\nrun()\n```'))

    def test_polish_kmeans(self):
        self.assertEqual(query_constraints('Kiedy należy zastosować metodę k-średnich')['algorithm'], {'kmeans'})


if __name__ == '__main__':
    unittest.main()

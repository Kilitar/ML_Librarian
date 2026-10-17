import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/librarian'))
from snippet_format import format_snippet


class SnippetTests(unittest.TestCase):
    def test_reported_html_wrapper_is_not_visible(self):
        source = '<div class="sub-header">Interaktivní webová platforma (Coderslab 2026).</div>'
        self.assertEqual(format_snippet(source), 'Interaktivní webová platforma (Coderslab 2026).')

    def test_visible_structure_survives_without_styles_or_scripts(self):
        source = '<style>.x{color:red}</style><h2>Nadpis</h2><p><strong>Text</strong><br>Další</p><script>alert(1)</script>'
        self.assertEqual(format_snippet(source), '## Nadpis\n\n**Text**\nDalší')

    def test_code_and_diagram_whitespace_survive(self):
        for fence in ('```', '~~~'):
            code = fence + 'html\n    <div class="x">&#x20;</div>\n' + fence
            self.assertEqual(format_snippet(code), code)
        self.assertEqual(format_snippet('`<div>raw</div>`'), '`<div>raw</div>`')

    def test_math_and_inequalities_remain(self):
        self.assertEqual(format_snippet(r'\(x < y\)'), '$x < y$')
        self.assertEqual(format_snippet(r'\\(y = ax + b\\)'), '$y = ax + b$')
        self.assertEqual(format_snippet('A &amp; B'), 'A & B')


if __name__ == '__main__':
    unittest.main()

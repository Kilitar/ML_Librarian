"""Presentation-only normalization of source excerpts for Streamlit Markdown."""
import html
import re
from html.parser import HTMLParser
from chunk_text import FENCE


class _ReadableHTML(HTMLParser):
    """Extract visible content; never enable source HTML/CSS execution."""
    blocks = {'div', 'p', 'section', 'article', 'header', 'footer', 'ul', 'ol', 'table', 'tr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}:
            self.hidden += 1
        elif not self.hidden:
            if tag in self.blocks:
                self.output.append('\n\n')
            elif tag in {'br', 'hr'}:
                self.output.append('\n')
            elif tag == 'li':
                self.output.append('\n- ')
            elif tag in {'strong', 'b'}:
                self.output.append('**')
            elif tag in {'em', 'i'}:
                self.output.append('*')
            elif re.fullmatch('h[1-6]', tag):
                self.output.append('\n\n' + '#' * int(tag[1]) + ' ')
            elif tag in {'td', 'th'}:
                self.output.append(' | ')
            elif tag == 'img':
                self.output.append(dict(attrs).get('alt') or '')
            elif tag not in {'span', 'a', 'small', 'label', 'sup', 'sub'}:
                self.output.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if tag in {'script', 'style'}:
            self.hidden = max(0, self.hidden - 1)
        elif not self.hidden:
            if tag in self.blocks or re.fullmatch('h[1-6]', tag):
                self.output.append('\n\n')
            elif tag in {'strong', 'b'}:
                self.output.append('**')
            elif tag in {'em', 'i'}:
                self.output.append('*')

    def handle_data(self, data):
        if not self.hidden:
            self.output.append(data)


def _format_prose(text: str) -> str:
    # Inline code is evidence too: do not strip its literal HTML examples.
    parts = re.split(r'(`[^`\n]+`)', text)
    for index in range(0, len(parts), 2):
        part = html.unescape(parts[index])
        parser = _ReadableHTML()
        parser.feed(part)
        parser.close()
        part = ''.join(parser.output)
        part = re.sub(r'\n{3,}', '\n\n', part)
        part = re.sub(r"\\{1,2}\((.*?)\\{1,2}\)", lambda m: "$" + m[1] + "$", part, flags=re.S)
        part = re.sub(r"\\{1,2}\[(.*?)\\{1,2}\]", lambda m: "\n\n$$\n" + m[1] + "\n$$\n\n", part, flags=re.S)
        parts[index] = part
    return ''.join(parts)


def format_snippet(text: str) -> str:
    parts = []
    position = 0
    for match in FENCE.finditer(text):
        parts.extend((_format_prose(text[position:match.start()]), match.group()))
        position = match.end()
    parts.append(_format_prose(text[position:]))
    return ''.join(parts).strip()

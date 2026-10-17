"""Source-local adjacent headings from static extraction, never generated text."""
import hashlib
import json
import re
from pathlib import Path

VERSION = 'adjacent-heading-v2'
DOCUMENTS = Path(__file__).resolve().parents[2] / 'data/normalized/documents.jsonl'
LINE = re.compile(r'^line:(\d+):st\.\w+$')
HEADING = re.compile(r'^#{1,6}\s+[^\n\r]{1,230}$')


class AdjacentHeadings:
    def __init__(self, path=DOCUMENTS, *, allow_formula=True):
        data=Path(path).read_bytes()
        self.sha256=hashlib.sha256(data).hexdigest()
        sources={}
        for line in data.decode('utf-8').splitlines():
            row=json.loads(line)
            match=LINE.fullmatch(row.get('locator',''))
            if row.get('source_kind')=='streamlit_literal' and match:
                sources.setdefault(row['source_path'],[]).append((int(match[1]),row))
        self.contexts={}
        for path, parts in sources.items():
            parts.sort(key=lambda p:p[0])  # AST traversal order is not source order.
            for position,((previous_line,previous),(current_line,current)) in enumerate(zip(parts,parts[1:]),1):
                bridge=None
                if allow_formula and previous['locator'].endswith(':st.latex') and position>=2:
                    heading_line,heading=parts[position-2]
                    if 1<=previous_line-heading_line<=2 and 1<=current_line-previous_line<=2:
                        bridge=previous['locator'];previous_line,previous=heading_line,heading
                text=previous.get('text','').strip()
                if (1<=current_line-previous_line<=3 and HEADING.fullmatch(text)
                        and not HEADING.fullmatch(current.get('text','').strip())):
                    self.contexts[path,current['locator']]={'text':text,'locator':previous['locator'],
                        'source_path':path,'catalog_sha256':self.sha256,
                        'version':VERSION if allow_formula else 'adjacent-heading-v1',
                        'intervening_formula_locator':bridge}

    def for_document(self, document):
        if document.get('source_kind')!='streamlit_literal':
            return None
        return self.contexts.get((document['source_path'],document.get('locator')))

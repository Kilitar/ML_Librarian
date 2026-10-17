"""Suppress repeated evidence without deleting source records."""
import unicodedata
from chunk_text import FENCE


def content_key(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    parts = []
    position = 0
    for match in FENCE.finditer(text):
        parts.append(" ".join(text[position:match.start()].split()))
        # Indentation and case can change code semantics; keep both verbatim.
        parts.append(match.group().rstrip("\n"))
        position = match.end()
    parts.append(" ".join(text[position:].split()))
    return "\n".join(parts)


def select_distinct(documents: list[dict], ranked: list[int], limit: int) -> list[int]:
    selected = []
    sources = set()
    contents = set()
    for distinct_sources in (True, False):
        for index in ranked:
            document = documents[index]
            key = content_key(document["text"])
            source = document["source_path"]
            if key in contents or (distinct_sources and source in sources):
                continue
            selected.append(index)
            sources.add(source)
            contents.add(key)
            if len(selected) == limit:
                return selected
    return selected

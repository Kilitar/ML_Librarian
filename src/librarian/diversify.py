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


def select_distinct(documents: list[dict], ranked: list[int], limit: int,
                    max_per_source: int = 1) -> list[int]:
    selected = []
    sources = {}
    contents = set()
    for source_cap in (max_per_source, None):
        for index in ranked:
            document = documents[index]
            key = content_key(document["text"])
            source = document["source_path"]
            if key in contents or (source_cap is not None and sources.get(source, 0) >= source_cap):
                continue
            selected.append(index)
            sources[source] = sources.get(source, 0) + 1
            contents.add(key)
            if len(selected) == limit:
                return selected
    return selected

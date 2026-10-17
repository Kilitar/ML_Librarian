"""Chunk prose while preserving fenced code and ASCII diagram whitespace."""
import re

FENCE = re.compile(r"(?ms)^ {0,3}(`{3,}|~{3,})[^\n]*\n.*?^ {0,3}\1[ \t]*(?:\n|$)")


def split_text(text: str, max_chars: int = 1100, overlap: int = 140) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    units = []
    position = 0
    for match in FENCE.finditer(text):
        units.append((text[position:match.start()], False))
        units.append((match.group().rstrip("\n"), True))
        position = match.end()
    units.append((text[position:], False))
    paragraphs = []
    for content, fenced in units:
        if fenced:
            paragraphs.append((content, True))
        else:
            content = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", content)
            content = re.sub(r"[ \t]+", " ", content)
            paragraphs.extend((p.strip(), False) for p in re.split(r"\n\s*\n", content) if p.strip())
    chunks = []
    current = ""
    for paragraph, fenced in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            if fenced:
                chunks.append(paragraph)
                continue
            start = 0
            while start < len(paragraph):
                end = min(len(paragraph), start + max_chars)
                if end < len(paragraph):
                    cut = paragraph.rfind(" ", start, end)
                    if cut > start + max_chars // 2:
                        end = cut
                chunks.append(paragraph[start:end].strip())
                if end == len(paragraph):
                    break
                start = max(start + 1, end - overlap)
        elif len(current) + len(paragraph) + 2 <= max_chars:
            current = (current + "\n\n" + paragraph).strip()
        else:
            if current:
                chunks.append(current)
            current = paragraph
    if current:
        chunks.append(current)
    return chunks

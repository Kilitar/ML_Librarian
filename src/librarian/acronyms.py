"""Recognize explicit acronym questions and source-local expansion evidence."""
import re
from constraints import normalize
from chunk_text import FENCE
from snippet_format import format_snippet


def requested_acronym(query: str) -> str | None:
    text = normalize(query)
    patterns = (
        r'(?:zkratk\w*|abbreviation|acronym|skrot\w*)\s+([a-z][a-z0-9]{1,9})\b',
        r'\b([a-z][a-z0-9]{1,9})\s+stand\s+for\b',
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).upper()
    return None


def exact_token(text: str, acronym: str) -> bool:
    return re.search(r'(?<!\w)' + re.escape(acronym) + r'(?!\w)', text, re.I) is not None


def definition_strength(text: str, acronym: str) -> int:
    visible = format_snippet(text)
    if not exact_token(visible, acronym):
        return -1
    prose = FENCE.sub('', visible)

    def expanded(content):
        escaped = re.escape(acronym)
        def initials_match(phrase, suffix=False):
            words = re.findall(r'[^\W\d_]+', phrase, re.U)
            if suffix:
                words = words[-len(acronym):]
            return len(words) >= 2 and ''.join(w[0] for w in words).upper() == acronym
        # Expansion (ACR), including translated variants: Machine Learning
        # (Strojové učení – ML). Require words beyond the acronym itself.
        for match in re.finditer(r'([^\n()]{2,120})\(([^\n()]{0,100})\)', content):
            before, parenthesis = match.groups()
            if (re.search(r'\b' + escaped + r'\s*$', parenthesis, re.I)
                    and initials_match(before, suffix=True)):
                return True
            if (re.search(r'\b' + escaped + r'\s*$', before, re.I)
                    and initials_match(parenthesis)):
                return True
        return False

    if expanded(prose):
        return 2
    return 1 if expanded(visible) else 0

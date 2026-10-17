"""Bounded comparison decomposition; original query always retains its own score."""
import re
from constraints import normalize
from semantic_layer import analyze


def aspect_query(aspect):
    """Use reviewed names, or explicit label-presence cues for learning paradigms."""
    plan = analyze('What is ' + aspect)
    if plan:
        return plan['canonical_query']
    learning_context = re.search(r'ucen\w*|uczen\w*|learning|groups?|grup\w*|skup\w*', aspect)
    if learning_context:
        if re.search(r'(?:bez|without|no) (?:etykiet\w*|label\w*|stitk\w*)', aspect):
            return 'What is unsupervised learning?'
        if re.search(r'(?:z|s|with) (?:etykiet\w*|label\w*|stitk\w*)', aspect):
            return 'What is supervised learning?'
    return aspect


def comparison_aspects(query):
    text = normalize(query)
    patterns = (
        r'.*\bdifference between (.+?) and (.+)',
        r'.*\brozdil mezi (.+?) a (.+)',
        r'.*\broznica miedzy (.+?) a (.+)',
        r'.*\brozni sie (.+?) od (.+)',
        r'.*\bdoes (.+?) differ from (.+)',
        r'.*\bje to (.+?) nebo (.+)',
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, text)
        if match:
            aspects = list(match.groups())
            if all(2 <= len(a) <= 100 for a in aspects) and aspects[0] != aspects[1]:
                return [aspect_query(a) for a in aspects]
    return []


def approved_pair(aspects):
    return len(aspects) == 2 and set(aspects) == {
        'What is supervised learning?', 'What is unsupervised learning?'}


def coverage_order(ranked, aspect_scores, ranking_scores):
    """Prefer evidence for an uncovered side, without forcing low-score matches."""
    pending = list(ranked)
    covered = set()
    output = []
    while pending:
        def priority(index):
            values = aspect_scores[index]
            missing = [float(v) for i,v in enumerate(values) if i not in covered and v >= .20]
            return (bool(missing), max(missing, default=0), ranking_scores[index])
        best = max(pending, key=priority) if len(covered) < 2 else pending[0]
        output.append(best)
        covered.update(i for i,v in enumerate(aspect_scores[best]) if v >= .20)
        pending.remove(best)
    return output

"""Bounded comparison decomposition; original query always retains its own score."""
import re
from constraints import normalize
from semantic_layer import analyze, CONCEPTS, REGISTRY, VERSION, FINGERPRINT
import math


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


def comparison_context(aspects):
    plans = [analyze(a) for a in aspects]
    if len(plans) != 2 or not all(plans):
        return None
    concepts = [CONCEPTS[p['concept_id']] for p in plans]
    axes = set(concepts[0].get('comparison_axes', [])) & set(concepts[1].get('comparison_axes', []))
    if not axes or concepts[0]['id'] == concepts[1]['id']:
        return None
    axis = sorted(axes)[0]
    return {'axis':axis, 'version':VERSION, 'vocabulary_sha256':FINGERPRINT,
            'query':f"How do {concepts[0]['label']} and {concepts[1]['label']} differ in {REGISTRY['comparison_axes'][axis]}?"}


def contextual_score(whole, context, aspects):
    """Fixed blend; a single strong side cannot dominate joint comparison."""
    joint = math.sqrt(max(0, float(aspects[0])) * max(0, float(aspects[1])))
    return .50 * float(context) + .25 * float(whole) + .25 * joint


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

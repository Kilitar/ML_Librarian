"""Conservative display grouping; never delete/reorder retrieved evidence."""
import math
import re
from semantic_layer import analyze, CONCEPTS
from constraints import normalize
from snippet_format import format_snippet
from chunk_text import FENCE
from rerank import REVISION

MIN_CONTEXT = .25  # Display heuristic only, not calibrated confidence.


def mentions(text, concept_id):
    prose = normalize(FENCE.sub('', format_snippet(text)))
    return any(re.search(r'\b'+re.escape(normalize(alias))+r'\b', prose)
               for aliases in CONCEPTS[concept_id]['aliases'].values() for alias in aliases)


def partition_results(results, status):
    numbered = list(enumerate(results, 1))
    if status != 'supported' or not results:
        return numbered, []
    context = results[0].get('comparison_context')
    aspects = results[0].get('comparison_aspects', [])
    if not context or context.get('axis') != 'prediction_target' or len(aspects) != 2:
        return numbered, []
    plans = [analyze(a) for a in aspects]
    if not all(plans) or plans[0]['concept_id'] == plans[1]['concept_id']:
        return numbered, []
    concepts = [p['concept_id'] for p in plans]
    for result in results:
        score = result.get('context_score')
        if (result.get('comparison_context') != context or result.get('retrieval_mode') != 'rerank'
                or result.get('reranker_revision') != REVISION or not isinstance(score, (int,float))
                or not math.isfinite(score) or not 0 <= score <= 1):
            return numbered, []
    if results[0]['context_score'] < MIN_CONTEXT or not all(mentions(results[0]['text'], c) for c in concepts):
        return numbered, []  # First passage may need a complementary second side.
    primary, additional = [], []
    for rank,result in numbered:
        keep = rank == 1 or (result['context_score'] >= MIN_CONTEXT and all(mentions(result['text'],c) for c in concepts))
        (primary if keep else additional).append((rank,result))
    return primary, additional

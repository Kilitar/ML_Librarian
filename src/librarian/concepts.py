"""Bounded multilingual concept aliases; no answer text or source IDs."""
import re
from constraints import normalize
from snippet_format import format_snippet
from chunk_text import FENCE
from semantic_layer import analyze

DEEP = r'(?:deep learning\w*|hlubok\w* ucen\w*|glebok\w* uczen\w*)'


def definition_query(query):
    """Canonicalize only a simple definition request, preserving complex intent."""
    plan = analyze(query)
    return plan['canonical_query'] if plan else None


def concept_strength(text, context=''):
    prose = normalize(FENCE.sub('', format_snippet(text)))
    topic = bool(re.search(r'\b' + DEEP + r'\b', prose))
    neural = bool(re.search(r'neuron\w* sit\w*|neural networks?|sieci\w* neuron\w*', prose))
    layers = bool(re.search(r'vrstv\w*|layers?|warstw\w*', prose))
    # Explain neural architecture as related evidence, never as an exact alias.
    explanatory = bool(re.search(r'obsahuje|jsou|pouziva|sklada|consists|hidden|skryt\w*|nelinear\w*', prose))
    neural_context = bool(re.search(r'neural.network|neuron\w*.sit', normalize(context)))
    if neural and layers and explanatory and (topic or neural_context):
        return 3 if topic else 2
    return 1 if topic else 0

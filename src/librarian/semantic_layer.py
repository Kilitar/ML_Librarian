"""Reviewed domain vocabulary, separate from learned retrieval and evidence."""
import hashlib
import json
import re
from pathlib import Path
from constraints import normalize

VOCABULARY = Path(__file__).with_name('domain_concepts.json')
_raw = VOCABULARY.read_bytes()
REGISTRY = json.loads(_raw)
VERSION = REGISTRY['version']
FINGERPRINT = hashlib.sha256(_raw).hexdigest()
CONCEPTS = {c['id']: c for c in REGISTRY['concepts']}
ALIASES = {}
for concept in CONCEPTS.values():
    for axis in concept.get('comparison_axes', []):
        if axis not in REGISTRY.get('comparison_axes', {}):
            raise ValueError('Unknown comparison axis')
    for aliases in concept['aliases'].values():
        for alias in aliases:
            key = normalize(alias)
            if key in ALIASES and ALIASES[key] != concept['id']:
                raise ValueError('Ambiguous domain alias: ' + alias)
            ALIASES[key] = concept['id']
    for relation in concept['relations']:
        if relation['target'] not in CONCEPTS:
            raise ValueError('Unknown relation target')


PRODUCTION_CONCEPTS = frozenset({'deep_learning', 'machine_learning', 'neural_networks', 'overfitting'})


def analyze(query, *, production_only=False):
    text = normalize(query)
    match = re.fullmatch(r'(?:co je|co jsou|co znamena|what is|what are|czym jest|czym sa|co to jest) (.+)', text)
    concept_id = ALIASES.get(match[1]) if match else None
    if not concept_id:
        return None
    if production_only and concept_id not in PRODUCTION_CONCEPTS:
        return None
    concept = CONCEPTS[concept_id]
    return {'version': VERSION, 'vocabulary_sha256': FINGERPRINT,
            'concept_id': concept_id, 'intent': 'definition',
            'production_enabled': concept_id in PRODUCTION_CONCEPTS,
            'canonical_query': ('What are ' if concept_id == 'neural_networks' else 'What is ') + concept['label'] + '?',
            'relations': concept['relations'],
            'related_evidence_only': concept.get('related_evidence_only', False)}

"""Server-only presentation config, no visitor key fields or paid-provider fallback."""
import os
from answer_generation import GenerationError, generate_answer

DEFAULT_MODEL = 'qwen/qwen3.8-27b'


def demo_config(secrets=None, environ=None):
    env = os.environ if environ is None else environ
    # Explicit supplied mapping makes tests independent from machine credentials.
    key = env.get('GROQ_API_KEY', '')
    model = env.get('GROQ_MODEL', DEFAULT_MODEL)
    if secrets is not None:
        try:
            key = secrets.get('GROQ_API_KEY', key)
            model = secrets.get('GROQ_MODEL', model)
        except (FileNotFoundError, KeyError):
            pass
    return {'api_key':key, 'model':model, 'provider':'groq'}


def generate_demo_answer(query, results, evidence, config, *, consent=False):
    if not config.get('api_key'):
        raise GenerationError('Generování prezentace zatím není nakonfigurované provozovatelem. Vyhledávání funguje bez omezení.')
    return generate_answer(query, results, evidence, config['api_key'], config['model'],
        consent=consent, provider='groq')

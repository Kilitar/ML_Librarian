"""Rank-only fallback when every candidate has weak whole-question evidence."""
import numpy as np

VERSION = 'weak-fusion-v2'


def weak_fusion(semantic, relevance, whole_query):
    """Return RRF scores or None; never create/modify evidence scores.

    The .10 boundary is the existing no-support boundary: all candidate scores
    below it implies every possible returned subset also stays below it. Missing,
    malformed, nonfinite or out-of-range model output cannot activate fusion.
    Two equal votes, k=60; source priors do not swamp small cosine differences.
    """
    arrays = [np.asarray(a, dtype=float) for a in (semantic, relevance, whole_query)]
    if (any(a.ndim != 1 or a.shape != arrays[0].shape or not np.isfinite(a).all() for a in arrays)
            or not len(arrays[0]) or any(np.any((a < 0) | (a > 1)) for a in arrays[1:])
            or np.max(arrays[2]) >= .10):
        return None
    fused = np.zeros(len(arrays[0]))
    for values in arrays[:2]:
        order = np.argsort(-values, kind='stable')
        fused[order] += 61 / (2 * (60 + np.arange(1, len(order) + 1)))
    return fused

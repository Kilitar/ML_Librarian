"""Conservative, versioned evidence availability signal, not answer verification."""
import math
from rerank import REVISION
from constraints import normalize
from domain_guard import outside_domain

POLICY_VERSION = "evidence-v5"
LOW_SUPPORT = 0.10
SUFFICIENT_SUPPORT = 0.20


def assess_evidence(results: list[dict], query: str = "") -> dict:
    if normalize(query) in {"jak to funguje", "co je lepsi", "how does it work", "which is better",
                            "jak to dziala", "co wybrac", "proc", "why", "dlaczego"}:
        return {"status": "uncertain", "policy": POLICY_VERSION, "score": None, "reason": "ambiguous_query"}
    if not results:
        return {"status": "no_support", "policy": POLICY_VERSION, "score": None}
    scores = []
    for result in results:
        value = result.get("whole_query_score")
        if (result.get("retrieval_mode") != "rerank" or result.get("reranker_revision") != REVISION
                or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1):
            return {"status": "unassessed", "policy": POLICY_VERSION, "score": None}
        scores.append(value)
    best = max(scores)
    if (best < SUFFICIENT_SUPPORT and results[0].get('comparison_aspects')
            and all(any(len(r.get('aspect_scores', [])) == 2 and r['aspect_scores'][i] >= .20
                        for r in results) for i in range(2))):
        return {"status": "uncertain", "policy": POLICY_VERSION, "score": best,
                "reason": "comparison_partial_evidence"}
    if any(r.get('related_evidence_only') for r in results):
        return {"status": "uncertain", "policy": POLICY_VERSION, "score": best,
                "reason": "related_concept_evidence"}
    if any(result.get('requested_acronym') and result.get('acronym_definition') for result in results):
        return {"status": "supported", "policy": POLICY_VERSION, "score": best, "reason": "explicit_acronym_definition"}
    if LOW_SUPPORT<=best<SUFFICIENT_SUPPORT and outside_domain(results,query):
        return {"status":"no_support","policy":POLICY_VERSION,"score":best,
                "reason":"out_of_domain_grey_band","domain_score":results[0]['domain_signal']['score']}
    status = "supported" if best >= SUFFICIENT_SUPPORT else "uncertain" if best >= LOW_SUPPORT else "no_support"
    return {"status": status, "policy": POLICY_VERSION, "score": best}

"""Bounded evidence coverage for explicit precision/recall priority questions."""
import re
from constraints import normalize

VERSION='metric-choice-v1'
ERRORS={'precision':('false positives','FP'),'recall':('false negatives','FN')}


def plan(query):
    text=normalize(query)
    if set(text.split()) & {'not','never','neni','ne','nie','nikdy'}:
        return None
    patterns=[
        r'\b(precision|recall)\s+(?:is\s+|jest\s+)?(?:more important|dulezitejsi|prednejsi|wazniejsza|wazniejszy|istotniejsza)\s+(?:than|nez|od|niz)\s+(precision|recall)\b',
        r'\b(?:prefer|prioritize|prioritise|favor|favour)\s+(precision|recall)\s+(?:over|to|rather than)\s+(precision|recall)\b',
    ]
    for pattern in patterns:
        match=re.search(pattern,text)
        if not match or match[1]==match[2]:continue
        context=re.fullmatch(r'\s+(?:in|for|with|pri|u|pro|v|w|dla|przy|podczas)\s+(?:(?:a|an|the)\s+)?(.+)',text[match.end():])
        if not context or not 3<=len(context[1])<=90:continue
        scenario=context[1]
        tokens=[t for t in scenario.split() if len(t)>=4]
        if not tokens:continue
        error,code=ERRORS[match[1]]
        return {'version':VERSION,'priority_metric':match[1],'other_metric':match[2],
                'error_type':error,'error_code':code,'scenario':scenario,
                'facet_query':f'When is it important to minimize {error} in {scenario}?'}
    return None


def eligible(document, request):
    """Require the named error class and a literal scenario anchor in the body."""
    text=normalize(document.get('text',''))
    code=request['error_code'].lower()
    if not re.search(r'\b'+code+r'\b|\b'+request['error_type']+r'\b',text):return False
    words=set(text.split())
    anchors=[w for w in request['scenario'].split() if len(w)>=4]
    return any(a in words or (len(a)>=5 and any(len(w)>=5 and a[:5]==w[:5] for w in words)) for a in anchors)


def coverage_order(ranked, leading, facet_scores):
    """Retain the original winner; add one cost explanation only when missing."""
    if not leading or not facet_scores:return ranked,None
    best=max(facet_scores,key=facet_scores.__getitem__)
    if facet_scores[best]<.20 or best in leading[:3]:return ranked,None
    return [ranked[0],best]+[i for i in ranked[1:] if i!=best],best

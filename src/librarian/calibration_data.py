"""Leakage grouping and explicit development-only threshold selection, no models."""
import hashlib
import math
import unicodedata


def query_key(text):return ' '.join(unicodedata.normalize('NFKC',text).casefold().split())
def source_key(text):return text.replace('\\','/').casefold()
def passage_key(text):return unicodedata.normalize('NFKC',text).replace('\r\n','\n').strip()


def group_pairs(rows):
    """A shared query OR source OR passage joins whole components transitively."""
    parent=list(range(len(rows)));owners={}
    def root(n):
        while parent[n]!=n:
            parent[n]=parent[parent[n]];n=parent[n]
        return n
    for n,row in enumerate(rows):
        keys=[('query',query_key(row['query'])),('source',source_key(row['source_path'])),
              ('passage',passage_key(row['text']))]
        if any(not value for _,value in keys):raise ValueError('Empty grouping identity')
        for key in keys:
            if key in owners:parent[root(n)]=root(owners[key])
            else:owners[key]=n
    components={}
    for n,row in enumerate(rows):components.setdefault(root(n),[]).append(row)
    result=[]
    for component in components.values():
        identities=sorted({query_key(r['query'])+'\0'+source_key(r['source_path'])+'\0'+passage_key(r['text']) for r in component})
        key=hashlib.sha256('\n'.join(identities).encode('utf-8')).hexdigest()[:16]
        fitted=sorted({v for r in component for v in r.get('fitted_versions',[])})
        for row in component:result.append({**row,'component':key,'component_fitted_versions':fitted,
            'role':'fit_connected_development' if fitted else 'calibration_candidate_development'})
    return result


def coverage(rows,minimums):
    positives=[r for r in rows if r['label']=='direct']
    negatives=[r for r in rows if r['label'] in ('topic_only','irrelevant')]
    binary=positives+negatives
    counts={'direct':len(positives),'negative':len(negatives),
        'query_languages':len({r['language'] for r in binary if r['language']!='unknown'}),
        'families':len({r['family'] for r in binary}),
        'source_groups':len({r['component'] for r in binary})}
    missing={k:{'actual':counts[k],'minimum':v} for k,v in minimums.items() if counts[k]<v}
    # Each requested language needs both classes; a language count alone hides gaps.
    language_classes={lang:{'direct':sum(r['language']==lang for r in positives),
                            'negative':sum(r['language']==lang for r in negatives)} for lang in ('cs','en','pl')}
    class_gaps=[lang for lang,c in language_classes.items() if not c['direct'] or not c['negative']]
    return {'counts':counts,'minimum_shortfalls':missing,'language_classes':language_classes,
            'language_class_gaps':class_gaps,'eligible':not missing and not class_gaps}


def select_threshold(rows, *, min_recall=.8, max_fpr=0.):
    """Only explicitly designated calibration rows; never consume test or fit rows."""
    if not rows:raise ValueError('No calibration rows')
    if not 0<=min_recall<=1 or not 0<=max_fpr<=1:raise ValueError('Invalid selection target')
    for r in rows:
        if r.get('role')!='calibration':raise ValueError('Only explicit calibration rows are accepted')
        if r.get('fitted_versions') or r.get('component_fitted_versions'):raise ValueError('Fitted component leakage')
        if r.get('target') not in (0,1) or isinstance(r.get('target'),bool):raise ValueError('Binary labels required')
        score=r.get('score')
        if isinstance(score,bool) or not isinstance(score,(int,float)) or not math.isfinite(score) or not 0<=score<=1:
            raise ValueError('Finite score in [0,1] required')
    pos=sum(r['target']==1 for r in rows);neg=len(rows)-pos
    if not pos or not neg:raise ValueError('Both classes required')
    thresholds={0.,1.}
    for r in rows:
        thresholds.add(r['score'])
        if r['score']<1:thresholds.add(math.nextafter(r['score'],math.inf))
    feasible=[]
    for threshold in sorted(thresholds):
        tp=sum(r['target']==1 and r['score']>=threshold for r in rows)
        fp=sum(r['target']==0 and r['score']>=threshold for r in rows)
        if tp/pos>=min_recall and fp/neg<=max_fpr:
            feasible.append({'threshold':threshold,'recall':tp/pos,'false_positives':fp,
                'empirical_fpr':fp/neg,'positive_count':pos,'negative_count':neg,
                'zero_fp_upper95_iid_diagnostic':1-.05**(1/neg) if fp==0 else None})
    if not feasible:return {'status':'infeasible','threshold':None,'reason':'No threshold meets fixed calibration targets'}
    selected=max(feasible,key=lambda r:(r['recall'],-r['false_positives'],r['threshold']))
    return {'status':'selected_development_only',**selected}

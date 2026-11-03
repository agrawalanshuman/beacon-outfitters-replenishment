from copy import deepcopy

def cold_snap(p,factor):
    # Official case asks whether the week 3–4 forecast is 20% wrong: all SKUs.
    q=deepcopy(p)
    q['fc']={t:(v*factor if t[2] in [3,4] else v) for t,v in p['fc'].items()}
    return q

def extra_supply(p,k):
    q=deepcopy(p); q['avail'][k,1]+=100
    return q

def policy(r):
    return dict(cases={(x.store_id,x.sku,x.week):x.cases for x in r['plan'].itertuples()},
                visit={(x.store_id,x.week):x.visit for x in r['trucks'].itertuples()})

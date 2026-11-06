"""Constraint and accounting checks independent of model expressions."""
import numpy as np
import pandas as pd

def verify(p,r):
    t=r['plan'].set_index(['store_id','sku','week']);v=r['trucks'].set_index(['store_id','week']).visit
    checks=[]
    def check(family,error): checks.append((family,float(error),float(error)<=1e-5))
    check('finite',0 if np.isfinite(t.to_numpy()).all() else float('inf'))
    check('nonnegative',max(0,-t.to_numpy().min()))
    check('whole_cases',abs(t.cases-t.cases.round()).max())
    for s in p['S']:
        for w in p['W']:
            row=t.loc[(s,slice(None),w),:]
            prev={k:p['opening'][s,k] if w==1 else t.loc[(s,k,w-1),'inventory'] for k in p['K']}
            check('shelf',max(0,sum(prev.values())+row.units_shipped.sum()-p['shelf'][s]))
            check('truck',max(0,row.units_shipped.sum()-p['truck'][s]*v[s,w]))
            check('binary_visit',min(abs(v[s,w]),abs(v[s,w]-1)))
            check('zero_delivery_visit',int(v[s,w]==1 and row.units_shipped.sum()<1e-6))
            for k in p['K']:
                a=t.loc[s,k,w]
                check('flow',abs(prev[k]+a.units_shipped-a.sales-a.inventory))
                check('demand',abs(a.sales+a.lost-p['fc'][s,k,w]))
                check('case_units',abs(a.units_shipped-a.cases*p['pack'][k]))
    for k in p['K']:
        for w in p['W']:
            check('cumulative_dc',max(0,t.reset_index().query('sku==@k and week<=@w').units_shipped.sum()-sum(p['avail'][k,j] for j in p['W'] if j<=w)))
    a=r['plan']; margin=sum(p['margin'][z.sku]*z.sales for z in a.itertuples())
    holding=sum(p['hold'][z.sku]*z.inventory for z in a.itertuples())
    delivery=sum(p['vcost'][z.store_id]*z.visit for z in r['trucks'].itertuples())
    check('objective',abs(margin-holding-delivery-r['objective']))
    result=pd.DataFrame(checks,columns=['family','violation','passed']).groupby('family',as_index=False).agg(violation=('violation','max'),passed=('passed','all'))
    assert result.passed.all(), result.to_string()
    return result,dict(profit=margin-holding-delivery,sales_margin=margin,holding_cost=holding,delivery_cost=delivery,
        units_sold=a.sales.sum(),units_lost=a.lost.sum(),fill_rate=a.sales.sum()/sum(p['fc'].values()),
        cases=a.cases.sum(),units_shipped=a.units_shipped.sum(),visits=r['trucks'].visit.sum())

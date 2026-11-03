"""Single computation pipeline consumed by notebook, results, memo and deck."""
import json
from pathlib import Path
import pandas as pd
import numpy as np
from src.optimization import solve
from src.validation import verify
from src.baselines import naive_policy
from src.scenarios import cold_snap,extra_supply,policy


def run_analysis(p,out='results',compare=True):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    runs={}; stats={}; checks=[]; evidence=[]
    def run(name,params=None,backend='gurobi',**kw):
        params=p if params is None else params
        try: r=solve(params,backend,**kw)
        except Exception as e:
            if backend!='gurobi': raise
            evidence.append(dict(scenario=name,solver=backend,status='UNAVAILABLE',detail=str(e)))
            print(f'{name}: Gurobi unavailable ({type(e).__name__}: {e}); using exact CP-SAT',flush=True)
            r=solve(params,'cp-sat',**kw)
        ch,st=verify(params,r);ch['scenario']=name;checks.append(ch)
        st.update(scenario=name,status=r['status']);stats[name]=st;runs[name]=r
        evidence.append(dict(scenario=name,**{k:v for k,v in r.items() if k not in ['plan','trucks']}))
        print(f'{name}: {r["status"]} ${st["profit"]:,.2f} ({r["runtime"]:.2f}s)',flush=True)
        return r
    base=run('base')
    if compare:
        other=run('base_cp_sat',backend='cp-sat',limit=60)
        if base['status']==other['status']=='OPTIMAL': assert abs(base['objective']-other['objective'])<0.011
    run('do_nothing',no_ship=True)
    run('naive',fixed=naive_policy(p))
    run('alternate_week',alternate=True)
    for label,f in [('lower',0.8),('higher',1.2)]:
        q=cold_snap(p,f);run(label,q);run(label+'_fixed',q,fixed=policy(base))
    bottlenecks=[]
    for k in p['K']:
        r=run('extra_'+k,extra_supply(p,k))
        bottlenecks.append(dict(sku=k,release_week=1,extra_units=100,profit=r['objective'],
            profit_gain=r['objective']-base['objective'],status=r['status'],base_status=base['status']))
    for name,r in runs.items():
        r['plan'].to_csv(out/f'{name}_plan.csv',index=False)
    base['plan'].query('cases>0').to_csv(out/'shipment_plan.csv',index=False)
    tr=base['trucks'].merge(base['plan'].groupby(['store_id','week']).units_shipped.sum().reset_index())
    tr['delivery_cost']=tr.apply(lambda z:z.visit*p['vcost'][z.store_id],axis=1)
    tr['cost_per_unit']=tr.delivery_cost.div(tr.units_shipped.replace(0,np.nan))
    tr['utilization']=tr.apply(lambda z:z.units_shipped/p['truck'][z.store_id],axis=1)
    tr.to_csv(out/'truck_schedule.csv',index=False)
    summary=pd.DataFrame(stats.values());summary['profit_uplift_vs_do_nothing']=summary.profit-stats['do_nothing']['profit']
    summary['profit_uplift_vs_naive']=summary.profit-stats['naive']['profit']
    summary.to_csv(out/'financial_summary.csv',index=False)
    summary[summary.scenario.isin(['base','do_nothing','naive'])].to_csv(out/'baseline_comparison.csv',index=False)
    summary[summary.scenario.isin(['base','lower','higher','lower_fixed','higher_fixed','alternate_week'])].to_csv(out/'sensitivity_results.csv',index=False)
    pd.DataFrame(bottlenecks).sort_values('profit_gain',ascending=False).to_csv(out/'sku_bottleneck.csv',index=False)
    pd.concat(checks).to_csv(out/'feasibility_checks.csv',index=False)
    pd.DataFrame(evidence).to_csv(out/'solver_comparison.csv',index=False)
    weekly=[]
    for w in p['W']:
        a=base['plan'].query('week==@w');t=tr.query('week==@w')
        margin=sum(p['margin'][z.sku]*z.sales for z in a.itertuples());holding=sum(p['hold'][z.sku]*z.inventory for z in a.itertuples())
        weekly.append(dict(week=w,sales_margin=margin,holding_cost=holding,delivery_cost=t.delivery_cost.sum(),profit=margin-holding-t.delivery_cost.sum()))
    pd.DataFrame(weekly).to_csv(out/'weekly_financials.csv',index=False)
    dc=[]
    for k in p['K']:
        for w in p['W']:
            shipped=base['plan'].query('sku==@k and week<=@w').units_shipped.sum()
            available=sum(p['avail'][k,j] for j in p['W'] if j<=w)
            dc.append(dict(sku=k,week=w,cumulative_shipped=shipped,cumulative_available=available,slack=available-shipped,binding=abs(available-shipped)<1e-5))
    pd.DataFrame(dc).to_csv(out/'dc_constraints.csv',index=False)
    base['plan'].query('lost>0.00001').to_csv(out/'shortages.csv',index=False)
    sku_summary=base['plan'].groupby('sku')[['sales','lost','inventory','units_shipped']].sum()
    sku_summary['fill_rate']=sku_summary.sales/(sku_summary.sales+sku_summary.lost)
    sku_summary.rename(columns={'inventory':'inventory_unit_weeks'}).to_csv(out/'sku_summary.csv')
    changes=[]
    base_cases=base['plan'].set_index(['store_id','sku','week']).cases
    base_visits=base['trucks'].set_index(['store_id','week']).visit
    for name in ['lower','higher','alternate_week']:
        r=runs[name]
        cases=r['plan'].set_index(['store_id','sku','week']).cases
        visits=r['trucks'].set_index(['store_id','week']).visit
        changes.append(dict(scenario=name,changed_case_decisions=int((cases!=base_cases).sum()),
            absolute_case_changes=int((cases-base_cases).abs().sum()),changed_visit_decisions=int((visits!=base_visits).sum())))
    pd.DataFrame(changes).to_csv(out/'decision_changes.csv',index=False)
    integer_residual=max(abs(base['plan'][['sales','lost','inventory']].to_numpy()-base['plan'][['sales','lost','inventory']].round().to_numpy()).flat)
    payload=dict(base_profit=float(stats['base']['profit']),integer_residual=float(integer_residual),
        scenarios={k:{key:(float(value) if isinstance(value,(np.number,)) else value) for key,value in val.items()} for k,val in stats.items()},
        bottlenecks=bottlenecks)
    (out/'verified_summary.json').write_text(json.dumps(payload,indent=2))
    return runs,summary,tr


def charts(summary,tr,out='results/figures'):
    import matplotlib.pyplot as plt
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid')
    for names,title,filename in [(['base','do_nothing','naive'],'Four-week contribution profit','baseline'),
           (['lower','lower_fixed','base','higher_fixed','higher'],'Cold-snap sensitivity: reoptimized vs fixed shipments','sensitivity')]:
        a=summary.set_index('scenario').loc[names];fig,ax=plt.subplots(figsize=(9,4))
        ax.bar(a.index,a.profit,color=['#177e89' if 'fixed' not in x else '#df9b36' for x in names])
        ax.set(ylabel='Contribution profit ($)',title=title);ax.tick_params(axis='x',rotation=15)
        for i,v in enumerate(a.profit):ax.text(i,v+1000,f'${v:,.0f}',ha='center',fontsize=9)
        fig.tight_layout();fig.savefig(out/f'{filename}.png',dpi=160);plt.show();plt.close(fig)
    a=tr.pivot(index='store_id',columns='week',values='units_shipped');fig,ax=plt.subplots(figsize=(8,6))
    im=ax.imshow(a,cmap='YlGnBu');ax.set_xticks(range(4),['Week 1','Week 2','Week 3','Week 4']);ax.set_yticks(range(len(a)),a.index)
    for i in range(len(a)):
        for j in range(4):ax.text(j,i,str(int(a.iloc[i,j])),ha='center',va='center',color='black')
    ax.set_title('Truck calendar: delivered units (zero = no visit)');fig.colorbar(im,ax=ax);fig.tight_layout()
    fig.savefig(out/'truck_calendar.png',dpi=160);plt.show();plt.close(fig)

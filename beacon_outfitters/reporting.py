"""Single computation pipeline consumed by notebook, results, memo and deck."""
import json
from pathlib import Path
import pandas as pd
import numpy as np
from beacon_outfitters.optimization import solve
from beacon_outfitters.validation import verify
from beacon_outfitters.baselines import naive_policy
from beacon_outfitters.scenarios import cold_snap,extra_supply,policy


def run_analysis(p,out='results',compare=True,provenance=None):
    root=Path(out);out=root/'tables';out.mkdir(parents=True,exist_ok=True)
    plans=root/'plans';plans.mkdir(exist_ok=True)
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
        r['plan'].to_csv(plans/f'{name}.csv',index=False)
    base['plan'].query('cases>0').to_csv(out/'shipment_plan.csv',index=False)
    tr=base['trucks'].merge(base['plan'].groupby(['store_id','week']).units_shipped.sum().reset_index())
    tr['delivery_cost']=tr.apply(lambda z:z.visit*p['vcost'][z.store_id],axis=1)
    tr['cost_per_unit']=tr.delivery_cost.div(tr.units_shipped.replace(0,np.nan))
    tr['utilization']=tr.apply(lambda z:z.units_shipped/p['truck'][z.store_id],axis=1)
    tr.to_csv(out/'truck_schedule.csv',index=False)
    summary=pd.DataFrame(stats.values());summary['profit_difference_vs_base_no_delivery']=summary.profit-stats['do_nothing']['profit']
    summary['profit_difference_vs_base_heuristic']=summary.profit-stats['naive']['profit']
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
    (root/'run_summary.json').write_text(json.dumps(payload,indent=2))
    import platform
    import importlib.metadata
    from datetime import datetime, timezone
    metadata = dict(schema_version=1, generated_at_utc=datetime.now(timezone.utc).isoformat(),
        python=platform.python_version(), platform=platform.platform(), seed=839, workers=2,
        default_time_limit_seconds=120, comparison_time_limit_seconds=60,
        dependencies={name:importlib.metadata.version(name) for name in ['pandas','numpy','ortools','matplotlib']},
        provenance=provenance or {}, scenarios=list(stats),
        all_returned_solutions_verified=True, all_solutions_proven_optimal=all(r['status']=='OPTIMAL' for r in runs.values()))
    (root/'run_metadata.json').write_text(json.dumps(metadata,indent=2))
    return runs,summary,tr


def charts(summary, tr, out='results/figures'):
    """Render decision-focused figures from the same verified experiment tables."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    s = summary.set_index('scenario')
    opportunities = pd.read_csv(out.parent/'tables/sku_bottleneck.csv')
    navy, teal, amber, muted = '#142D4E', '#087E8B', '#E5A23D', '#65758B'
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10,
        'axes.spines.top':False, 'axes.spines.right':False,
        'axes.titleweight':'bold', 'axes.labelcolor':navy,
        'text.color':navy, 'axes.titlecolor':navy, 'figure.facecolor':'white'})
    money_axis = FuncFormatter(lambda x, _: f'${x/1000:,.0f}k')

    def finish(fig, name):
        fig.savefig(out/f'{name}.png', dpi=160, bbox_inches='tight', facecolor='white')
        plt.show()
        plt.close(fig)

    def bars(ax, names, labels, title):
        vals = s.loc[names, 'profit']
        ax.barh(labels, vals, color=[teal if n=='base' else navy for n in names], height=.58)
        ax.invert_yaxis()
        ax.set(title=title, xlabel='Modeled four-week contribution ($)')
        ax.xaxis.set_major_formatter(money_axis)
        ax.set_xlim(0, vals.max()*1.23)
        for i, val in enumerate(vals):
            ax.text(val+1500, i, f'${val:,.0f}', va='center', fontsize=10)
        ax.grid(axis='x', alpha=.15)
        ax.set_axisbelow(True)

    fig, ax = plt.subplots(figsize=(10,4.3), layout='constrained')
    bars(ax, ['base','naive','do_nothing'], ['Optimized plan','Feasible heuristic','No deliveries'], 'Policy benchmark | same demand and accounting')
    finish(fig, 'baseline')

    fig, ax = plt.subplots(figsize=(10,4.5), layout='constrained')
    names = ['lower','base','higher']
    x = np.arange(3); reopt = s.loc[names, 'profit'].to_numpy()
    fixed = s.loc[['lower_fixed','base','higher_fixed'],'profit'].to_numpy()
    ax.bar(x-.18, reopt, width=.36, label='Reoptimized', color=teal)
    ax.bar(x+.18, fixed, width=.36, label='Base shipments retained', color=amber)
    ax.set_xticks(x, ['−20% late demand','Base demand','+20% late demand'])
    ax.set(title='Demand uncertainty | adaptation versus a fixed shipment policy', ylabel='Modeled four-week contribution ($)')
    ax.yaxis.set_major_formatter(money_axis);ax.set_ylim(0,max(reopt)*1.20)
    for positions, values in [(x-.18,reopt),(x+.18,fixed)]:
        for pos,val in zip(positions,values):ax.text(pos,val+1800,f'${val/1000:,.1f}k',ha='center',fontsize=9)
    ax.legend(loc='upper left', frameon=False);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    finish(fig, 'sensitivity')

    calendar = tr.pivot(index='store_id',columns='week',values='units_shipped')
    fig, ax = plt.subplots(figsize=(9,6.8), layout='constrained')
    im = ax.imshow(calendar,cmap='Blues',vmin=0)
    ax.set_xticks(range(4), ['Week 1','Week 2','Week 3','Week 4'])
    ax.set_yticks(range(len(calendar)),calendar.index)
    ax.set_title('Delivery calendar | units delivered; zero means no visit',pad=16)
    for i in range(len(calendar)):
        for j in range(4):
            val=calendar.iloc[i,j]
            ax.text(j,i,str(int(val)),ha='center',va='center',color='white' if val>calendar.max().max()*.6 else navy)
    fig.colorbar(im,ax=ax,shrink=.8,label='Units delivered')
    finish(fig, 'truck_calendar')

    fig, ax = plt.subplots(figsize=(10,4.2), layout='constrained')
    a=opportunities.sort_values('profit_gain',ascending=True)
    ax.barh(a.sku,a.profit_gain.clip(lower=0),color=[teal if k=='J200' else navy for k in a.sku])
    ax.set(title='Supply opportunity | 100 additional units released in week 1',xlabel='Gross modeled contribution gain ($)')
    for i,v in enumerate(a.profit_gain):ax.text(max(0,v)+80,i,f'${v:,.0f}',va='center',fontsize=9)
    ax.set_xlim(0,a.profit_gain.max()*1.18);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    finish(fig, 'supply_opportunity')

    fig = plt.figure(figsize=(16,9), facecolor='#F4F7FB', layout='constrained')
    grid=fig.add_gridspec(3,2,height_ratios=[.65,1.7,1.6])
    header=fig.add_subplot(grid[0,:]);header.axis('off')
    header.text(0, .93, 'BEACON OUTFITTERS  /  REPLENISHMENT DECISION ANALYTICS',fontsize=20,fontweight='bold')
    uplift=s.loc['base','profit']-s.loc['naive','profit']
    header.text(0,.56,'Contributors: Anshuman · Inka · Juan Diego',fontsize=11,color=muted)
    metrics=[(f"${s.loc['base','profit']:,.0f}",'MODELED CONTRIBUTION'),
             (f"{100*uplift/s.loc['naive','profit']:.2f}%",'UPLIFT VS FEASIBLE HEURISTIC'),
             (f"{s.loc['base','fill_rate']:.2%}",'DEMAND FILL RATE'),
             (f"{int(s.loc['base','visits'])}",'PLANNED STORE VISITS')]
    for i,(value,label) in enumerate(metrics):
        header.text(i*.25,.12,value,fontsize=24,fontweight='bold',color=teal)
        header.text(i*.25,-.14,label,fontsize=9,color=muted)
    left=fig.add_subplot(grid[1,0]);bars(left,['base','naive','do_nothing'],['Optimized','Heuristic','No deliveries'],'Four-week benchmark')
    right=fig.add_subplot(grid[1,1]);a=opportunities.head(3).iloc[::-1]
    right.barh(a.sku,a.profit_gain,color=teal);right.set(title='Best +100-unit supply opportunities',xlabel='Gross modeled gain ($)')
    right.set_xlim(0,a.profit_gain.max()*1.25)
    for i,v in enumerate(a.profit_gain):right.text(v+100,i,f'${v:,.0f}',va='center')
    ax=fig.add_subplot(grid[2,:]);im=ax.imshow(calendar.T,aspect='auto',cmap='Blues',vmin=0)
    ax.set_xticks(range(len(calendar)),calendar.index);ax.set_yticks(range(4),['Week 1','Week 2','Week 3','Week 4'])
    ax.set_title('Executable store/week delivery calendar · delivered units',pad=12)
    for i in range(4):
        for j in range(len(calendar)):
            v=calendar.iloc[j,i];ax.text(j,i,str(int(v)),ha='center',va='center',color='white' if v>calendar.max().max()*.6 else navy)
    fig.text(.015,-.025,'Benchmark results, not realized company savings. Gurobi and CP-SAT independently certify the base objective.',fontsize=10,color=muted)
    finish(fig, 'overview')

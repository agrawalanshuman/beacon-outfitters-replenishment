"""Same replenishment model through Gurobi and exact-scaled CP-SAT."""
import time
import math
import pandas as pd


def solve(p, backend='cp-sat', fixed=None, no_ship=False, alternate=False, limit=120):
    if backend not in {'gurobi', 'cp-sat'}:
        raise ValueError(f'Unsupported backend: {backend}')
    S,K,W = (p[x] for x in ['S','K','W'])
    keys=[(s,k,w) for s in S for k in K for w in W]
    sw=[(s,w) for s in S for w in W]
    cp = backend == 'cp-sat'
    scale=5 if cp else 1  # 0.8 / 1.2 demand is exact in fifths; no rounding.
    if cp:
        import ortools
        from ortools.sat.python import cp_model
        model=cp_model.CpModel()
        version=ortools.__version__
        def var(lo,hi,name,integer=True): return model.new_int_var(int(lo),int(hi),name)
        add=model.add
    else:
        import gurobipy as gp
        model=gp.Model('beacon');model.Params.OutputFlag=0
        model.Params.TimeLimit=limit; model.Params.Seed=839; model.Params.Threads=2
        model.Params.MIPGap=0;model.Params.MIPGapAbs=0.001
        version='.'.join(map(str,gp.gurobi.version()))
        def var(lo,hi,name,integer=True):
            return model.addVar(lb=lo,ub=hi,vtype=gp.GRB.INTEGER if integer else gp.GRB.CONTINUOUS,name=name)
        add=model.addConstr
    def q(x):
        v=x*scale
        if cp and abs(v-round(v))>1e-6: raise ValueError('Quantity not exact in fifths')
        return int(round(v)) if cp else v
    cases={t:var(0, int(min(p['truck'][t[0]],p['shelf'][t[0]])//p['pack'][t[1]]),f'cases_{t}') for t in keys}
    sales={t:var(0,q(p['fc'][t]),f'sales_{t}',False) for t in keys}
    lost={t:var(0,q(p['fc'][t]),f'lost_{t}',False) for t in keys}
    inv={t:var(0,q(p['shelf'][t[0]]),f'inv_{t}',False) for t in keys}
    visit={t:var(0,1,f'visit_{t}') for t in sw}
    for s,k,w in keys:
        t=(s,k,w); prev=q(p['opening'][s,k]) if w==1 else inv[s,k,w-1]
        add(prev+q(p['pack'][k])*cases[t]==sales[t]+inv[t])
        add(sales[t]+lost[t]==q(p['fc'][t]))
        if no_ship: add(cases[t]==0)
        if fixed is not None: add(cases[t]==int(fixed['cases'][t]))
    for s,w in sw:
        units=sum(q(p['pack'][k])*cases[s,k,w] for k in K)
        prev=sum(q(p['opening'][s,k]) if w==1 else inv[s,k,w-1] for k in K)
        add(prev+units<=q(p['shelf'][s]))
        add(units<=q(p['truck'][s])*visit[s,w])
        if fixed is not None: add(visit[s,w]==int(fixed['visit'][s,w]))
    if alternate:
        # Each store chooses either weeks 1&3 or weeks 2&4, and may skip a visit.
        phase={s:var(0,1,f'phase_{s}') for s in S}
        for s,w in sw: add(visit[s,w] <= (phase[s] if w%2 else 1-phase[s]))
    for k in K:
        for w in W:
            add(sum(q(p['pack'][k])*cases[s,k,t] for s in S for t in W if t<=w)
                <=q(sum(p['avail'][k,t] for t in W if t<=w)))
    def cents(x):
        assert abs(100*x-round(100*x))<1e-6
        return int(round(100*x))
    objective=sum(cents(p['margin'][k])*sales[s,k,w]-cents(p['hold'][k])*inv[s,k,w] for s,k,w in keys)-sum(cents(p['vcost'][s])*scale*visit[s,w] for s,w in sw)
    start=time.perf_counter()
    if cp:
        model.maximize(objective); solver=cp_model.CpSolver()
        solver.parameters.max_time_in_seconds=limit;solver.parameters.num_search_workers=2;solver.parameters.random_seed=839
        status=solver.solve(model);status_name=solver.status_name(status)
        if status not in [cp_model.OPTIMAL,cp_model.FEASIBLE]: raise RuntimeError(status_name)
        value=solver.value; obj=solver.objective_value/(100*scale);bound=solver.best_objective_bound/(100*scale)
    else:
        model.setObjective(objective, gp.GRB.MAXIMIZE);model.optimize()
        if not model.SolCount: raise RuntimeError(f'Gurobi status {model.Status}: no incumbent')
        status_name='OPTIMAL' if model.Status==gp.GRB.OPTIMAL else f'FEASIBLE_STATUS_{model.Status}'
        value=lambda v:v.X; obj=model.ObjVal/100;bound=model.ObjBound/100
    rows=[]
    for s,k,w in keys:
        t=s,k,w
        rows.append(dict(store_id=s,sku=k,week=w,cases=int(round(value(cases[t]))),
                         units_shipped=int(round(value(cases[t])))*p['pack'][k],
                         sales=value(sales[t])/scale,lost=value(lost[t])/scale,inventory=value(inv[t])/scale))
    trucks=pd.DataFrame([dict(store_id=s,week=w,visit=int(round(value(visit[s,w])))) for s,w in sw])
    return dict(plan=pd.DataFrame(rows), trucks=trucks, objective=obj, status=status_name, bound=bound,
                gap=abs(bound-obj)/max(1,abs(obj)), runtime=time.perf_counter()-start,solver=backend,version=version)

"""Deterministic feasible weekly-forecast heuristic, never a relaxed plan."""
import math
from copy import deepcopy

def naive_policy(p):
    stock=dict(p['opening']); dc={k:0 for k in p['K']}; cases={};visit={}
    # Stable IDs are tie-breaks; high margin per unit SKUs first.
    order=sorted(p['K'],key=lambda k:(-p['margin'][k],k))
    for w in p['W']:
        for k in p['K']: dc[k]+=p['avail'][k,w]
        for s in sorted(p['S']):
            room=p['shelf'][s]-sum(stock[s,k] for k in p['K']); truck=p['truck'][s]
            for k in order:
                pack=p['pack'][k];wanted=max(0,math.ceil((p['fc'][s,k,w]-stock[s,k])/pack))
                c=min(wanted,int(dc[k]//pack),int(room//pack),int(truck//pack))
                cases[s,k,w]=c;units=c*pack;stock[s,k]+=units;dc[k]-=units;room-=units;truck-=units
            visit[s,w]=int(truck<p['truck'][s])
            for k in p['K']: stock[s,k]-=min(stock[s,k],p['fc'][s,k,w])
    return dict(cases=cases,visit=visit)

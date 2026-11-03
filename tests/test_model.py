from copy import deepcopy
import pytest
from src.optimization import solve
from src.validation import verify


def tiny():
    return dict(S=['S'],K=['K'],W=[1,2,3,4],shelf={'S':6},truck={'S':6},vcost={'S':2},
        pack={'K':3},margin={'K':10},hold={'K':1},opening={('S','K'):0},
        fc={('S','K',w):3 for w in [1,2,3,4]},avail={('K',w):3 for w in [1,2,3,4]})

@pytest.mark.parametrize('backend',['gurobi','cp-sat'])
def test_manual_four_visits(backend):
    p=tiny();r=solve(p,backend);verify(p,r)
    assert r['status']=='OPTIMAL'
    assert r['objective']==pytest.approx(112)  # 12*10 - 4*2; early stock not available.
    assert r['trucks'].visit.sum()==4


def test_dc_carry_and_shared_shelf():
    p=tiny();p['avail']={('K',w):12 if w==1 else 0 for w in p['W']}
    r=solve(p);verify(p,r)
    # Consolidating two weeks saves $2 truck but costs $3 holding: weekly wins.
    assert r['objective']==pytest.approx(112)
    p['vcost']['S']=5;r=solve(p);verify(p,r)
    assert r['objective']==pytest.approx(104)  # two trucks (10) + six holding (6).


def test_corruption_detected():
    p=tiny();r=solve(p);r['plan'].loc[0,'sales']+=1
    with pytest.raises(AssertionError): verify(p,r)


def test_do_nothing():
    p=tiny();p['opening']['S','K']=3
    r=solve(p,no_ship=True);verify(p,r)
    assert r['objective']==pytest.approx(30)
    assert r['plan'].units_shipped.sum()==0

@pytest.mark.parametrize('backend',['gurobi','cp-sat'])
def test_fractional_demand_is_exact(backend):
    p=tiny();p['opening']['S','K']=3
    p['fc']={('S','K',w):2.4 if w==1 else 0 for w in p['W']}
    r=solve(p,backend,no_ship=True);verify(p,r)
    assert r['objective']==pytest.approx(21.6)

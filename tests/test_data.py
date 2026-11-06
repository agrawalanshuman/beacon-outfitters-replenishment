from pathlib import Path
from copy import deepcopy
import pytest
from beacon_outfitters.data_loader import load_data,validate_data,parameters
from beacon_outfitters.scenarios import cold_snap
ROOT=Path(__file__).resolve().parents[1]
def test_real_data_and_corruption():
    d=load_data(ROOT/'data/raw');assert validate_data(d)
    broken=deepcopy(d);broken['demand_forecast'].iloc[0,0]='unknown'
    with pytest.raises(AssertionError):validate_data(broken)

def test_fractional_forecast_and_unchanged_early_weeks():
    p=parameters(load_data(ROOT/'data/raw'));q=cold_snap(p,0.8)
    for t,v in p['fc'].items():
        assert q['fc'][t]==pytest.approx(v if t[2]<3 else v*0.8)
        assert q['fc'][t]*5==pytest.approx(round(q['fc'][t]*5))

@pytest.mark.parametrize('dataset,column,value',[
    ('skus','case_pack',1.5),('stores','truck_capacity_units',float('inf')),
    ('demand_forecast','forecast_units',-1),('skus','holding_cost_per_unit_week',0.001)])
def test_invalid_numeric_inputs_rejected(dataset,column,value):
    d=load_data(ROOT/'data/raw');d[dataset][column]=d[dataset][column].astype(float)
    d[dataset].loc[0,column]=value
    with pytest.raises(AssertionError):validate_data(d)

"""Official academic case data, with checksum-verified offline snapshots."""
from pathlib import Path
from io import BytesIO
from urllib.request import urlopen
import hashlib
import pandas as pd

NAMES = ['stores', 'skus', 'demand_forecast', 'opening_inventory', 'dc_availability']

def load_data(root):
    return {n: pd.read_csv(Path(root) / f'{n}.csv') for n in NAMES}


def validate_data(d):
    import numpy as np
    expected = dict(zip(NAMES, [12, 8, 384, 96, 32]))
    keys = {'stores':['store_id'], 'skus':['sku'], 'demand_forecast':['store_id','sku','week'],
            'opening_inventory':['store_id','sku'], 'dc_availability':['sku','week']}
    numeric_columns = {
        'stores':['shelf_capacity_units','delivery_cost_per_visit','truck_capacity_units'],
        'skus':['unit_cost','retail_price','case_pack','holding_cost_per_unit_week'],
        'demand_forecast':['week','forecast_units'],
        'opening_inventory':['on_hand_units'], 'dc_availability':['week','units_available']}
    money = {'unit_cost','retail_price','holding_cost_per_unit_week','delivery_cost_per_visit'}
    assert set(d)==set(NAMES), 'Expected exactly five datasets'
    for name,t in d.items():
        required = set(keys[name]+numeric_columns[name])
        if name=='stores': required.add('store_name')
        if name=='skus': required.add('sku_name')
        assert set(t.columns)==required, f'{name}: unexpected schema'
        assert len(t)==expected[name], f'{name}: unexpected row count'
        assert not t.isna().any().any(), f'{name}: missing values'
        assert not t.duplicated(keys[name]).any(), f'{name}: duplicate keys'
        for col in numeric_columns[name]:
            assert pd.api.types.is_numeric_dtype(t[col]), f'{name}.{col}: numeric dtype required'
            assert np.isfinite(t[col]).all() and (t[col]>=0).all(), f'{name}.{col}: invalid range'
            scale=100 if col in money else 1
            assert np.allclose(t[col]*scale, np.round(t[col]*scale), atol=1e-8, rtol=0), f'{name}.{col}: invalid precision'
    S,K=set(d['stores'].store_id),set(d['skus'].sku)
    grids = {
        'demand_forecast':{(s,k,w) for s in S for k in K for w in [1,2,3,4]},
        'opening_inventory':{(s,k) for s in S for k in K},
        'dc_availability':{(k,w) for k in K for w in [1,2,3,4]}}
    for name,grid in grids.items():
        assert set(d[name][keys[name]].itertuples(index=False,name=None))==grid, f'{name}: incomplete/unknown identifiers'
    assert (d['skus'].case_pack>0).all(), 'Positive case packs required'
    assert (d['skus'].retail_price>d['skus'].unit_cost).all(), 'Positive margins required'
    assert (d['stores'][['shelf_capacity_units','truck_capacity_units','delivery_cost_per_visit']]>0).all().all()
    assert (d['skus'].holding_cost_per_unit_week>0).all()
    opening=d['opening_inventory'].groupby('store_id').on_hand_units.sum()
    assert (opening<=d['stores'].set_index('store_id').shelf_capacity_units).all(), 'Opening inventory exceeds shared shelf'
    return True


def parameters(d):
    st, sk = d['stores'].set_index('store_id'), d['skus'].set_index('sku')
    return dict(S=list(st.index), K=list(sk.index), W=[1,2,3,4],
        shelf=st.shelf_capacity_units.to_dict(), truck=st.truck_capacity_units.to_dict(),
        vcost=st.delivery_cost_per_visit.to_dict(), pack=sk.case_pack.to_dict(),
        margin=(sk.retail_price-sk.unit_cost).to_dict(), hold=sk.holding_cost_per_unit_week.to_dict(),
        fc=d['demand_forecast'].set_index(['store_id','sku','week']).forecast_units.to_dict(),
        opening=d['opening_inventory'].set_index(['store_id','sku']).on_hand_units.to_dict(),
        avail=d['dc_availability'].set_index(['sku','week']).units_available.to_dict())

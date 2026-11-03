import json
from pathlib import Path
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]

def test_saved_results_reconcile():
    r=ROOT/'results';s=pd.read_csv(r/'financial_summary.csv').set_index('scenario')
    assert s.loc['base','profit']==pytest.approx(213503.10)
    assert s.loc['base_cp_sat','profit']==pytest.approx(s.loc['base','profit'])
    assert s.loc['base','profit']>=s.loc['naive','profit']>=s.loc['do_nothing','profit']
    assert pd.read_csv(r/'weekly_financials.csv').profit.sum()==pytest.approx(s.loc['base','profit'])
    assert pd.read_csv(r/'feasibility_checks.csv').passed.all()
    assert s.loc['lower','profit']>=s.loc['lower_fixed','profit']-0.01
    assert s.loc['higher','profit']>=s.loc['higher_fixed','profit']-0.01

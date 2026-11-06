import json
from pathlib import Path
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]

def test_saved_results_reconcile():
    r=ROOT/'results/tables';s=pd.read_csv(r/'financial_summary.csv').set_index('scenario')
    assert s.loc['base','profit']==pytest.approx(213503.10)
    assert s.loc['base_cp_sat','profit']==pytest.approx(s.loc['base','profit'])
    assert s.loc['base','profit']>=s.loc['naive','profit']>=s.loc['do_nothing','profit']
    assert pd.read_csv(r/'weekly_financials.csv').profit.sum()==pytest.approx(s.loc['base','profit'])
    assert pd.read_csv(r/'feasibility_checks.csv').passed.all()
    assert s.loc['lower','profit']>=s.loc['lower_fixed','profit']-0.01
    assert s.loc['higher','profit']>=s.loc['higher_fixed','profit']-0.01


def test_run_provenance_matches_inputs_and_model():
    import hashlib
    meta=json.loads((ROOT/'results/run_metadata.json').read_text())
    assert meta['all_returned_solutions_verified']
    assert meta['all_solutions_proven_optimal']
    assert len(meta['scenarios'])==17
    for name,digest in meta['provenance']['input_sha256'].items():
        assert hashlib.sha256((ROOT/f'data/raw/{name}.csv').read_bytes()).hexdigest()==digest
    for name,digest in meta['provenance']['model_source_sha256'].items():
        assert hashlib.sha256((ROOT/'beacon_outfitters'/name).read_bytes()).hexdigest()==digest

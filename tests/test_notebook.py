from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
import pandas as pd
import nbformat
ROOT=Path(__file__).resolve().parents[1]

def test_offline_embedded_snapshots_match_original_csvs():
    n=nbformat.read(ROOT/'notebooks/Beacon_Outfitters_Optimization.ipynb',as_version=4)
    cell=next(c for c in n.cells if c.cell_type=='code' and 'SNAPSHOTS = ' in c.source)
    namespace={}
    with patch('urllib.request.urlopen',side_effect=URLError('offline integration test')):
        exec(compile(cell.source,'notebook-data-cell','exec'),namespace)
    for name,frame in namespace['data'].items():
        pd.testing.assert_frame_equal(frame,pd.read_csv(ROOT/f'data/raw/{name}.csv'))

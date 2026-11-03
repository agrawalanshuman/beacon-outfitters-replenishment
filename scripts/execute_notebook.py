"""Run the submission notebook in an isolated kernel outside the checkout."""
from pathlib import Path
import argparse,json,tempfile,time,os
import nbformat
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--workdir',type=Path);args=parser.parse_args()
work=args.workdir or Path(tempfile.mkdtemp(prefix='beacon-notebook-'))
work.mkdir(parents=True,exist_ok=True)
assert not any(work.iterdir()), 'Choose an empty working directory'
os.environ.setdefault('MPLCONFIGDIR','/tmp/beacon-mpl')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/beacon-cache')
p=ROOT/'class_submission/Beacon_Outfitters_Midterm.ipynb';n=nbformat.read(p,as_version=4)
start=time.perf_counter()
NotebookClient(n,timeout=900,kernel_name='python3',resources={'metadata':{'path':str(work.resolve())}}).execute()
nbformat.write(n,p)
record=dict(code_cells=sum(c.cell_type=='code' for c in n.cells),
    executed=sum(c.cell_type=='code' and c.execution_count is not None for c in n.cells),
    errors=sum(o.output_type=='error' for c in n.cells if c.cell_type=='code' for o in c.outputs),
    runtime_seconds=time.perf_counter()-start,working_directory='empty directory outside checkout',hosted_colab_tested=False)
(ROOT/'results/notebook_execution.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2));print('Computed results:',work/'beacon_results')

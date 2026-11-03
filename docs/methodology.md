# Reproducible workflow

Use the existing checkout. Python 3.12.14 was tested. Install exact versions:

```sh
python -m pip install -r requirements.txt
```

The class notebook is independent of the checkout and includes all tested model
source plus checksum-verified original CSV snapshots. It fetches public course
data at a fixed Git revision and falls back to identical embedded bytes. It
installs core dependencies then attempts optional Gurobi separately. No secret,
manual upload, paid runtime, or checkout-relative input is needed.

To refresh the local result pipeline from the repository root:

```sh
MPLCONFIGDIR=/tmp/beacon-mpl python - <<'PY'
from src.data_loader import load_data, validate_data, parameters
from src.reporting import run_analysis, charts
data = load_data('data/raw')
validate_data(data)
runs, summary, trucks = run_analysis(parameters(data))
charts(summary, trucks)
PY
python scripts/build_submission.py
python -m pytest -q
```

`python scripts/build_notebook.py` detects origin owner and remote default branch,
then rebuilds the self-contained notebook. This requires read-only Git access
and clears notebook outputs; execute it again afterward. Execute in a fresh
kernel and empty directory outside the checkout to expose hidden file reliance:

```python
from pathlib import Path
import nbformat
from nbclient import NotebookClient
p = Path('class_submission/Beacon_Outfitters_Midterm.ipynb')
n = nbformat.read(p, as_version=4)
Path('/tmp/beacon-clean-run').mkdir(exist_ok=True)
NotebookClient(n, timeout=900, kernel_name='python3',
    resources={'metadata': {'path': '/tmp/beacon-clean-run'}}).execute()
nbformat.write(n, p)
```

All solver runs have fixed seed 839 and two workers/threads; time-limited solver
behavior may vary by CPU. Gurobi allows up to 120 seconds per model; CP-SAT
comparison allows 60 seconds. Exact proof status, objective, bound and gap are
saved per run. Allocation ties can produce different but equally profitable
plans. Artifact figures and the truck calendar are generated from one base plan,
not assembled from different solver allocations. Fixed-policy profits can depend
on which tied base optimum was selected; check them against this saved schedule.

## Acceptance mapping

The public rubric assigns 10 points model correctness, 8 business insight and
7 briefing clarity. Independent constraints/objective checks and two-solver
agreement support correctness. The baseline, bottleneck, scheduling and cold-snap
results address the five business questions. Memo and timed five-slide briefing
address communication; team rehearsal and instructor assessment remain human.
The private Canvas rubric and absent Word brief cannot be certified.

There is no project license file because redistribution rights for course
material have not been established. Original data is attributed and unchanged.

# Methodology

## Decision workflow

1. Ingest five immutable CSV snapshots; validate schemas, types, finite ranges,
   key uniqueness, full store/SKU/week grids, precision and opening shelf stock.
2. Explore demand, available supply, unit margins, shelf tightness and delivery
   economics. Provided forecasts remain inputs rather than model predictions.
3. Formulate integer case shipments and binary visits with inventory, demand,
   shared shelf, truck and cumulative supply constraints.
4. Attempt Gurobi first; explicitly report availability failures and fall back
   to the comparable open-source CP-SAT formulation. Record objective, bound,
   gap, runtime and version. Never call a time-limited incumbent optimal.
5. Compare no-delivery and feasible heuristic benchmarks; test additional
   supply, alternating visits, ±20% late-horizon demand, and fixed-policy stress.
6. Recompute objective values from extracted decisions and check every constraint
   family independently. Reconcile financials, notebook outputs and reports.

## Reproduce

Python 3.12 is the tested runtime. From the repository root:

```sh
python -m pip install -r requirements.txt
python -m beacon_outfitters --data data/raw --output results
python scripts/build_reports.py
python scripts/build_notebook.py
python scripts/execute_notebook.py --workdir /tmp/beacon-clean-run
python -m pytest -q
python scripts/verify_project.py --notebook-results /tmp/beacon-clean-run/beacon_results
```

The run directory must be empty. The notebook installs dependencies and includes
all model source and checksum-verified CSV fallbacks; it needs no checkout,
manual uploads, credentials or paid runtime. Regeneration clears notebook
outputs, so execute afterward. Hosted Colab execution is distinct from local
fresh-kernel execution and is not claimed without a hosted run.

For an installable command, use `python -m pip install -e .` and then
`beacon --data data/raw --output results`. Gurobi, reports and developer tools
are optional extras in pyproject.toml; requirements.txt pins the full workflow.
The bundled Gurobi license supports this model's 1,584 variables. CP-SAT is the
open-source fallback. This is decision optimization, not predictive ML; RMSE,
classification accuracy and train/test splits are not appropriate model scores.

## Experiment records and interpretation

Every full pipeline run writes data/model SHA-256 hashes, runtime versions,
seed, workers, timestamp and scenario list in results/run_metadata.json.
Selected benchmark outputs are in results/tables; complete scenario allocations
are in results/plans; shareable plots are in results/figures. Reported objectives
are recomputed from decisions. Baseline-relative percentage uplift divides the
profit difference by the feasible heuristic's profit.

Seeds and worker counts are fixed; runtime and tied allocations can vary.
Comparisons certify the model on this dataset, not an unbiased estimate of live
business benefit. Deployment would require lead times, operational policy,
forecast calibration, multi-period rolling validation and data governance.

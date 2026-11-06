# Verification evidence

**Contributors: Anshuman · Inka · Juan Diego**

## Executed checks

- Standalone notebook: 13/13 code cells, zero errors,
  146.94 seconds in a fresh kernel outside the checkout.
- Automated tests: 17 passed,
  0 failed. See results/test_execution.json.
- Independent CLI and notebook results agree: True. All scenario profit
  claims, base calendar, SKU fills, decision changes and provenance reconcile.
- Independent feasibility and accounting checks pass for all returned plans.
- Gurobi base status: OPTIMAL; objective
  $213,503.10; bound $213,503.10;
  gap 0.00%; runtime 8.62s.
- CP-SAT base status: OPTIMAL; objective
  $213,503.10; bound $213,503.10;
  gap 0.00%; runtime 36.86s.
- All 17 recorded experiments report OPTIMAL within solver tolerances. Fixed
  heuristic/policy status certifies recourse under fixed decisions, not optimal
  heuristic allocations. Timings are machine observations, not performance claims.
- Decision brief: 3 pages. Analytics overview: 6 slides.
  PDF/deck monetary claims and the PDF store calendar match the saved results.
- Contributors appear at the top. Legacy framing checks pass for portfolio
  documentation, notebooks, PDF and slide text. Source attribution is retained.

## Reproducibility and scope

Five input files retain their original bytes. Input and model SHA-256 hashes,
versions, seed, workers and experiment settings are in results/run_metadata.json.
The offline notebook test blocks URL access and compares embedded datasets with
those original snapshots. The installable CLI entry point is verified.
Companion EDA and solver-comparison notebooks are executed separately.

The isolated run uses pinned dependencies in a fresh kernel; this is not a
separately provisioned hosted Colab runtime. Hosted Colab execution remains
unverified; access from this environment is blocked by its proxy policy.
Publication status: **published**.
See results/publication_check.json for published artifact verification when
available. The standalone link is:

https://colab.research.google.com/github/agrawalanshuman/beacon-outfitters-replenishment/blob/main/notebooks/Beacon_Outfitters_Optimization.ipynb

These are modeled benchmark outcomes, not realized company savings. No
predictive model, live retailer deployment or external posting is claimed.
LinkedIn copy is a draft. See assumptions.md, data_provenance.md and
AI_DISCLOSURE.md for interpretation, source credit and assistance details.

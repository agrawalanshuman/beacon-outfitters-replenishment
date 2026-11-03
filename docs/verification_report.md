# Verification report — November 3, 2026

## Workflow verified

The class notebook installs dependencies, loads five official CSVs without a
checkout or uploads, validates all schemas and key grids, solves and verifies
the base model, feasible baselines, supply additions, scheduling policy and
cold-snap scenarios, then displays shipment tables, financials and charts.
The inline source matches the standalone Python computation pipeline.

## Actual execution evidence

- Python 3.12.14. Exact dependencies are in requirements.txt.
- Final standalone execution: **13/13 code cells**, **0 errors**,
  **148.45 seconds**, fresh kernel in an initially empty directory outside
  the checkout. The interpreter's dependencies were installed/pinned; this was
  not a separately provisioned hosted Google Colab runtime.
- **15 tests passed, 0 failed**, one unrelated anyio pytest plugin deprecation
  warning. Tests exercise known-optimum small models, DC carry-forward, holding
  versus truck costs, no deliveries, fifth-unit demand, invalid data/constraint
  corruption, baseline/results accounting and embedded offline CSV snapshots.
- Offline data integration test blocks all URL access and loads all five
  identical embedded datasets, comparing each to its original CSV snapshot.
- Gurobi 13.0.3 base: OPTIMAL, $213,503.10, 8.99 seconds, bound $213,503.10,
  0% gap. CP-SAT 9.15.6755 base: OPTIMAL, same objective, 23.41 seconds,
  same bound and 0% gap. These are recorded pipeline runtimes, not benchmarks.
- All 17 recorded runs report OPTIMAL (within solver tolerances). Fixed-policy
  and naive-run certification concerns recourse with fixed shipment decisions;
  it does not certify that the heuristic chose optimal shipments.
- Independent profit recomputation and all constraint-family checks pass.
  Full evidence is in results/feasibility_checks.csv and solver_comparison.csv.
- Original CSVs match the official pinned Git revision byte for byte; notebook
  downloads and embedded fallbacks verify SHA-256 before parsing.
- The notebook's independent run matches all saved scenario profits/statuses,
  the base truck calendar, per-SKU fills and scenario decision-change tables.
- Memo: **3 pages** (limit five); deck: **5 slides**;
  presenter script: **586 words**. Extracted memo/deck text agrees
  with notebook and pipeline monetary claims; the memo store/week calendar
  matches saved results. Memo pages were rendered and inspected; the PDF embeds
  readable fonts. PowerPoint structure/text were checked, not rendered in an
  actual PowerPoint application.
- Both companion analysis notebooks were executed successfully.
- git diff --check passes. The completed project was committed and pushed to
  GitHub main with explicit user authorization. No Canvas upload was performed.
- A targeted scan found no common private-key/GitHub-token/AWS-access-key
  signatures in project files. The original history and new project files
  were inspected; no credentials were introduced. This is not an exhaustive secret audit.

## Business reconciliations

Base contribution is $221,013.00 sales margin minus $1,399.90 holding and
$6,110.00 delivery cost = **$213,503.10**. Ship **512 cases / 4,028 units** on
**27 visits**, sell 4,598 units, lose 185 forecast units, fill 96.13% of demand.
No-delivery profit is $35,599.75; feasible naive profit is $207,379.20. Uplifts
are $177,903.35 and $6,123.90 respectively. One hundred extra J200 parkas in
week 1 adds $10,169.20 after reoptimization. Forced alternate-week policy earns
$210,379.10, a $3,124.00 reduction. The lower/higher demand reoptimized profits
are $196,074.61 / $228,223.15; fixed-base-policy profits are
$192,979.83 / $221,594.99. All accounting conventions are consistent.

## Publication and external limits

**Published notebook; hosted Colab execution unverified:**
https://colab.research.google.com/github/agrawalanshuman/beacon-outfitters-replenishment/blob/main/class_submission/Beacon_Outfitters_Midterm.ipynb

Owner and branch were detected from Git origin and authoritative remote symbolic
HEAD. The user explicitly authorized publication, and the complete project was
pushed to main. The public raw notebook returns **HTTP 200** and matches the
local notebook byte for byte. See results/publication_check.json for the verified
revision and SHA-256. Direct Colab access was blocked by the environment proxy
(CONNECT 403); no hosted Colab execution is claimed. Open the badge in a browser,
select Runtime → Run all and check every cell to complete hosted verification.

The live course website was denied by network policy; its official case,
syllabus and deadline source and Sessions 2–7 were inspected via the public
course Git repository. The Word brief was absent. Canvas file/rubric details
were not accessible. The public case permits optional slides; the team must
confirm private upload requirements and review all deliverables before Canvas
submission. The submission remains NEEDS REVIEW for these external steps.

## Reproduction and artifacts

Use scripts/build_notebook.py to regenerate the standalone notebook (clears its
outputs), scripts/execute_notebook.py for a fresh-kernel run,
scripts/build_submission.py for memo/slides/READMEs from verified results, and
scripts/verify_submission.py --notebook-results <run-directory>/beacon_results
for a cross-run artifact audit. See docs/methodology.md for commands and
assumptions.md for source interpretation. Exact files are listed in
[the project inventory](file_inventory.txt).

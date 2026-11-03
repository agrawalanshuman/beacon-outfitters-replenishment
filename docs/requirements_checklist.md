# Requirements traceability (written before implementation)

- [x] Self-contained Colab notebook: install packages, fetch five real CSVs without cloning or uploads, solve and render results.
- [x] Verify official case and Session 7 formulation; record inaccessible sources and absent uploaded brief.
- [x] Validate 12 stores, 8 SKUs, four weeks and 384/96/32 fact rows.
- [x] Whole case packs, demand balance, pre-sales aggregate shelf capacity, inventory flow, truck activation, cumulative DC limits.
- [x] Contribution profit: margin less inventory holding and truck visits; independently verify all constraints.
- [x] Try Gurobi and compare with an open source integer solver; distinguish feasible and proven optimal.
- [x] Do-nothing and feasible forecast heuristic baselines; extra 100 units per SKU; alternating-week schedule; cold-snap scenarios and fixed-policy checks.
- [x] Notebook execution, tests, results CSVs and charts; memo/slides generated from the same verified results.
- [x] Detect Git owner/default branch; badges in both READMEs; mark unpublished URL pending; publish only with authorization.
- [x] Explain limits: local execution is not a hosted Colab test; missing Canvas/brief prevents full rubric certification.

## Evidence and outstanding acceptance checks

- Self-contained notebook: 13/13 code cells completed, zero errors, fresh kernel
  in an empty directory outside the checkout; 148.45 seconds. This is local
  execution with installed/pinned dependencies, not a clean hosted Colab session.
- Gurobi 13.0.3 and CP-SAT 9.15.6755 prove base profit $213,503.10.
- All 17 recorded solves prove their respective optima (fixed-policy/heuristic
  status certifies sales recourse under fixed shipments, not heuristic allocation).
- Five CSVs match the official pinned course revision byte for byte.
- Feasibility, independent accounting, fractional demand, corruption and offline
  snapshot tests pass. Notebook and local pipeline financials/calendar agree.
- Memo: 3 pages; deck: 5 slides; presenter script: 586 words.
- Both READMEs have the detected-owner/default-branch Colab badge and Run all steps.
- GitHub publication was explicitly authorized and completed; the public raw
  notebook returns HTTP 200 and matches the local file byte for byte.
- [x] Publish with user authorization and verify the public notebook download.
- [ ] Verify a hosted Colab run. Direct Colab access from this environment is
  blocked by the proxy (CONNECT 403); local execution remains verified.
- [ ] Team must confirm private Canvas requirements and defend/rehearse the work.
- [ ] Word brief 839_midterm_brief.docx is absent; compare it if later supplied.

No license file was added because rights to relicense the course content were
not established. Companion analysis notebooks are executed; no empty files
were created. Full generated file list is in docs/file_inventory.txt.

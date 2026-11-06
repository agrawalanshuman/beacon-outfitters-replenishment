# Assumptions and scenario design

The model is a deterministic retail benchmark. Demand forecasts are supplied
inputs, not predictions trained by this project. Four-week contribution is a
modeled accounting outcome, not realized revenue, cash flow or audited savings.

- Store shelf capacity is shared across SKUs and enforced immediately after
  delivery, before that week's sales. Trucks have actual unit capacities.
- Unused DC release carries forward; future releases cannot be borrowed.
- Shipments are whole case packs. Sales and remaining stock are continuous in
  the MILP. The CP-SAT model uses exact fifth-unit quantities and integer cents.
- Margin is retail price minus unit cost, including sales from opening stock.
  Unit costs are counted once. No terminal salvage value, backorders, routing,
  warehouse storage limit, service floor or supplier lead time is invented.
- Demand stress: multiply every SKU's week 3–4 forecast by 0.8 or 1.2. Weeks 1–2
  are unchanged. Fractional demand is retained exactly, not rounded. These are
  direct ±20% tests, not a probabilistic forecast interval.
- Perfect-foresight scenarios reoptimize independently. Fixed-policy scenarios
  hold base shipments and visits constant, adjusting sales and remaining stock.
  These evaluate different questions and are reported separately.
- Extra-supply experiments add 100 units of one SKU at the start of week 1,
  identically across SKUs. Reported gains are finite reoptimization values, not
  LP shadow prices, purchase prices or returns net of a new supplier premium.
- Alternating-week policy: each store chooses either weeks 1/3 or weeks 2/4,
  and can skip a visit. It is a constrained comparison, not a routing solution.
- No-delivery baseline optimizes sales from opening stock with zero truck costs.
- Feasible heuristic: each week add DC releases, process stores in ascending ID,
  prioritize descending unit margin (SKU-ID ties), request cases for current
  demand net of stock, round up requests, and cap by remaining DC, shelf and
  truck capacity. Fixed-shipment sales recourse is then optimized consistently.
  This is a specified benchmark, not an observed company policy.

All scenarios use the same accounting and constraints. Summary differences
versus baselines refer to the *base-demand* benchmark, even for stress scenarios;
use fixed-policy comparisons to assess forecast adaptation. Equivalent optimum
allocations may differ across runs; their fixed-policy stress performance can
also differ. Solver runtime depends on hardware, versions and time limits.

See [data provenance](data_provenance.md) for original source credit and hashes.

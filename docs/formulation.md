# Four-week replenishment formulation

For stores s, SKUs k and weeks w, choose integer cases c, binary visits y,
and nonnegative continuous sales a, lost demand l, and ending inventory i.
Let p be case-pack units, m retail minus unit cost, h holding cost per unit/week,
f forecast, I opening inventory, A weekly DC release, C shelf units, T truck units,
and v cost per visit.

Maximize sum(m[k] a[s,k,w] - h[k] i[s,k,w]) - sum(v[s] y[s,w]).

- Flow: i_previous + p[k] c[s,k,w] = a[s,k,w] + i[s,k,w], using I in week 1.
- Demand: a[s,k,w] + l[s,k,w] = f[s,k,w].
- Shelf: sum_k(i_previous + p[k] c[s,k,w]) <= C[s]. This is the shared shelf after arrival BEFORE sales.
- Truck: sum_k p[k] c[s,k,w] <= T[s] y[s,w]. Actual capacity is the linking bound.
- DC: sum_{s,t<=w} p[k] c[s,k,t] <= sum_{t<=w} A[k,t].

Unit costs occur once, inside margin. Opening stock uses the benchmark margin
convention; this is not a cash-flow or sunk-cost valuation of opening stock.
No end-of-horizon salvage, backorders, routing, or service floor is invented.

## Why integer sales are comparable

With cases and visits fixed, margins are positive and constant across weeks,
and holding costs are positive. Selling an available unit now rather than
withholding it for later cannot reduce total sales revenue, saves holding cost,
and frees shelf space. Therefore an optimal recourse policy sells
`min(available units, forecast)` in each week for each SKU. This exchange
argument guarantees an integral optimum for integer data, and an exact
fifth-unit optimum for the scaled ±20% scenarios. No general multicommodity
network integrality assumption is needed. Gurobi keeps sales/lost/inventory
continuous in the MILP formulation; CP-SAT represents them in fifths,
with currency in cents. We compare objectives and independently check numerical
integrality in the base data. This argument relies on the benchmark's positive,
time-invariant margins and holding costs, not arbitrary future variants.

The base model has 1,584 variables: 384 each for cases, sales, lost, inventory,
and 48 visits. Gurobi's bundled restricted license can solve this small benchmark
model without an API key. If unavailable, CP-SAT solves the same scaled model.
A time-limited incumbent is reported as feasible with its bound and gap.

# Session 8 one-page model outline

Decision owner: merchandising VP. Decide cases shipped by store, SKU and week,
and whether each store receives a truck. Sales, unmet demand and ending stock
follow those decisions.

Maximize four-week sales margin less holding and delivery costs. Margins include
unit cost once and follow the case's accounting for opening stock.

1. Inventory conservation: opening/carried inventory plus whole-pack arrivals
   equals sales plus ending stock.
2. Sales plus lost demand equals forecast. No future backlog or negative stock.
3. All SKU stock after arrival fits the store's shared shelf before selling.
4. Delivered units fit the actual truck, and a delivery activates its visit cost.
5. Cumulative DC shipments cannot exceed cumulative SKU releases.

Cases are nonnegative integers; visits are binary; sales/lost/stock are
continuous. Case-specific recourse has an integral optimum for integer data.
Gurobi first, exact-scaled CP-SAT independently, with status and bounds recorded.

Business questions: value versus no deliveries/naive allocation; highest-value
SKU with 100 more units in week 1; store-specific consolidation; weeks 3–4 ±20%
forecast changes and whether the original shipment policy still performs well.

Check-in question: should management prefer a robustness tie-break among base
plans with equal contribution profit before locking the delivery calendar?

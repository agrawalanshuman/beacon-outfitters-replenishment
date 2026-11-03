# Sources and assumptions

Read the case page source `src/pages/case.astro`, syllabus data, deadlines, and
Session 2–7 notebooks from official course Git commit
`1e2b0374818759215a61475fe5eeb3af000f8263`.
Direct requests to https://isom-839.vercel.app/case and /syllabus were denied by
the environment network policy; the public GitHub source was used instead.
The initially supplied notebook URLs omit session subdirectories; current
notebooks are under `public/session-02/` through `public/session-07/`.
`839_midterm_brief.docx` was not supplied. Private Canvas instructions were not
accessible; the public case requires a notebook, memo (<=5 pages), and in-class
briefing; slides are optional. Confirm Canvas file rules with the team.
The public deadline is November 4, 2026, 7:40 PM America/New_York.

The case asks if the week 3–4 forecast is 20% too high or low. We use original
forecast times 0.8 or 1.2 for ALL SKUs in weeks 3–4, leaving weeks 1–2 untouched.
These are direct ±20% stress tests, not division by 1.2 or 0.8. Fractional
forecast units are retained exactly in fifths, as expected-demand planning units.
No SKU-specific cold-snap increment is supplied, so none is invented.

Extra supply: add 100 units of one SKU at the START of WEEK 1; carry forward
unused units. Every SKU uses the same release timing. Gain is a finite
reoptimization value, not a mixed-integer shadow price or supplier net price.
The alternating schedule lets each store choose odd or even weeks, with at most
two visits. Fixed-policy scenarios fix both base shipments and visits and allow
sales/inventory to adapt. They may be infeasible if reduced sales fill shelves;
we do not relax capacity to force feasibility.

Naive heuristic: each week, add DC releases, then process stores by ascending
store ID. Within each store, prioritize descending unit margin (SKU ID ties).
Request enough cases to cover this week's demand net of opening/ending stock,
round requests up to cases, and cap allocations by remaining DC, shelf and truck
space. Sell up to demand, carry excess. Optimize sales recourse with those fixed
shipments for fair accounting. It is feasible but not an optimized allocation.

No license is imposed: course data/content attribution does not grant us a
right to relicense those sources. Raw files retain their original bytes.

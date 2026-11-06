# Share the project on LinkedIn

## Suggested post

How do you turn a demand forecast into an executable replenishment plan?

Sharing Beacon Outfitters, a retail decision-science project developed with
Inka and Juan Diego. We modeled whole-case shipments and store visits across
12 stores, 8 SKUs and a four-week horizon, subject to inventory, shelf, truck
and supply constraints.

On the benchmark data, the verified plan achieves:
• $213,503.10 modeled contribution over four weeks
• 2.95% improvement over a feasible forecast-driven heuristic
• 96.13% demand fill rate with 27 planned visits

We also tested ±20% late-horizon demand, fixed-plan robustness and the value of
additional supply. Gurobi and OR-Tools CP-SAT independently verified the base
optimum, supported by automated data, feasibility and accounting checks.

The key lesson: the best allocation and delivery calendar should be optimized
together, and adapting to new demand is different from testing a fixed plan.

These are modeled benchmark outcomes, not realized company savings.
ChatGPT helped debug and refine explanations; Codex also assisted implementation,
testing and documentation. Full disclosure is in the repository.

Code, notebook and reproducible results:
https://github.com/agrawalanshuman/beacon-outfitters-replenishment

Contributors: Anshuman · Inka · Juan Diego

#DataScience #OperationsResearch #SupplyChainAnalytics

## Posting steps

1. Open LinkedIn → Start a post. Attach results/figures/overview.png as the main
   image, then paste the suggested post above. Review the numbers and voice.
2. Tag Inka and Juan Diego using their actual profiles. Keep the benchmark
   qualifier so modeled improvements are not confused with live business savings.
3. Publish, then open the post once to confirm the image and repository link.
4. Add the repository under Profile → Add profile section → Recommended →
   Add featured → Add a link. UI labels may vary. Use the title
   “Beacon Outfitters | Retail Replenishment Optimization”.
5. Optionally add a Projects entry naming all three contributors, with Python,
   mathematical optimization, scenario analysis and reproducibility as skills.

No LinkedIn post has been published automatically. Hosted Colab execution
remains separate from the locally verified notebook run.

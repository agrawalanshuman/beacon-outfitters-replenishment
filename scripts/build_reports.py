"""Generate portfolio documents and shareable copy from verified run outputs."""
from pathlib import Path
import json
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from matplotlib import get_data_path
from pptx import Presentation
from pptx.util import Inches, Pt

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results';T=R/'tables';D=ROOT/'reports';D.mkdir(exist_ok=True)
s=pd.read_csv(T/'financial_summary.csv').set_index('scenario')
tr=pd.read_csv(T/'truck_schedule.csv');b=pd.read_csv(T/'sku_bottleneck.csv')
assert pd.read_csv(T/'feasibility_checks.csv').passed.all()
assert (s.status=='OPTIMAL').all(), 'Review feasible-only results before publishing numerical claims'
v=s.loc['base'];gain=v.profit-s.loc['naive','profit'];pct=100*gain/s.loc['naive','profit']
alt=v.profit-s.loc['alternate_week','profit'];money=lambda x:f'${x:,.2f}'
contributors='Anshuman · Inka · Juan Diego'
link=json.loads((ROOT/'docs/colab_link.json').read_text())['url']
repo='https://github.com/agrawalanshuman/beacon-outfitters-replenishment'

fonts=Path(get_data_path())/'fonts/ttf'
pdfmetrics.registerFont(TTFont('BeaconSans',str(fonts/'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('BeaconBold',str(fonts/'DejaVuSans-Bold.ttf')))
styles=getSampleStyleSheet()
for st in styles.byName.values():st.fontName='BeaconBold' if st.name=='Title' or 'Heading' in st.name else 'BeaconSans'
story=[]
def paragraph(text,style='BodyText'):
    story.extend([Paragraph(text,styles[style]),Spacer(1,10)])
def table(rows,widths):
    a=Table([[Paragraph(str(z),styles['BodyText']) for z in row] for row in rows],colWidths=widths,repeatRows=1)
    a.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E3EEF5')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.35,colors.lightgrey),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.extend([a,Spacer(1,12)])
paragraph('Contributors: '+contributors)
paragraph('Beacon Outfitters','Title');paragraph('Retail replenishment | Decision brief','Heading1')
paragraph(f"Plan {int(v.cases)} cases ({int(v.units_shipped):,} units) on {int(v.visits)} visits across 12 stores and four weeks. The verified benchmark yields {money(v.profit)} in modeled contribution, {money(gain)} ({pct:.2f}%) above a feasible forecast-driven heuristic.")
paragraph('Decision: allocate scarce supply, choose delivery weeks and balance sales margin against stock holding and truck costs. These are benchmark outcomes, not realized company savings.')
table([['Decision metric','Verified result'],['Modeled contribution',money(v.profit)],['Heuristic uplift',money(gain)+f' / {pct:.2f}%'],['Demand fill rate',f'{v.fill_rate:.2%}'],['Best +100-unit opportunity',f'J200 parkas: {money(b.iloc[0].profit_gain)}'],['Forced alternate-week loss',money(alt)]],[245,245])
paragraph('Recommended action','Heading2')
paragraph(f"Use the store-specific delivery calendar rather than a blanket alternating-week rule. Evaluate 100 additional J200 parkas released in week 1: their gross incremental contribution is {money(b.iloc[0].profit_gain)} before any new procurement premium. Refresh the allocation when demand or releases change.")
story.append(Image(str(R/'figures/baseline.png'),width=490,height=211))
story.append(PageBreak())
paragraph('Uncertainty and execution','Heading1')
table([['Weeks 3–4 demand','Reoptimized contribution','Base shipments retained']]+[[label,money(s.loc[a,'profit']),money(s.loc[c,'profit'])] for label,a,c in [('−20%','lower','lower_fixed'),('Base','base','base'),('+20%','higher','higher_fixed')]],[150,170,170])
paragraph('The stress tests change all eight SKUs in weeks 3–4 and retain exact fractional demand. Reoptimization is perfect-foresight adaptation; fixed-policy evaluation allows sales and remaining inventory to adjust while shipments and visits stay fixed. Neither is a forecast confidence interval.')
story.append(Image(str(R/'figures/sensitivity.png'),width=490,height=175))
paragraph('Store-specific delivery schedule','Heading2')
table([['Store','Visit weeks','Units']]+[[store,', '.join(str(w) for w in a.query('visit==1').week),int(a.units_shipped.sum())] for store,a in tr.groupby('store_id')],[100,285,105])
story.append(PageBreak())
paragraph('Why the result is credible','Heading1')
paragraph(f"Contribution reconciles to {money(v.sales_margin)} sales margin less {money(v.holding_cost)} holding and {money(v.delivery_cost)} visits. Gurobi and CP-SAT independently prove the same base objective. Every extracted plan is checked for flow balance, demand, shared shelf limits, truck activation, cumulative supply and whole packs.")
paragraph('Data and model','Heading2')
paragraph('Five validated CSVs describe 12 stores, 8 SKUs and 4 weeks. The formulation has 1,584 variables with integer cases and binary visits. Actual truck capacity supplies the linking bound. The pipeline records input/model hashes, runtime versions, solver bounds, gaps and independent verification evidence. Provided demand forecasts are inputs, not predictions trained here.')
paragraph('Scope and limitations','Heading2')
paragraph('This is a deterministic retail benchmark. Opening-stock sales follow the margin convention; unit costs are counted once. No routing, supplier lead times, forecast learning, terminal salvage or operational service floor is assumed. Time limits and tied allocations can affect solutions on different hardware. Deployment needs rolling validation, calibrated uncertainty and operational review.')
paragraph('Contributors and assistance','Heading2');paragraph(contributors)
paragraph('ChatGPT assisted debugging and technical explanations. OpenAI Codex assisted implementation, automated tests, documentation and artifact generation. Numerical claims are solver-derived and independently checked; contributors remain responsible for interpretation.')
paragraph('Source: Hasan Arslan’s public benchmark data and modeling reference; full credit, original revision and hashes are in docs/data_provenance.md.')
SimpleDocTemplate(str(D/'Beacon_Outfitters_Decision_Brief.pdf'),pagesize=(612,792),leftMargin=55,rightMargin=55,topMargin=40,bottomMargin=40,title='Beacon Outfitters | Retail Replenishment',author=contributors).build(story)

prs=Presentation();prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5)
def slide(title,lines,image=None):
    a=prs.slides.add_slide(prs.slide_layouts[6])
    for x,y,w,h,text,size,bold in [(.55,.2,12.3,.4,'CONTRIBUTORS: '+contributors,12,False),(.55,.8,12.1,1,title,29,True)]:
        t=a.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)).text_frame;t.word_wrap=True;t.text=text
        for p in t.paragraphs:p.font.size=Pt(size);p.font.bold=bold
    f=a.shapes.add_textbox(Inches(.65),Inches(2),Inches(5.1 if image else 11.8),Inches(4.9)).text_frame;f.word_wrap=True
    for i,text in enumerate(lines):
        p=f.paragraphs[0] if i==0 else f.add_paragraph();p.text=text;p.font.size=Pt(21);p.space_after=Pt(18)
    if image:a.shapes.add_picture(str(R/'figures'/image),Inches(6.2),Inches(2),width=Inches(6.55))
slide('Retail replenishment as a decision-science problem',['12 stores · 8 SKUs · 4 weeks','Choose whole-case shipments and delivery visits under real capacity limits.','Benchmark analysis: modeled outcomes, not realized company savings.'])
slide('Validated data → constrained decisions',['Five immutable CSVs with schema and identifier checks.','MILP: stock flow, demand, shared shelf, trucks and cumulative supply.','Independent Gurobi / CP-SAT comparison, objective bounds and accounting checks.'])
slide('Optimized benchmark: '+money(v.profit),[f'{money(gain)} / {pct:.2f}% above a feasible heuristic',f'{v.fill_rate:.2%} demand filled',f'{int(v.cases)} cases · {int(v.visits)} visits'],'baseline.png')
slide('Allocate supply and consolidate deliberately',[f'100 extra J200 parkas: +{money(b.iloc[0].profit_gain)} gross contribution',f'Blanket alternate-week deliveries cost {money(alt)}.','Approve the detailed store/week calendar.'],'truck_calendar.png')
slide('Separate adaptation from fixed-policy robustness',[f'Lower demand: {money(s.loc["lower","profit"])} reoptimized',f'Higher demand: {money(s.loc["higher","profit"])} reoptimized','Weeks 3–4 change ±20%; original deliveries evaluated separately.'],'sensitivity.png')
slide('Reproduce, inspect and extend',['Standalone Colab notebook; installable Python CLI; tested input and constraint checks.','Use forecasts as inputs; validate rolling decisions before deployment.','ChatGPT: debugging and explanations. Codex: implementation, testing and documentation.','Source credit and complete reproducibility evidence are in the repository.'])
prs.save(D/'Beacon_Outfitters_Analytics_Overview.pptx')

badge=f'[![Open in Google Colab](https://colab.research.google.com/assets/colab-badge.svg)]({link})'
(ROOT/'README.md').write_text(f'''**Contributors: {contributors}**

# Beacon Outfitters | Retail Replenishment Optimization

A reproducible decision-science project that converts demand forecasts and
capacity constraints into shipment recommendations, delivery schedules and
quantified inventory trade-offs.

{badge}

![Decision analytics overview](results/figures/overview.png)

## Results at a glance

| Benchmark metric | Verified result |
|---|---:|
| Four-week modeled contribution | **{money(v.profit)}** |
| Improvement over feasible heuristic | **{money(gain)} / {pct:.2f}%** |
| Demand fill rate | **{v.fill_rate:.2%}** |
| Shipment / visit plan | **{int(v.cases)} cases · {int(v.visits)} visits** |
| Gross value of 100 more J200 parkas, week 1 | **{money(b.iloc[0].profit_gain)}** |

These are modeled benchmark outcomes, **not realized company savings**. The
heuristic is a specified feasible policy, not an observed business process.
All results are regenerated from one verified pipeline. Gurobi and CP-SAT
independently prove the same base objective; bounds, gaps and timings are in
[solver evidence](results/tables/solver_comparison.csv).

## Business question

Across 12 stores, eight SKUs and four weeks, how many cases should ship, where
and when? Stock is limited, shelves and trucks have finite capacity, deliveries
carry fixed costs, and demand shifts late in the planning horizon.

The model maximizes contribution: sales margin minus holding and visit costs.
Integer case packs, binary visits, inventory conservation, shared shelf space
**before sales**, truck capacity and cumulative DC releases are enforced.
Provided forecasts are inputs; this project does not train a forecasting model.
See [formulation](docs/formulation.md) and [scenario assumptions](docs/assumptions.md).

## Analysis and decision support

- Data quality: schemas, numeric precision, key grids, missingness and supply integrity.
- Benchmark evaluation: no deliveries and a feasible forecast-driven heuristic.
- Allocation: full case-level shipment plan and store/week delivery calendar.
- Marginal opportunity: separate 100-unit supply additions for every SKU.
- Uncertainty: ±20% demand in weeks 3–4, separately reoptimized and evaluated
  under the fixed base shipment policy.
- Scheduling: constrained alternating-week policy versus store-specific visits.
- Verification: independent constraint/accounting checks and two-solver agreement.

| Policy / experiment | Modeled contribution |
|---|---:|
| Optimized base | {money(v.profit)} |
| Feasible heuristic | {money(s.loc['naive','profit'])} |
| No deliveries | {money(s.loc['do_nothing','profit'])} |
| Forced alternating-week deliveries | {money(s.loc['alternate_week','profit'])} |
| Lower demand: reoptimized / fixed shipments | {money(s.loc['lower','profit'])} / {money(s.loc['lower_fixed','profit'])} |
| Higher demand: reoptimized / fixed shipments | {money(s.loc['higher','profit'])} / {money(s.loc['higher_fixed','profit'])} |

Replanning improves lower-demand contribution by {money(s.loc['lower','profit']-s.loc['lower_fixed','profit'])}
and higher-demand contribution by {money(s.loc['higher','profit']-s.loc['higher_fixed','profit'])}.
A blanket alternating-week rule loses {money(alt)} versus the optimized calendar.
The extra-parka opportunity is gross incremental contribution before a new
procurement premium, not a supplier price or a linear-programming shadow price.

## Run in Google Colab

Open the badge, select a free CPU runtime, then **Runtime → Run all**.
The notebook installs pinned dependencies, loads five checksum-verified datasets
with embedded fallbacks, solves the experiments and displays tables and charts.
No clone, upload, private API key or paid runtime is needed.

{link}

Local fresh-kernel execution is verified independently of hosted Colab
execution. See [verification](docs/verification_report.md) for current evidence
and publication status.

## Reproduce locally

```sh
git clone {repo}.git
cd beacon-outfitters-replenishment
python -m pip install -r requirements.txt
python -m beacon_outfitters --data data/raw --output results
python scripts/build_reports.py
python -m pytest -q
```

Python 3.12 is tested. Install `pip install -e .` to use the `beacon` command.
Gurobi is attempted first; its bundled small-model license handles this model.
If unavailable, the comparable integer CP-SAT implementation is used explicitly.
Time-limited solutions retain their actual status, objective bound and gap.
[Full reproduction steps](docs/methodology.md) cover notebook regeneration,
isolated execution and report reconciliation.

## Project map

```text
beacon_outfitters/  reusable validation, modeling, scenarios, reporting and CLI
notebooks/         standalone optimization notebook, EDA and solver comparison
data/raw/          five unchanged source CSVs
results/tables/    financials, shipments, shortages, scenarios and feasibility
results/plans/     complete allocations for every solved experiment
results/figures/   decision dashboard and shareable charts
reports/           decision brief PDF and analytics overview deck
scripts/           reproducible notebook/report builders and verification
tests/             small known-optimum problems and data/result checks
docs/              formulation, assumptions, provenance and AI disclosure
```

## Evidence, limitations and source credit

The pipeline records data/model SHA-256 hashes, runtime versions, random seed,
workers and scenario definitions in [run metadata](results/run_metadata.json).
[Verification](docs/verification_report.md) distinguishes tested capabilities
from unverified hosted execution. Full results include every nonzero shipment,
weekly financials, per-SKU fills and scenario decision changes.

This is deterministic benchmark analysis. Deployment would need calibrated
forecasts, supplier lead times, routing/service policies and rolling operational
validation. Margin accounting is not cash flow, and the same-input optimum is
not evidence of unbiased live business uplift.

Original benchmark data and modeling reference: **Hasan Arslan**.
[Data provenance](docs/data_provenance.md) preserves source credit, revision,
data dictionary and original hashes. Raw source files are unchanged.

**AI assistance:** ChatGPT helped with debugging and technical explanations;
OpenAI Codex assisted implementation, testing, documentation and artifact
creation. Contributors remain responsible for reviewing the work.
[Full disclosure](docs/AI_DISCLOSURE.md).

## Explore and share

- [Standalone notebook](notebooks/Beacon_Outfitters_Optimization.ipynb)
- [Decision brief](reports/Beacon_Outfitters_Decision_Brief.pdf)
- [Analytics overview deck](reports/Beacon_Outfitters_Analytics_Overview.pptx)
- [LinkedIn post draft and posting steps](docs/linkedin_post.md)
''')
(ROOT/'docs/linkedin_post.md').write_text(f'''# Share the project on LinkedIn

## Suggested post

How do you turn a demand forecast into an executable replenishment plan?

Sharing Beacon Outfitters, a retail decision-science project developed with
Inka and Juan Diego. We modeled whole-case shipments and store visits across
12 stores, 8 SKUs and a four-week horizon, subject to inventory, shelf, truck
and supply constraints.

On the benchmark data, the verified plan achieves:
• {money(v.profit)} modeled contribution over four weeks
• {pct:.2f}% improvement over a feasible forecast-driven heuristic
• {v.fill_rate:.2%} demand fill rate with {int(v.visits)} planned visits

We also tested ±20% late-horizon demand, fixed-plan robustness and the value of
additional supply. Gurobi and OR-Tools CP-SAT independently verified the base
optimum, supported by automated data, feasibility and accounting checks.

The key lesson: the best allocation and delivery calendar should be optimized
together, and adapting to new demand is different from testing a fixed plan.

These are modeled benchmark outcomes, not realized company savings.
ChatGPT helped debug and refine explanations; Codex also assisted implementation,
testing and documentation. Full disclosure is in the repository.

Code, notebook and reproducible results:
{repo}

Contributors: {contributors}

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
''')
print('Generated decision brief, six-slide deck, README and LinkedIn draft from verified results.')

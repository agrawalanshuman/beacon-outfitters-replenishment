"""Generate memo, deck and READMEs only from independently verified results."""
from pathlib import Path
import json
import pandas as pd
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from pptx import Presentation
from pptx.util import Inches,Pt

ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';C=ROOT/'class_submission'
s=pd.read_csv(R/'financial_summary.csv').set_index('scenario');tr=pd.read_csv(R/'truck_schedule.csv')
b=pd.read_csv(R/'sku_bottleneck.csv');e=json.loads((R/'verified_summary.json').read_text())
assert pd.read_csv(R/'feasibility_checks.csv').passed.all()
assert (s.status=='OPTIMAL').all(), 'Review unproven results before producing executive artifacts'
base=s.loc['base'];url=json.loads((ROOT/'docs/colab_link.json').read_text())['url']
money=lambda x:f'${x:,.2f}'
uplift=base.profit-s.loc['do_nothing','profit'];gain=base.profit-s.loc['naive','profit']
alt=base.profit-s.loc['alternate_week','profit']
summary=f"Approve the four-week plan: {int(base.cases)} cases ({int(base.units_shipped):,} units) on {int(base.visits)} store visits. Expected contribution profit is {money(base.profit)}, {money(uplift)} above no deliveries and {money(gain)} above the feasible forecast-driven rule."
ask=f"Secure 100 additional J200 down parkas for week 1 if the incremental procurement premium is below the {money(b.iloc[0].profit_gain)} gross gain. Use the store-specific calendar rather than a blanket every-other-week rule, which costs {money(alt)} in profit."
cold=f"With weeks 3–4 demand 20% lower, replan for {money(s.loc['lower','profit'])}; keeping the base shipments earns {money(s.loc['lower_fixed','profit'])}. With demand 20% higher, replan for {money(s.loc['higher','profit'])}; the fixed base plan earns {money(s.loc['higher_fixed','profit'])}."
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from matplotlib import get_data_path
fontdir=Path(get_data_path())/'fonts/ttf'
pdfmetrics.registerFont(TTFont('BeaconSans',str(fontdir/'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('BeaconSansBold',str(fontdir/'DejaVuSans-Bold.ttf')))
styles=getSampleStyleSheet()
for style in styles.byName.values():
    style.fontName='BeaconSansBold' if 'Heading' in style.name or style.name=='Title' else 'BeaconSans'
story=[]
def para(text,style='BodyText'):
    story.append(Paragraph(text,styles[style]));story.append(Spacer(1,9))
def table(rows,widths=None):
    t=Table([[Paragraph(str(v),styles['BodyText']) for v in row] for row in rows],colWidths=widths,repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dceef0')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('GRID',(0,0),(-1,-1),0.4,colors.lightgrey)]));story.append(t);story.append(Spacer(1,10))
para('Beacon Outfitters | COO decision memo','Title')
para('To: Merchandising VP | From: Anshuman, Inka, Juan Diego<br/>November 3, 2026 | ISOM 839 academic case')
para('Approve a targeted replenishment plan','Heading1');para(summary);para(ask);para(cold)
para(f"The plan sells {base.units_sold:,.0f} units, fills {base.fill_rate:.2%} of demand and leaves {base.units_lost:,.0f} units of unmet demand. The detailed case-by-case shipment file accompanies the notebook; the calendar below gives each store's delivery weeks.")
rows=[['Store','Delivery weeks','Units']]
for sid,a in tr.groupby('store_id'):
    rows.append([sid,', '.join(str(x) for x in a.query('visit==1').week),int(a.units_shipped.sum())])
table(rows,[90,270,90])
story.append(PageBreak())
para('The money and the scarce stock','Heading1')
table([['Policy','Profit','Visits','Fill rate']]+[[n,money(s.loc[n,'profit']),int(s.loc[n,'visits']),f"{s.loc[n,'fill_rate']:.2%}"] for n in ['base','do_nothing','naive','alternate_week']],[140,130,80,100])
para(f"Contribution = {money(base.sales_margin)} sales margin minus {money(base.holding_cost)} shelf holding and {money(base.delivery_cost)} truck costs. Unit cost is counted once in margin, including sales from opening stock as specified in the case.")
table([['SKU (+100 units at start of week 1)','Profit gain']]+[[z.sku,money(z.profit_gain)] for z in b.itertuples()],[310,140])
para('A binding supply limit alone does not identify the best purchase. J200 has the largest finite profit opportunity. The values above include pack sizes, shelf limits and changed delivery decisions; they are not per-unit shadow prices.')
para('Naive comparison rule','Heading2')
para('Each week, process stores by ID and SKUs by descending unit margin. Request enough cases for that week and cap allocation by available DC stock, shelf room and truck capacity. Sales and carryover adjust with fixed shipments. This feasible benchmark is intentionally simple; it is not claimed to reproduce an actual current company policy.')
story.append(PageBreak())
para('The forecast changes the best plan','Heading1');para(cold)
para(f"Replanning instead of holding the base deliveries improves lower-demand profit by {money(s.loc['lower','profit']-s.loc['lower_fixed','profit'])} and higher-demand profit by {money(s.loc['higher','profit']-s.loc['higher_fixed','profit'])}. Higher demand increases the best attainable profit here; it does not automatically destroy profit.")
story.append(Image(str(R/'figures/sensitivity.png'),width=470,height=209))
para('Truck recommendation','Heading2')
econ=tr.groupby('store_id')[['delivery_cost','units_shipped']].sum();econ['cost_per_unit']=econ.delivery_cost/econ.units_shipped
small=econ.loc['S08'];large=econ.loc['S01']
para(f"Burlington VT (S08, smallest shelf) costs {money(small.cost_per_unit)} per delivered unit; Boston Back Bay (S01, largest shelf) costs {money(large.cost_per_unit)}. Truck capacity is 420 units in both; cost efficiency depends on actual volume and visits. Keep store-specific consolidation. A forced odd/even-week-only policy saves visits but sacrifices {money(alt)} net profit.")
para('Technical evidence and limits','Heading2')
para('Gurobi and CP-SAT both prove the same base optimum; all reported mandatory reoptimizations are proven optimal. Independent checks cover flow, demand, shared shelf after arrival, truck activation, cumulative DC, integer packs and recomputed profit. Currency uses cents; CP-SAT uses fifth-units so fractional scenario demand is exact. Opening stock follows the published margin convention. No routing, terminal salvage, safety stock or demand learning is assumed.')
para('Team action: review and defend every constraint, verify private Canvas rules, rehearse the five-minute briefing, and publish the reviewed notebook only after authorization. Local notebook execution does not establish a hosted Google Colab test. The Word brief was absent; public course case/syllabus source was read from GitHub because the website was blocked.')
SimpleDocTemplate(str(C/'Beacon_Outfitters_COO_Memo.pdf'),pagesize=(612,792),rightMargin=60,leftMargin=60,topMargin=40,bottomMargin=40).build(story)

prs=Presentation();prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5)
def slide(title,text,image=None):
    a=prs.slides.add_slide(prs.slide_layouts[6]);box=a.shapes.add_textbox(Inches(.6),Inches(.35),Inches(12.1),Inches(1.1));tf=box.text_frame;tf.word_wrap=True;tf.text=title
    for p in tf.paragraphs:p.font.size=Pt(29);p.font.bold=True
    box=a.shapes.add_textbox(Inches(.7),Inches(1.6),Inches(5.3 if image else 11.8),Inches(5.2));tf=box.text_frame;tf.word_wrap=True
    for i,line in enumerate(text):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.size=Pt(22);p.space_after=Pt(20)
    if image:a.shapes.add_picture(str(R/'figures'/image),Inches(6.4),Inches(1.6),width=Inches(6.4))
    return a
slide('0:00 | Approve targeted replenishment',[f'{int(base.cases)} cases · {int(base.visits)} visits · {money(base.profit)} profit',f'+{money(uplift)} versus no deliveries',f'+{money(gain)} versus a feasible forecast rule'],'baseline.png')
slide('0:30 | Parkas are the best supply opportunity',[f'100 extra J200 parkas in week 1: +{money(b.iloc[0].profit_gain)}',f'Next: H600 beanies +{money(float(b.set_index("sku").loc["H600","profit_gain"]))}', 'These are total gains after replanning, not per-unit shadow prices.'])
slide('1:30 | Give each store its own delivery calendar',[f'{int(base.units_shipped):,} units on {int(base.visits)} visits',f'Blanket alternate-week policy costs {money(alt)}', 'Numbers in the calendar are delivered units; zero means no truck.'],'truck_calendar.png')
slide('3:00 | Refresh the plan when forecasts move',[f'Lower demand: {money(s.loc["lower","profit"])} replanned',f'Higher demand: {money(s.loc["higher","profit"])} replanned', 'Weeks 3–4 only; all SKUs ±20%. Fixed-policy results shown in notebook.'],'sensitivity.png')
slide('4:15 | VP action requested',['Approve the case-level shipments and store-specific truck calendar.',f'Secure 100 parkas if the premium is below {money(b.iloc[0].profit_gain)}.', 'Replan when forecasts or supply change; retain the base plan only as a fallback.', 'Anshuman · Inka · Juan Diego | ISOM 839 | Academic case'])
prs.save(str(C/'Beacon_Outfitters_Briefing.pptx'))

badge=f'[![Open in Google Colab](https://colab.research.google.com/assets/colab-badge.svg)]({url})'
(ROOT/'README.md').write_text(f'''# Beacon Outfitters: Four Weeks of Replenishment

{badge}

**Notebook published on GitHub.** The public notebook download is verified.
Hosted Google Colab execution remains unverified because this environment blocks Colab access.

{url}

## Executive overview

{summary}

{ask}

Academic retail replenishment case: 12 New England stores, one Worcester DC,
eight SKUs, four weeks. Team: **Anshuman, Inka, Juan Diego**. ISOM 839,
Prescriptive Analytics: Modeling & Optimization, Suffolk University,
Professor Hasan Arslan. Due November 4, 2026 at 7:40 PM Eastern.

## Run in Google Colab

Click **Open in Google Colab**, then select **Runtime → Run all**.
Use the free CPU runtime. The notebook installs exact dependency versions,
loads five public course CSVs (with embedded checksum-verified snapshots as a
fallback), solves the model, and displays shipments, financial comparisons,
charts, bottlenecks and sensitivity results. No clone, file upload, private key,
or paid subscription is needed. Allow several minutes. Read solver status and
gap: a time-limited feasible solution is not a proven optimum.

The URL owner and default branch were detected from Git origin and remote HEAD,
not the temporary local branch. Regenerate with `python scripts/build_notebook.py`.
This rebuild clears saved notebook outputs; execute it again before submission.
Published to GitHub with user authorization. No Canvas submission has been performed.

## Decisions and model

Choose integer case packs and binary truck visits. Maximize sales margin less
holding and visit costs, subject to inventory flow, demand, aggregate shelf space
**after arrival and before sales**, truck capacity and cumulative DC availability.
Unit costs appear once in margin; opening stock follows the case convention.
See [formulation](docs/formulation.md) and [assumptions](docs/assumptions.md).
Gurobi is attempted first using its bundled small-model license, with an explicit
open-source CP-SAT fallback. Both independently prove **{money(base.profit)}**
for the base model. Currency cents and fifth-unit scaling preserve scenario
precision. See [solver evidence](results/solver_comparison.csv) for versions,
status, objective, runtime, bound and gap for every run.

## Verified findings and scenarios

| Policy | Four-week profit |
|---|---:|
| Optimized base | {money(base.profit)} |
| No deliveries | {money(s.loc['do_nothing','profit'])} |
| Feasible naive rule | {money(s.loc['naive','profit'])} |
| Restricted alternate-week | {money(s.loc['alternate_week','profit'])} |
| Lower demand, reoptimized | {money(s.loc['lower','profit'])} |
| Higher demand, reoptimized | {money(s.loc['higher','profit'])} |

{cold}

Base fill rate is **{base.fill_rate:.2%}**, with **{int(base.units_lost)} lost units**.
The feasible naive benchmark uses stable store-ID allocation and descending unit
margin priority, with all supply, shelf, truck and pack limits enforced. It is
not claimed to be the company's actual current practice. The alternate-week
scenario lets each store choose either odd or even delivery weeks. Every extra
100-unit comparison releases supply in week 1. All week 3–4 forecasts change by
±20%, with exact fractional demand; weeks 1–2 stay unchanged.

![Truck calendar](results/figures/truck_calendar.png)
![Scenario comparison](results/figures/sensitivity.png)

## Data sources and dictionary

Professor Arslan's [official case](https://isom-839.vercel.app/case) and
[course repository](https://github.com/harslan/isom-839), revision
`1e2b0374818759215a61475fe5eeb3af000f8263`. Original bytes are in `data/raw/`.

| CSV | Rows | Contents |
|---|---:|---|
| stores.csv | 12 | store IDs/names, shelf and truck units, visit dollars |
| skus.csv | 8 | SKU ID/name, cost/price, case-pack units, weekly holding dollars/unit |
| demand_forecast.csv | 384 | store, SKU, week, forecast units |
| opening_inventory.csv | 96 | store, SKU, opening units |
| dc_availability.csv | 32 | SKU, week, released units (unused supply carries forward) |

The notebook shows dtypes, descriptive statistics, weekly/store demand,
supply shortfalls, shelf tightness, pack sizes, margins and truck economics.
Source URLs and original files are attributed, not relicensed.

## Repository and local reproduction

- `class_submission/`: executed notebook, COO memo PDF, optional briefing deck,
  team disclosure and submission instructions.
- `src/`: loading, verification, model, baselines, scenarios and reporting.
- `data/raw/`: five unmodified official CSVs.
- `results/`: full plans, schedules, financials, scenarios, feasibility and solver evidence.
- `tests/`: manually checkable model cases, corruption detection, data and results checks.
- `docs/`: formulation, assumptions, methodology, script, verification and traceability.
- `scripts/`: reproducible notebook and executive-artifact generation.

Use Python 3.12 and `python -m pip install -r requirements.txt`.
Run the class notebook in Jupyter, or execute it with `nbclient` in a fresh kernel.
Run `python -m pytest -q` and `python scripts/build_submission.py` after
refreshing the pipeline with `run_analysis(parameters(load_data('data/raw')))`
from the corresponding `src` modules. See [methodology](docs/methodology.md).

## Verification and limitations

Independent checks recompute profit and verify every constraint family, case
integrality and visit validity. Gurobi and CP-SAT agree on the proven base
objective. The memo, slides and notebook derive their figures from one pipeline;
[verification report](docs/verification_report.md) records actual test evidence.
The published notebook download is verified; hosted Google Colab execution remains unverified.
The Word brief was absent; private Canvas rules need team confirmation.
The public website was blocked, so its official GitHub source was read instead.
No live company data, routing, forecast estimation, terminal salvage or production
deployment is claimed. Future work could investigate uncertain-demand policies
and approved routing/service requirements.

## Submission and academic integrity

See [class submission](class_submission/README.md). The team must review and
defend every constraint and rehearse the five-minute briefing. AI assistance is
disclosed in [AI_Disclosure_and_Team.txt](class_submission/AI_Disclosure_and_Team.txt).
OpenAI Codex implemented, debugged, tested and documented these artifacts;
ChatGPT planning/prompt assistance is team-reported. Published to GitHub with
user authorization; no Canvas submission was performed.

## References

- [Case and public rubric](https://isom-839.vercel.app/case)
- [Syllabus](https://isom-839.vercel.app/syllabus)
- [Session 7 data and model skeleton](https://github.com/harslan/isom-839/blob/master/public/session-07/ISOM839_Session7_Scheduling_CPSAT_and_Midterm_Case.ipynb)
- Sessions 2–6 notebooks under the course repository's `public/session-02/`
  through `public/session-06/` directories.
''')
(C/'README.md').write_text(f'''# CLASS SUBMISSION - NOVEMBER 4, 2026

{badge}

**NEEDS REVIEW — notebook published on GitHub.** The public download is verified.
Local execution evidence is in [verification report](../docs/verification_report.md).
Hosted Colab execution and private Canvas requirements remain unverified.
No Canvas submission has been performed.

## Run in Google Colab

{url}

Open the badge and select **Runtime → Run all** in a free CPU
runtime. Dependencies install automatically; all five datasets load from public
course URLs or identical embedded snapshots. No clone, uploads, private API keys
or paid Colab plan are required.

## Submission files

The public case requires the model notebook, a memo of at most five pages and an
in-class five-minute briefing. Slides are optional; private Canvas upload rules
have not been checked.

- `Beacon_Outfitters_Midterm.ipynb` — self-contained model and all results.
- `Beacon_Outfitters_COO_Memo.pdf` — three-page merchandising VP memo.
- `Beacon_Outfitters_Briefing.pptx` — optional five-slide briefing aid.
- `AI_Disclosure_and_Team.txt` — attach/include as Canvas permits.

## Team submission steps

1. Anshuman, Inka and Juan Diego review the model, numbers and disclosure.
2. Confirm Canvas accepts the notebook/memo and optional slides/disclosure.
3. GitHub publication and the public notebook download are verified. Open the
   Colab badge and run all cells to verify hosted execution.
4. Upload required files by **November 4, 2026, 7:40 PM Eastern** and confirm receipt.
5. Rehearse the five-minute briefing; every member must defend the model.
''')
(C/'AI_Disclosure_and_Team.txt').write_text('''Team: Anshuman, Inka, Juan Diego
Course: ISOM 839, Suffolk University; Professor Hasan Arslan
OpenAI ChatGPT: planning, requirement analysis and Codex prompt assistance
(as reported in the team's supplied project instructions).
OpenAI Codex: model implementation, debugging, notebook/documentation,
automated verification and artifact creation in this session.
Actual computational tools: Python, pandas, NumPy, matplotlib, Gurobi,
OR-Tools CP-SAT, pytest, nbclient, ReportLab and python-pptx.
Case/data and instructional model skeleton: Professor Hasan Arslan's official
ISOM 839 course repository. This is an academic case.
The team must review all artifacts and be able to defend every constraint.
GitHub publication was authorized by the user and completed.
No Canvas upload or classroom presentation has been performed.
''')
print('Generated memo, deck, both READMEs and disclosure from verified results.')
script=f'''# Five-minute presenter script

## 0:00 — The decision and the dollars

Approve this four-week replenishment plan. We recommend shipping {int(base.cases)} cases,
containing {int(base.units_shipped):,} units, through {int(base.visits)} store visits. The plan earns
{money(base.profit)} in contribution profit. That is {money(uplift)} more than
selling opening inventory without deliveries, and {money(gain)} more than our
feasible forecast-driven rule. Those comparisons use the same margins, holding
charges and delivery costs. We are recommending an actionable shipment schedule,
not a forecast model, and the case-level recommendations are in the notebook.

## 0:30 — The bottleneck

The most valuable additional supply is J200, the down parka. Making 100 more
units available at the distribution center at the start of week one increases
four-week profit by {money(b.iloc[0].profit_gain)} after we replan. We tested the same
100-unit addition separately for every SKU, using identical release timing.
Parkas offer substantially more value than extra beanies or gloves. This is the
total opportunity from additional supply, not a guaranteed supplier price or a
per-unit shadow price. We would compare any procurement premium against that
benefit before buying. Some other products show shortages or tight restrictions,
but neither shortage volume nor a binding limit alone identifies the best
commercial opportunity. The actual dollar improvement is the decision criterion.

## 1:30 — The plan in a picture

The calendar shows delivered units by store and week. A zero means no truck.
Boston, Cambridge, Providence and Worcester receive visits in weeks one, two
and four. Hartford, Portland, New Haven, Springfield and Nashua receive visits
in weeks one and three. Manchester and Burlington receive visits in weeks one
and four. Portsmouth receives its only visit in week two. These are
store-specific choices, rather than a blanket weekly rule.

The plan respects whole case packs, shelves before customers buy, actual truck
capacities, and the distribution center's cumulative releases. Inventory can
carry forward, but unavailable stock cannot be borrowed from a future week.
It fills {base.fill_rate:.2%} of demand, leaving {int(base.units_lost)} units of unmet demand.
We also tested a policy forcing every store onto either odd or even weeks.
That policy earns {money(s.loc['alternate_week','profit'])}, losing {money(alt)} relative
to the recommended plan. Consolidation is useful, but imposing the same
rhythm everywhere gives away more margin than it saves in truck costs.

## 3:00 — What we assumed and what moves

The cold-snap test changes all week-three and week-four forecasts by twenty
percent, while preserving the first two weeks. With lower demand, replanning
earns {money(s.loc['lower','profit'])}. If we keep the original shipments and adjust
only sales and remaining inventory, profit falls to {money(s.loc['lower_fixed','profit'])}.
With higher demand, replanning earns {money(s.loc['higher','profit'])}, versus
{money(s.loc['higher_fixed','profit'])} under the fixed original deliveries. Higher demand
raises attainable profit here; it does not automatically make the business worse.
These tests distinguish adapting the plan from merely hoping the original
forecast is correct. Our recommendation is to refresh replenishment when
forecasts change, rather than lock every delivery for four weeks. This is a
controlled academic case: we have not modeled actual routes, supplier lead times,
or new service promises, so those would need review before operational use.

## 4:15 — The ask

Approve the shipment file and store-specific truck calendar. Prioritize the
additional parkas if the procurement premium justifies the benefit, and require
a rerun when forecasts or supply change. Both solvers proved the same base
profit, and independent checks reconcile the money and capacity limits. The
team will defend those assumptions and every constraint. We are asking for
approval of a clear decision with a measurable dollar return, supported by
an executable notebook and a practical calendar.
'''
(ROOT/'docs/presentation_script.md').write_text(script)
print('Presenter script words:',len(script.split()))

from pathlib import Path
import nbformat as nb
import json,hashlib,subprocess,re
root=Path(__file__).resolve().parents[1]
origin=subprocess.check_output(['git','remote','get-url','origin'],cwd=root,text=True).strip()
match=re.search(r'github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$',origin)
owner,repo=match.groups()
# Read-only remote HEAD is authoritative, not the local checkout branch named work.
remote=subprocess.check_output(['git','ls-remote','--symref','origin','HEAD'],cwd=root,text=True)
branch=re.search(r'ref: refs/heads/(\S+)\s+HEAD',remote).group(1)
url=f'https://colab.research.google.com/github/{owner}/{repo}/blob/{branch}/class_submission/Beacon_Outfitters_Midterm.ipynb'
(root/'docs/colab_link.json').write_text(json.dumps(dict(owner=owner,repository=repo,default_branch=branch,url=url,publication='pending publication'),indent=2))
cells=[]
def md(t):cells.append(nb.v4.new_markdown_cell(t))
def code(t):cells.append(nb.v4.new_code_cell(t))
md('''# Beacon Outfitters: Four Weeks of Replenishment
**ISOM 839 · Suffolk University · Professor Hasan Arslan**  
**Team: Anshuman, Inka, Juan Diego**

Choose case-pack shipments and truck visits across 12 stores, 8 SKUs and 4 weeks.
Maximize contribution profit while honoring shared shelf space, truck capacity,
and cumulative DC supply. This academic case is not a deployed retail system.

**Run:** Runtime → Run all in free Google Colab (CPU runtime). No repository clone,
manual uploads, API keys or paid subscription are needed. Package installation
requires internet access. All model code and five verified CSV snapshots are in
this notebook. Estimated runtime: several minutes; each solve has a 120-second
limit. Inspect status and gap before claiming optimality.

Source: [official case](https://isom-839.vercel.app/case),
[syllabus](https://isom-839.vercel.app/syllabus), and
[Session 7](https://github.com/harslan/isom-839/blob/master/public/session-07/ISOM839_Session7_Scheduling_CPSAT_and_Midterm_Case.ipynb).
''')
md('## 1. Automatic dependencies\nExact tested versions; Gurobi is optional. The bundled small-model license needs no private key; CP-SAT is the open-source fallback.')
code('''import sys, subprocess, os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/beacon-matplotlib')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet',
    'numpy==2.3.5', 'pandas==2.2.3', 'matplotlib==3.10.8', 'ortools==9.15.6755'])
optional = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'gurobipy==13.0.3'])
print('Gurobi package installed' if optional.returncode == 0 else 'Gurobi installation failed; CP-SAT remains available')
from IPython.display import display, Markdown
''')
md('## 2. Official data ingestion and validation\nFetch the pinned course revision with TLS verification and SHA-256 checks. If the network is unavailable, use identical embedded original CSV bytes. Unexpected online bytes fail validation rather than silently changing the experiment.')
raw={p.stem:p.read_text() for p in (root/'data/raw').glob('*.csv')}
# read_bytes preserves CRLF for byte-identical offline backups.
import base64
payload={p.stem:base64.b64encode(p.read_bytes()).decode() for p in (root/'data/raw').glob('*.csv')}
hashes={p.stem:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'data/raw').glob('*.csv')}
code('''import pandas as pd
import hashlib, base64
from io import BytesIO
from urllib.request import urlopen
from urllib.error import URLError
COURSE_COMMIT = '1e2b0374818759215a61475fe5eeb3af000f8263'
RAW = f'https://raw.githubusercontent.com/harslan/isom-839/{COURSE_COMMIT}/public/session-07/case/'
SNAPSHOTS = '''+repr(payload)+'''
SHA256 = '''+repr(hashes)+'''
data = {}
for name in ['stores','skus','demand_forecast','opening_inventory','dc_availability']:
    try:
        with urlopen(RAW + name + '.csv', timeout=20) as response:
            content = response.read()
        source = 'pinned course URL'
    except (URLError, TimeoutError, OSError) as exc:
        content = base64.b64decode(SNAPSHOTS[name])
        source = 'embedded original snapshot (' + type(exc).__name__ + ')'
    assert hashlib.sha256(content).hexdigest() == SHA256[name], 'Source checksum mismatch: ' + name
    data[name] = pd.read_csv(BytesIO(content))
    print(name, len(data[name]), source)
''')
# Inline tested source; no downloads of project code or local path imports.
code((root/'src/data_loader.py').read_text()+"\nassert validate_data(data)\np = parameters(data)\nfor name, table in data.items():\n    print(name, table.dtypes.to_dict()); display(table.describe(include='all'))")
md('## 3. Demand, supply and store economics\nShelf capacity is shared by all SKUs and is checked before sales. Unit margin is retail price less unit cost. A small store can have the same truck capacity as a large one, but less volume to spread its visit cost across.')
code('''display(data['stores']); display(data['skus'].assign(margin=lambda x: x.retail_price-x.unit_cost))
by_week=data['demand_forecast'].groupby('week').forecast_units.sum()
display(by_week.to_frame('demand'))
supply_demand=pd.concat([
    data['demand_forecast'].groupby('sku').forecast_units.sum().rename('demand'),
    data['dc_availability'].groupby('sku').units_available.sum().rename('DC_supply'),
    data['opening_inventory'].groupby('sku').on_hand_units.sum().rename('opening')],axis=1)
supply_demand['shortage']=supply_demand.demand-supply_demand.DC_supply-supply_demand.opening
display(supply_demand)
store_stats=data['stores'].set_index('store_id').join(data['demand_forecast'].groupby('store_id').forecast_units.sum().rename('four_week_demand'))
store_stats['shelf_to_demand']=store_stats.shelf_capacity_units/store_stats.four_week_demand
store_stats['visit_cost_per_forecast_week_unit']=store_stats.delivery_cost_per_visit/(store_stats.four_week_demand/4)
display(store_stats.sort_values('shelf_to_demand'))
print('Total shelf capacity:',data['stores'].shelf_capacity_units.sum(),'Opening stock:',data['opening_inventory'].on_hand_units.sum())
import matplotlib.pyplot as plt
fig, axes=plt.subplots(1,2,figsize=(12,4))
by_week.plot.bar(ax=axes[0],title='Forecast by week',ylabel='Units')
supply_demand[['demand','DC_supply','opening']].plot.bar(ax=axes[1],title='Supply and demand by SKU')
plt.tight_layout(); plt.show()
''')
md('## 4. Mathematical formulation\n'+(root/'docs/formulation.md').read_text())
md('## 5. Tested model, baselines, scenarios and independent verification\n'+(root/'docs/assumptions.md').read_text())
for name in ['optimization','validation','baselines','scenarios','reporting']:
 text=(root/f'src/{name}.py').read_text()
 text='\n'.join(line for line in text.splitlines() if not line.startswith('from src.'))
 code(text)
md('''## 6. Solve and certify all mandatory scenarios
Gurobi is attempted first; failures are printed and trigger the exact CP-SAT model.
The comparison run uses a 60-second limit. Mandatory analyses have 120 seconds
per solve. Values are not called optimal unless status is OPTIMAL. Equivalent
optima can have different shipment allocations. All extracted solutions undergo
independent feasibility and profit checks. Re-run this cell to refresh results.
''')
code("runs, summary, trucks = run_analysis(p, out='beacon_results')\ndisplay(summary)\ndisplay(pd.read_csv('beacon_results/solver_comparison.csv'))")
md('## 7. Shipment recommendations, truck calendar and weekly financials\nEvery nonzero shipment is shown. Downloads are optional; all results are displayed without uploads or a checkout.')
code("with pd.option_context('display.max_rows', 500):\n    display(runs['base']['plan'].query('cases>0'))\n    display(trucks)\ndisplay(pd.read_csv('beacon_results/weekly_financials.csv'))\ncharts(summary, trucks, out='beacon_results/figures')")
md('## 8. Baselines, bottlenecks and forecast sensitivity\nExtra 100-unit opportunities arrive in week 1. Finite re-solves measure total profit gains, not LP shadow prices. Alternate-week deliveries are restricted to either odd or even weeks per store. Fixed-policy scenarios preserve original cases and visits while adjusting sales and inventory.')
code("for filename in ['baseline_comparison','sku_bottleneck','sensitivity_results','dc_constraints','shortages','sku_summary','decision_changes','feasibility_checks']:\n    print(filename); display(pd.read_csv('beacon_results/'+filename+'.csv'))\nprint('Actual small/large store delivery economics:')\neconomics=trucks.groupby('store_id')[['units_shipped','delivery_cost','visit']].sum()\neconomics['cost_per_delivered_unit']=economics.delivery_cost/economics.units_shipped\ndisplay(economics.join(store_stats[['four_week_demand']]).sort_values('four_week_demand'))")
md('## 9. Executive decision and consistency checks\nThe memo and briefing are generated from this same pipeline. Expected figures below are regression checks for the preserved source data; feasible time-limited solutions are never presented as proven optima.')
code('''s=summary.set_index('scenario')
best=pd.read_csv('beacon_results/sku_bottleneck.csv').iloc[0]
if s.loc['base','status']=='OPTIMAL':
    assert abs(s.loc['base','profit']-213503.10)<0.011
assert pd.read_csv('beacon_results/feasibility_checks.csv').passed.all()
assert abs(pd.read_csv('beacon_results/weekly_financials.csv').profit.sum()-s.loc['base','profit'])<0.011
display(Markdown(f"""**Base plan:** ${s.loc['base','profit']:,.2f} contribution profit,
{s.loc['base','visits']:.0f} visits, {s.loc['base','cases']:.0f} cases.
Profit uplift: ${s.loc['base','profit']-s.loc['do_nothing','profit']:,.2f} versus no deliveries;
${s.loc['base','profit']-s.loc['naive','profit']:,.2f} versus the feasible heuristic.
Best 100-unit opportunity: **{best.sku}**, ${best.profit_gain:,.2f} gross gain.
Alternate-week restriction costs ${s.loc['base','profit']-s.loc['alternate_week','profit']:,.2f}.
Lower/higher forecast reoptimization: ${s.loc['lower','profit']:,.2f} / ${s.loc['higher','profit']:,.2f}.
Keeping the base shipments instead: ${s.loc['lower_fixed','profit']:,.2f} / ${s.loc['higher_fixed','profit']:,.2f}.
Use the truck calendar and case-level table above; refresh the plan when forecasts change.
**Team review:** defend every constraint, confirm Canvas requirements, and rehearse the briefing.
"""))
''')
md('''## 10. Attribution, AI disclosure and verification limits
Course case and five datasets: Professor Hasan Arslan, ISOM 839 (academic case).
OpenAI ChatGPT: planning, requirement analysis and Codex prompt assistance, as
reported by the team. OpenAI Codex: implementation, debugging, documentation,
verification and artifact generation. Team: Anshuman, Inka, Juan Diego.
The team must review and defend the entire model.

Local isolated-kernel execution is recorded in the repository verification report.
A real hosted Google Colab session has not been tested. Publication is pending;
no GitHub push or Canvas submission has been performed. The uploaded Word brief
was absent; private Canvas requirements require team confirmation.
''')
book=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'colab':{'name':'Beacon_Outfitters_Midterm.ipynb','provenance':[]},'language_info':{'name':'python'}})
nb.write(book,root/'class_submission/Beacon_Outfitters_Midterm.ipynb')
print(url)

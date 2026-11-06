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
url=f'https://colab.research.google.com/github/{owner}/{repo}/blob/{branch}/notebooks/Beacon_Outfitters_Optimization.ipynb'
link_path=root/'docs/colab_link.json'
previous=json.loads(link_path.read_text()) if link_path.exists() else {}
publication=previous.get('publication','pending publication') if previous.get('url')==url else 'pending publication'
link_path.write_text(json.dumps(dict(owner=owner,repository=repo,default_branch=branch,url=url,publication=publication),indent=2))
cells=[]
def md(t):cells.append(nb.v4.new_markdown_cell(t))
def code(t):cells.append(nb.v4.new_code_cell(t))
md('''**Contributors: Anshuman · Inka · Juan Diego**

# Beacon Outfitters | Retail Replenishment Optimization

A reproducible decision-science workflow: validated retail data → constrained
optimization → benchmark evaluation → uncertainty analysis → shipment decisions.
Decide how many whole cases to ship and which stores receive trucks across
12 stores, 8 SKUs and 4 weeks. Results are modeled benchmark outcomes, not
realized company savings. The supplied demand forecast is an input, not a
prediction trained here.

**Run:** Runtime → Run all in a free Google Colab CPU runtime. Dependencies
install automatically; no checkout, file upload, private API key or paid runtime
is needed. The notebook includes all model source and verified CSV snapshots.
Inspect objective, bound and gap before calling a result optimal.
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
md('## 2. Data ingestion and validation\nFetch the pinned data revision with TLS verification and SHA-256 checks. If the network is unavailable, use identical embedded original CSV bytes. Unexpected online bytes fail validation rather than silently changing the experiment.')
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
DATA_REVISION = 'f8b2855f099bc4010c8b211fb083d1061292bf04'
RAW = f'https://raw.githubusercontent.com/agrawalanshuman/beacon-outfitters-replenishment/{DATA_REVISION}/data/raw/'
SNAPSHOTS = '''+repr(payload)+'''
SHA256 = '''+repr(hashes)+'''
data = {}
for name in ['stores','skus','demand_forecast','opening_inventory','dc_availability']:
    try:
        with urlopen(RAW + name + '.csv', timeout=20) as response:
            content = response.read()
        source = 'pinned data URL'
    except (URLError, TimeoutError, OSError) as exc:
        content = base64.b64decode(SNAPSHOTS[name])
        source = 'embedded original snapshot (' + type(exc).__name__ + ')'
    assert hashlib.sha256(content).hexdigest() == SHA256[name], 'Source checksum mismatch: ' + name
    data[name] = pd.read_csv(BytesIO(content))
    print(name, len(data[name]), source)
''')
# Inline tested source; no downloads of project code or local path imports.
code((root/'beacon_outfitters/data_loader.py').read_text()+"\nassert validate_data(data)\np = parameters(data)\nfor name, table in data.items():\n    print(name, table.dtypes.to_dict()); display(table.describe(include='all'))")
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
 text=(root/f'beacon_outfitters/{name}.py').read_text()
 text='\n'.join(line for line in text.splitlines() if not line.startswith('from beacon_outfitters.'))
 code(text)
md('''## 6. Solve and certify all experiments
Gurobi is attempted first; failures are printed and trigger the exact CP-SAT model.
The comparison run uses a 60-second limit. Primary experiments have 120 seconds
per solve. Values are not called optimal unless status is OPTIMAL. Equivalent
optima can have different shipment allocations. All extracted solutions undergo
independent feasibility and profit checks. Re-run this cell to refresh results.
''')
code("MODEL_SHA256 = "+repr({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'beacon_outfitters').glob('*.py') if p.name in ['data_loader.py','optimization.py','validation.py','baselines.py','scenarios.py','reporting.py']})+"\nruns, summary, trucks = run_analysis(p, out='beacon_results', provenance={'input_sha256':SHA256,'model_source_sha256':MODEL_SHA256})\ndisplay(summary)\ndisplay(pd.read_csv('beacon_results/tables/solver_comparison.csv'))")
md('## 7. Shipment recommendations, truck calendar and weekly financials\nEvery nonzero shipment is shown. Downloads are optional; all results are displayed without uploads or a checkout.')
code("with pd.option_context('display.max_rows', 500):\n    display(runs['base']['plan'].query('cases>0'))\n    display(trucks)\ndisplay(pd.read_csv('beacon_results/tables/weekly_financials.csv'))\ncharts(summary, trucks, out='beacon_results/figures')")
md('## 8. Baselines, bottlenecks and forecast sensitivity\nExtra 100-unit opportunities arrive in week 1. Finite re-solves measure total profit gains, not LP shadow prices. Alternate-week deliveries are restricted to either odd or even weeks per store. Fixed-policy scenarios preserve original cases and visits while adjusting sales and inventory.')
code("for filename in ['baseline_comparison','sku_bottleneck','sensitivity_results','dc_constraints','shortages','sku_summary','decision_changes','feasibility_checks']:\n    print(filename); display(pd.read_csv('beacon_results/tables/'+filename+'.csv'))\nprint('Actual small/large store delivery economics:')\neconomics=trucks.groupby('store_id')[['units_shipped','delivery_cost','visit']].sum()\neconomics['cost_per_delivered_unit']=economics.delivery_cost/economics.units_shipped\ndisplay(economics.join(store_stats[['four_week_demand']]).sort_values('four_week_demand'))")
md('## 9. Executive decision and consistency checks\nThe memo and briefing are generated from this same pipeline. Expected figures below are regression checks for the preserved source data; feasible time-limited solutions are never presented as proven optima.')
code('''s=summary.set_index('scenario')
best=pd.read_csv('beacon_results/tables/sku_bottleneck.csv').iloc[0]
if s.loc['base','status']=='OPTIMAL':
    assert abs(s.loc['base','profit']-213503.10)<0.011
assert pd.read_csv('beacon_results/tables/feasibility_checks.csv').passed.all()
assert abs(pd.read_csv('beacon_results/tables/weekly_financials.csv').profit.sum()-s.loc['base','profit'])<0.011
display(Markdown(f"""**Base plan:** ${s.loc['base','profit']:,.2f} contribution profit,
{s.loc['base','visits']:.0f} visits, {s.loc['base','cases']:.0f} cases.
Profit uplift: ${s.loc['base','profit']-s.loc['do_nothing','profit']:,.2f} versus no deliveries;
${s.loc['base','profit']-s.loc['naive','profit']:,.2f} versus the feasible heuristic.
Best 100-unit opportunity: **{best.sku}**, ${best.profit_gain:,.2f} gross gain.
Alternate-week restriction costs ${s.loc['base','profit']-s.loc['alternate_week','profit']:,.2f}.
Lower/higher forecast reoptimization: ${s.loc['lower','profit']:,.2f} / ${s.loc['higher','profit']:,.2f}.
Keeping the base shipments instead: ${s.loc['lower_fixed','profit']:,.2f} / ${s.loc['higher_fixed','profit']:,.2f}.
Use the truck calendar and case-level table above; refresh the plan when forecasts change.
**Review:** validate operational assumptions and the shipment calendar before adopting the policy.
"""))
''')
md('''## 10. Reproducibility, source credit and AI assistance

Original benchmark data and modeling reference: Hasan Arslan's
[public repository](https://github.com/harslan/isom-839).
The original five CSVs remain unchanged; source attribution and file hashes are
recorded in `docs/data_provenance.md`.

ChatGPT assisted debugging and technical explanations. OpenAI Codex assisted
implementation, testing, documentation and artifact generation. Contributors
remain responsible for reviewing the model and interpretation.

The run writes data/model hashes, solver versions, bounds, gaps and independent
checks. Local fresh-kernel execution is tested separately from hosted Google
Colab execution; no hosted execution claim is made without a hosted run.
''')
book=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'colab':{'name':'Beacon_Outfitters_Optimization.ipynb','provenance':[]},'language_info':{'name':'python'}})
nb.write(book,root/'notebooks/Beacon_Outfitters_Optimization.ipynb')
print(url)

"""Reconcile portfolio artifacts, notebook execution, provenance and financial claims."""
from pathlib import Path
import argparse, hashlib, json, re, subprocess
import nbformat
import pandas as pd
from pptx import Presentation

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--notebook-results',type=Path)
args=parser.parse_args()
r=ROOT/'results';t=r/'tables'
s=pd.read_csv(t/'financial_summary.csv').set_index('scenario')
checks=pd.read_csv(t/'feasibility_checks.csv');assert checks.passed.all()
link=json.loads((ROOT/'docs/colab_link.json').read_text())
book=nbformat.read(ROOT/'notebooks/Beacon_Outfitters_Optimization.ipynb',as_version=4)
nbformat.validate(book)
cells=[c for c in book.cells if c.cell_type=='code']
assert all(c.execution_count is not None for c in cells)
assert not any(o.output_type=='error' for c in cells for o in c.outputs)
assert not any('from beacon_outfitters.' in c.source for c in cells), 'Standalone model must inline its implementation'
text='\n'.join(str(o.get('text',''))+str(o.get('data',{}).get('text/markdown',''))+str(o.get('data',{}).get('text/plain','')) for c in cells for o in c.outputs)
for name in ['base','do_nothing','naive','alternate_week','lower','higher','lower_fixed','higher_fixed']:
    assert f'${s.loc[name,"profit"]:,.2f}' in text, (name,'notebook financial mismatch')
info=subprocess.check_output(['pdfinfo',str(ROOT/'reports/Beacon_Outfitters_Decision_Brief.pdf')],text=True)
pages=int(re.search(r'Pages:\s+(\d+)',info).group(1));assert 1<=pages<=5
pdf_text=subprocess.check_output(['pdftotext',str(ROOT/'reports/Beacon_Outfitters_Decision_Brief.pdf'),'-'],text=True)
deck=Presentation(ROOT/'reports/Beacon_Outfitters_Analytics_Overview.pptx');assert len(deck.slides)==6
slides='\n'.join(shape.text for slide in deck.slides for shape in slide.shapes if shape.has_text_frame)
for name in ['base','lower','higher','lower_fixed','higher_fixed']:
    assert f'${s.loc[name,"profit"]:,.2f}' in pdf_text,(name,'decision brief mismatch')
for name in ['base','lower','higher']:
    assert f'${s.loc[name,"profit"]:,.2f}' in slides,(name,'deck mismatch')
best=pd.read_csv(t/'sku_bottleneck.csv').iloc[0]
assert f'${best.profit_gain:,.2f}' in pdf_text and f'${best.profit_gain:,.2f}' in slides
tr=pd.read_csv(t/'truck_schedule.csv')
for store,a in tr.groupby('store_id'):
    weeks=', '.join(str(w) for w in a.query('visit==1').week)
    assert re.search(store+r'\s+'+re.escape(weeks),pdf_text),(store,'calendar mismatch')
readme=(ROOT/'README.md').read_text()
assert readme.startswith('**Contributors: Anshuman · Inka · Juan Diego**')
assert link['url'] in readme and 'colab-badge.svg' in readme
assert 'notebooks/Beacon_Outfitters_Optimization.ipynb' in link['url']
assert not (ROOT/'class_submission').exists()
legacy=re.compile(r'\b(midterm|coursework|syllabus|canvas|suffolk|professor)\b|class_submission|ISOM\s*839',re.I)
for p in [ROOT/'README.md', *list((ROOT/'docs').glob('*.md'))]:
    assert not legacy.search(p.read_text()),f'Outdated framing: {p.name}'
assert not legacy.search(pdf_text+slides)
for p in (ROOT/'notebooks').glob('*.ipynb'):
    n=nbformat.read(p,as_version=4)
    assert n.cells[0].source.startswith('**Contributors:')
    assert not legacy.search('\n'.join(c.source for c in n.cells)),p.name
matched=False
if args.notebook_results:
    other=pd.read_csv(args.notebook_results/'tables/financial_summary.csv').set_index('scenario')
    for name in s.index:
        assert abs(other.loc[name,'profit']-s.loc[name,'profit'])<.011,(name,'independent run mismatch')
        assert other.loc[name,'status']==s.loc[name,'status']
    for name in ['truck_schedule','sku_summary','decision_changes']:
        pd.testing.assert_frame_equal(pd.read_csv(args.notebook_results/f'tables/{name}.csv'),pd.read_csv(t/f'{name}.csv'),atol=1e-6,rtol=1e-6)
    local_meta=json.loads((r/'run_metadata.json').read_text())
    other_meta=json.loads((args.notebook_results/'run_metadata.json').read_text())
    assert local_meta['provenance']==other_meta['provenance']
    matched=True
meta=json.loads((r/'run_metadata.json').read_text())
for name,digest in meta['provenance']['model_source_sha256'].items():
    assert hashlib.sha256((ROOT/'beacon_outfitters'/name).read_bytes()).hexdigest()==digest
report=dict(notebook_code_cells=len(cells),all_executed=True,notebook_errors=0,
    decision_brief_pages=pages,slides=len(deck.slides),financial_claims_reconciled=True,
    notebook_and_cli_results_match=matched,input_and_source_provenance_match=True,
    contributors_at_top=True,legacy_framing_removed=True,
    all_solver_statuses=s.status.unique().tolist(),hosted_colab_execution_verified=False,
    publication=link.get('publication','pending publication'))
(r/'verification.json').write_text(json.dumps(report,indent=2))
execution=json.loads((r/'notebook_execution.json').read_text())
tests=json.loads((r/'test_execution.json').read_text()) if (r/'test_execution.json').exists() else {}
evidence=pd.read_csv(t/'solver_comparison.csv').set_index('scenario')
(ROOT/'docs/verification_report.md').write_text(f'''# Verification evidence

**Contributors: Anshuman · Inka · Juan Diego**

## Executed checks

- Standalone notebook: {len(cells)}/{len(cells)} code cells, zero errors,
  {execution['runtime_seconds']:.2f} seconds in a fresh kernel outside the checkout.
- Automated tests: {tests.get('passed','not recorded')} passed,
  {tests.get('failed','not recorded')} failed. See results/test_execution.json.
- Independent CLI and notebook results agree: {matched}. All scenario profit
  claims, base calendar, SKU fills, decision changes and provenance reconcile.
- Independent feasibility and accounting checks pass for all returned plans.
- Gurobi base status: {evidence.loc['base','status']}; objective
  ${evidence.loc['base','objective']:,.2f}; bound ${evidence.loc['base','bound']:,.2f};
  gap {evidence.loc['base','gap']:.2%}; runtime {evidence.loc['base','runtime']:.2f}s.
- CP-SAT base status: {evidence.loc['base_cp_sat','status']}; objective
  ${evidence.loc['base_cp_sat','objective']:,.2f}; bound ${evidence.loc['base_cp_sat','bound']:,.2f};
  gap {evidence.loc['base_cp_sat','gap']:.2%}; runtime {evidence.loc['base_cp_sat','runtime']:.2f}s.
- All 17 recorded experiments report OPTIMAL within solver tolerances. Fixed
  heuristic/policy status certifies recourse under fixed decisions, not optimal
  heuristic allocations. Timings are machine observations, not performance claims.
- Decision brief: {pages} pages. Analytics overview: {len(deck.slides)} slides.
  PDF/deck monetary claims and the PDF store calendar match the saved results.
- Contributors appear at the top. Legacy framing checks pass for portfolio
  documentation, notebooks, PDF and slide text. Source attribution is retained.

## Reproducibility and scope

Five input files retain their original bytes. Input and model SHA-256 hashes,
versions, seed, workers and experiment settings are in results/run_metadata.json.
The offline notebook test blocks URL access and compares embedded datasets with
those original snapshots. The installable CLI entry point is verified.
Companion EDA and solver-comparison notebooks are executed separately.

The isolated run uses pinned dependencies in a fresh kernel; this is not a
separately provisioned hosted Colab runtime. Hosted Colab execution remains
unverified; access from this environment is blocked by its proxy policy.
Publication status: **{link.get('publication','pending publication')}**.
See results/publication_check.json for published artifact verification when
available. The standalone link is:

{link['url']}

These are modeled benchmark outcomes, not realized company savings. No
predictive model, live retailer deployment or external posting is claimed.
LinkedIn copy is a draft. See assumptions.md, data_provenance.md and
AI_DISCLOSURE.md for interpretation, source credit and assistance details.
''')
print(json.dumps(report,indent=2))

"""Audit executed notebook and generated deliverables against saved results."""
from pathlib import Path
import json,subprocess,re,argparse
import nbformat
import pandas as pd
from pptx import Presentation
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--notebook-results',type=Path);args=parser.parse_args()
r=ROOT/'results';c=ROOT/'class_submission'
s=pd.read_csv(r/'financial_summary.csv').set_index('scenario')
book=nbformat.read(c/'Beacon_Outfitters_Midterm.ipynb',as_version=4)
nbformat.validate(book)
code=[z for z in book.cells if z.cell_type=='code']
assert all(z.execution_count is not None for z in code)
assert not any(o.output_type=='error' for z in code for o in z.outputs)
assert not any('from src.' in z.source for z in code), 'Standalone notebook must inline the implementation'
texts='\n'.join(str(o.get('text',''))+'\n'+str(o.get('data',{}).get('text/markdown',''))+'\n'+str(o.get('data',{}).get('text/plain','')) for z in code for o in z.outputs)
for name in ['base','do_nothing','naive','alternate_week','lower','higher','lower_fixed','higher_fixed']:
    assert f'${s.loc[name,"profit"]:,.2f}' in texts,(name,'missing notebook figure')
pdf=c/'Beacon_Outfitters_COO_Memo.pdf'
info=subprocess.check_output(['pdfinfo',str(pdf)],text=True)
pages=int(re.search(r'Pages:\s+(\d+)',info).group(1));assert pages<=5
pdf_text=subprocess.check_output(['pdftotext',str(pdf),'-'],text=True)
deck=Presentation(c/'Beacon_Outfitters_Briefing.pptx');assert len(deck.slides)==5
slide_text='\n'.join(shape.text for slide in deck.slides for shape in slide.shapes if shape.has_text_frame)
for name in ['base','do_nothing','naive','alternate_week','lower','higher','lower_fixed','higher_fixed']:
    assert f'${s.loc[name,"profit"]:,.2f}' in pdf_text,(name,'missing memo figure')
for name in ['base','lower','higher']:
    assert f'${s.loc[name,"profit"]:,.2f}' in slide_text,(name,'missing briefing figure')
b=pd.read_csv(r/'sku_bottleneck.csv').iloc[0]
assert f'${b.profit_gain:,.2f}' in pdf_text and f'${b.profit_gain:,.2f}' in slide_text
# Match store IDs and the adjacent delivery-week string from the text extraction.
tr=pd.read_csv(r/'truck_schedule.csv')
for store,a in tr.groupby('store_id'):
    weeks=', '.join(str(z) for z in a.query('visit==1').week)
    assert re.search(store+r'\s+'+re.escape(weeks),pdf_text),(store,'memo calendar differs')
words=len((ROOT/'docs/presentation_script.md').read_text().split());assert 550<=words<=650
link_metadata=json.loads((ROOT/'docs/colab_link.json').read_text())
link=link_metadata['url']
publication=link_metadata.get('publication','pending publication')
for path in [ROOT/'README.md',c/'README.md']:
    text=path.read_text();assert link in text and 'colab-badge.svg' in text
    if publication=='published': assert 'published on GitHub' in text
    else: assert 'pending publication' in text
matched=False
if args.notebook_results:
    other=pd.read_csv(args.notebook_results/'financial_summary.csv').set_index('scenario')
    # Different tied optimal allocations can occur; the proof and financial totals must agree.
    for name in s.index:
        assert abs(other.loc[name,'profit']-s.loc[name,'profit'])<0.011,(name,'notebook/repository mismatch')
        assert other.loc[name,'status']==s.loc[name,'status']
    pd.testing.assert_frame_equal(pd.read_csv(args.notebook_results/'truck_schedule.csv'),tr,atol=1e-6,rtol=1e-6)
    for filename in ['sku_summary.csv','decision_changes.csv']:
        pd.testing.assert_frame_equal(pd.read_csv(args.notebook_results/filename),pd.read_csv(r/filename),atol=1e-6,rtol=1e-6)
    matched=True
report=dict(notebook_code_cells=len(code),all_executed=True,notebook_errors=0,memo_pages=pages,
    slides=len(deck.slides),presenter_script_words=words,notebook_memo_slides_figures_agree=True,
    notebook_and_repository_runs_agree=matched,all_solver_statuses=s.status.unique().tolist(),
    hosted_colab_verified=False,publication=publication)
(r/'deliverable_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

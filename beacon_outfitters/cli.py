"""Run the same validated pipeline used by the standalone notebook."""
import argparse
import hashlib
from pathlib import Path
from .data_loader import load_data, validate_data, parameters
from .reporting import run_analysis, charts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path('data/raw'))
    parser.add_argument('--output', type=Path, default=Path('results'))
    parser.add_argument('--skip-comparison', action='store_true', help='Skip the independent base CP-SAT comparison')
    args = parser.parse_args(argv)
    data = load_data(args.data)
    validate_data(data)
    input_hashes = {p.stem:hashlib.sha256(p.read_bytes()).hexdigest() for p in args.data.glob('*.csv')}
    source_hashes = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py') if p.name in ['data_loader.py','optimization.py','validation.py','baselines.py','scenarios.py','reporting.py']}
    runs, summary, trucks = run_analysis(parameters(data), out=args.output,
        compare=not args.skip_comparison,
        provenance={'input_sha256':input_hashes,'model_source_sha256':source_hashes})
    charts(summary, trucks, out=args.output/'figures')
    print(summary[['scenario','status','profit','fill_rate','visits']].to_string(index=False))
    return 0

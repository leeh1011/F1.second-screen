"""Evaluate recent races chronologically using already rebuilt datasets.

Run from backend: python -m app.pipeline.forward_evaluation
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

from app.pipeline.season import evaluate, make_plan
from app.pipeline.train import write_json


METRICS = ['average_precision', 'roc_auc', 'log_loss', 'brier_score']


def main():
    backend = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rebuild', type=Path,
                        default=backend / 'data' / 'rebuild_20261104_191805')
    parser.add_argument('--test-races', type=int, default=5)
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    if args.test_races < 1 or args.jobs < 1:
        parser.error('--test-races and --jobs must be positive')

    rebuild = args.rebuild.resolve()
    source_path = rebuild / 'reports' / 'latest' / 'manifest.json'
    source = json.loads(source_path.read_text(encoding='utf-8-sig'))
    if source['status'] != 'complete':
        raise ValueError('The rebuilt season run is not complete')
    original_plan = sorted(source['plan'], key=lambda r: pd.Timestamp(r['date_start']))
    calibration_races = sum(r['role'] == 'calibration' for r in original_plan)
    if calibration_races < 1 or len(original_plan) - args.test_races - calibration_races < 3:
        raise ValueError('Each fold needs at least three training races plus calibration races')
    processed = rebuild / 'processed'
    for race in original_plan:
        path = processed / str(race['session_key']) / 'labeled_3lap_v2.parquet'
        if not path.is_file():
            raise FileNotFoundError(f'Missing rebuilt data: {path}')

    schedule = [dict(r, session_name='Race') for r in original_plan]
    years = sorted({int(r['year']) for r in schedule})
    targets = original_plan[-args.test_races:]
    # Fix all folds before fitting any model. Each fold ends at its test race.
    plans = [make_plan(schedule, calibration_races, years, int(r['session_key']))
             for r in targets]
    if any(plan[-1]['session_key'] != race['session_key']
           for plan, race in zip(plans, targets)):
        raise ValueError('Evaluation plan does not match requested test races')

    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid4().hex[:6]
    output = rebuild / 'forward_reports' / run_id
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / 'source_manifest.json', source)
    write_json(output / 'schedule.json', schedule)
    pd.DataFrame(targets)[['session_key', 'date_start', 'circuit_short_name']].to_csv(
        output / 'evaluation_plan.csv', index=False, encoding='utf-8-sig')
    metadata = {'status': 'running', 'year_decay': source['year_decay'],
                'calibration_races': calibration_races, 'plans': plans,
                'source_manifest': str(source_path), 'completed_sessions': []}
    write_json(output / 'manifest.json', metadata)
    print(f'Output: {output}', flush=True)
    results = []
    try:
        for race, plan in zip(targets, plans):
            key = int(race['session_key'])
            folder = output / f'session_{key}' / 'latest'
            folder.mkdir(parents=True)
            write_json(folder / 'split_plan.json', plan)
            write_json(folder / 'manifest.json', {'status': 'running', 'plan': plan})
            print(f'\n=== Evaluation: {key} ({race["circuit_short_name"]}) ===', flush=True)
            evaluate(processed, folder, plan, args.jobs, source['year_decay'])
            results.append(pd.read_csv(folder / 'metrics_by_race.csv'))
            combined = pd.concat(results, ignore_index=True)
            combined.to_csv(output / 'metrics_by_race.csv', index=False, encoding='utf-8-sig')
            metadata['completed_sessions'].append(key)
            write_json(output / 'manifest.json', metadata)

        grouped = combined.groupby(['model', 'variant'])
        summary = grouped[METRICS].mean()
        summary = summary.join(grouped.size().rename('races'))
        summary = summary.join(grouped[METRICS].count().add_suffix('_valid_races')).reset_index()
        summary.to_csv(output / 'metrics_macro.csv', index=False, encoding='utf-8-sig')
        metadata['status'] = 'complete'
        write_json(output / 'manifest.json', metadata)
        print('\n' + summary[['model', 'variant', 'races'] + METRICS].to_string(index=False))
        print(f'\nComplete: {output}')
    except (Exception, KeyboardInterrupt) as exc:
        metadata.update(status='interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed',
                        error=f'{type(exc).__name__}: {exc}')
        write_json(output / 'manifest.json', metadata)
        write_json(folder / 'manifest.json', {'status': metadata['status'], 'plan': plan,
                                             'error': metadata['error']})
        raise


if __name__ == '__main__':
    main()

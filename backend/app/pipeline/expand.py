"""Collect the first N completed races of a season, validate, then evaluate forward."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

from app.pipeline.batch import ROOT, run_batch
from app.pipeline.collect import fetch_data
from app.pipeline.train import run, write_json


def select_races(records, year, limit, now=None):
    now = pd.Timestamp(now or datetime.now(timezone.utc))
    eligible = [r for r in records if r.get('year') == year and r.get('session_name') == 'Race'
                and not r.get('is_cancelled', False) and r.get('date_end')
                and pd.Timestamp(r['date_end']) < now]
    eligible.sort(key=lambda r: pd.Timestamp(r['date_start']))
    if len(eligible) < limit or limit < 4:
        raise ValueError('Need at least four completed races and enough races for the requested limit')
    selected = eligible[:limit]
    if len({r['session_key'] for r in selected}) != limit:
        raise ValueError('Duplicate session keys in season schedule')
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--year', type=int, default=2024)
    parser.add_argument('--limit', type=int, default=8)
    parser.add_argument('--min-train-races', type=int, default=3)
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--schedule', type=Path, help='Optional local sessions JSON instead of API lookup')
    args = parser.parse_args()
    if not 2 <= args.min_train_races < args.limit or args.jobs < 1:
        parser.error('Require 2 <= min-train-races < limit and jobs >= 1')
    records = (json.loads(args.schedule.read_text(encoding='utf-8-sig')) if args.schedule
               else fetch_data('sessions', year=args.year, session_name='Race'))
    races = select_races(records, args.year, args.limit)
    keys = [int(r['session_key']) for r in races]
    report = ROOT / 'data' / 'processed' / 'expansion_reports' / (
        datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid4().hex[:6])
    report.mkdir(parents=True)
    write_json(report / 'selected_sessions.json', races)
    for r in races:
        print(f"{r['session_key']}: {r['date_start']} {r['country_name']} {r['circuit_short_name']}", flush=True)
    result = run_batch(keys, ROOT / 'data' / 'pilot_raw', ROOT / 'data' / 'processed', report)
    print(result.to_string(index=False))
    if result.status.ne('ok').any() or result.validation_violations.fillna(-1).ne(0).any():
        raise SystemExit(f'Collection/validation failed. Training stopped; see {report}')
    trained = run(ROOT / 'data' / 'processed', ROOT / 'data' / 'processed' / 'training_reports',
                  keys, jobs=args.jobs, split='forward', min_train_races=args.min_train_races)
    write_json(report / 'training_report.json', {'path': str(trained.resolve()), 'sessions': keys})


if __name__ == '__main__':
    main()

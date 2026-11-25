"""Check saved V3 labels against local raw records, without training or downloads.

Run from backend: python -m app.pipeline.validate_v3_dataset
Resume after Ctrl+C: python -m app.pipeline.validate_v3_dataset --resume
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import traceback

import pandas as pd
from app.pipeline.extract import timestamp
from app.pipeline.label import LABEL_VERSION, LABEL_MAX_UPDATE_SECONDS, validate_labels

BACKEND = Path(__file__).resolve().parents[2]
ENDPOINTS = ['drivers', 'intervals', 'position', 'laps', 'stints', 'pit', 'race_control', 'overtakes']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path = Path(path)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    temp.replace(path)


def raw_data(key):
    data = {}
    for endpoint in ENDPOINTS:
        path = BACKEND / 'data/pilot_raw' / str(key) / (endpoint + '.json')
        if not path.exists():
            url = f'https://api.openf1.org/v1/{endpoint}?session_key={key}'
            path = BACKEND / 'data/openf1/cache' / endpoint / (hashlib.sha256(url.encode()).hexdigest()[:20] + '.json')
        rows = read_json(path)
        if not isinstance(rows, list) or any(r.get('session_key') != key for r in rows):
            raise ValueError(f'{endpoint}: raw session mismatch or invalid format')
        data[endpoint] = rows
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return data, digest


def validate_one(key, rebuild, source_hashes, previous, report_dir):
    folder = rebuild / 'processed' / str(key)
    metadata = read_json(rebuild / 'race_reports' / f'{key}.json')
    current_sources = {name: sha(BACKEND / name) for name in source_hashes}
    if current_sources != source_hashes or metadata['sources'] != source_hashes:
        raise ValueError('Pipeline source differs from the rebuild; do not treat this as validation of the original policy')
    output_hashes = {name: sha(folder / name) for name in metadata['output_hashes']}
    if output_hashes != metadata['output_hashes']:
        raise ValueError('Saved candidates/labels differ from rebuild hashes')
    data, raw_hash = raw_data(key)
    if raw_hash != metadata['raw_sha256']:
        raise ValueError('Raw data differs from data used during regeneration')
    fingerprint = {'sources': current_sources, 'outputs': output_hashes, 'raw_sha256': raw_hash,
                   'validator_runner_sha256': sha(__file__)}
    if previous and previous.get('status') == 'passed' and previous.get('fingerprint') == fingerprint:
        return dict(previous, reused=True)
    labels = pd.read_parquet(folder / 'labeled_3lap_v2.parquet')
    candidates = pd.read_parquet(folder / 'candidates.parquet')
    identity = ['session_key', 'prediction_time', 'attacker_number', 'defender_number']
    if labels.empty or not labels.session_key.eq(key).all():
        raise ValueError('Empty labels or session mismatch')
    if not labels[identity].equals(candidates[identity]) or labels[identity].isna().any().any():
        raise ValueError('Label/candidate identity mismatch or missing identity')
    if labels.duplicated(['session_key', 'prediction_time', 'attacker_number']).any():
        raise ValueError('Duplicate attacker observations')
    if not labels.label_version.eq(LABEL_VERSION).all():
        raise ValueError('Mixed/incorrect label version, including unknown rows')
    if not labels.label_max_update_seconds.eq(LABEL_MAX_UPDATE_SECONDS).all():
        raise ValueError('Mixed/incorrect observation limit, including unknown rows')
    known = labels.target_overtake_3lap.notna()
    if not labels.loc[known, 'target_overtake_3lap'].isin([0, 1]).all():
        raise ValueError('Known labels must be binary')
    if not (labels.loc[known, 'battle_ready'].eq(True) & labels.loc[known, 'offline_eligible'].eq(True)).fillna(False).all():
        raise ValueError('Known labels violate readiness/eligibility')
    checks = validate_labels(labels, data)
    return {'session_key': key, 'status': 'passed', 'reused': False, 'fingerprint': fingerprint,
            'rows': len(labels), 'known_rows': int(known.sum()), 'raw_checks': checks,
            'checked_at': datetime.now(timezone.utc).isoformat()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rebuild', type=Path, default=BACKEND / 'data/rebuild_20261125_v3')
    parser.add_argument('--report-dir', type=Path, default=BACKEND / 'data/validation/raw_v3')
    parser.add_argument('--sessions', type=int, nargs='+', help='Optional subset; never reported as full-dataset completion')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    rebuild, report_dir = args.rebuild.resolve(), args.report_dir.resolve()
    if report_dir == rebuild or rebuild in report_dir.parents or report_dir in rebuild.parents:
        parser.error('Keep validation reports separate from the rebuilt dataset')
    if LABEL_VERSION != 'v2-gap-evidence-negative-guard-v3' or LABEL_MAX_UPDATE_SECONDS != 10:
        parser.error('This runner is for guard-v3 with a 10-second observation limit')
    manifest = read_json(rebuild / 'reports/latest/manifest.json')
    if manifest['status'] != 'complete':
        parser.error('Rebuild is not complete')
    all_keys = [int(r['session_key']) for r in manifest['plan']]
    if len(set(all_keys)) != len(all_keys):
        parser.error('Duplicate session keys in rebuild plan')
    selected = set(args.sessions) if args.sessions else set(all_keys)
    if not selected <= set(all_keys):
        parser.error('Requested sessions are not in the rebuild plan')
    keys = [key for key in all_keys if key in selected]
    report_dir.mkdir(parents=True, exist_ok=True)
    summary_path = report_dir / 'summary.json'
    if summary_path.exists() and not args.resume:
        parser.error('Report already exists. Use --resume or choose another --report-dir')
    sources = read_json(rebuild / 'source_hashes.json')
    if args.resume and summary_path.exists() and read_json(summary_path).get('rebuild') != str(rebuild):
        parser.error('This report directory belongs to a different rebuild')
    summary = {'status': 'running', 'rebuild': str(rebuild), 'selected_sessions': keys,
               'full_dataset': selected == set(all_keys), 'expected_sessions': len(all_keys),
               'results': [], 'limitations': [
                   'Raw validator checks known labels against records and metadata; it does not independently prove unknown rows should be unknown.',
                   'No video truth verification or model retraining is performed.',
                   'The raw validator is separately implemented but shares the label policy assumptions.']}
    save(summary_path, summary)
    try:
        for index, key in enumerate(keys, 1):
            print(f'START {index}/{len(keys)} session={key}', flush=True)
            path = report_dir / f'session_{key}.json'
            previous = read_json(path) if args.resume and path.exists() else None
            try:
                result = validate_one(key, rebuild, sources, previous, report_dir)
            except Exception as exc:
                detail = traceback.format_exc()
                (report_dir / f'session_{key}_error.txt').write_text(detail, encoding='utf-8')
                result = {'session_key': key, 'status': 'failed', 'error': f'{type(exc).__name__}: {exc}'}
            finally:
                timestamp.cache_clear()
            save(path, result)
            summary['results'].append(result)
            save(summary_path, summary)
            print(f"{result['status'].upper()} session={key}" + (' (reused)' if result.get('reused') else ''), flush=True)
    except KeyboardInterrupt:
        summary['status'] = 'interrupted'
        save(summary_path, summary)
        print(f'Interrupted. Resume with the same arguments plus --resume. REPORT: {summary_path}', flush=True)
        return 130
    failures = [r for r in summary['results'] if r['status'] != 'passed']
    summary['status'] = 'failed' if failures else ('passed' if summary['full_dataset'] else 'subset_passed')
    summary['passed_sessions'] = len(keys) - len(failures)
    summary['failed_sessions'] = [r['session_key'] for r in failures]
    save(summary_path, summary)
    with (report_dir / 'results.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['session_key', 'status', 'rows', 'known_rows', 'reused', 'error'], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(summary['results'])
    print(f"SUMMARY status={summary['status']} passed={summary['passed_sessions']}/{len(keys)} failed={summary['failed_sessions']}", flush=True)
    print(f'REPORT: {summary_path}', flush=True)
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())

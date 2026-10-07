"""Three-race pilot. Run from backend: python -m app.pipeline.batch

Uses bundled historical JSON when present, otherwise existing collect.py.
Writes per-race candidates/labels plus a fresh comparison report for this run.
No train/test split or combined training dataset is created at this stage.
"""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

import pandas as pd

from app.pipeline.extract import extract_candidates, build_control, CONTROL_POLICY_VERSION
from app.pipeline.label import make_labels, validate_labels, LABEL_VERSION

ENDPOINTS = ('drivers', 'intervals', 'position', 'laps', 'stints', 'pit', 'race_control', 'overtakes')
PILOT = {9472: 'Bahrain 2024', 9480: 'Saudi Arabia 2024', 9488: 'Australia 2024'}
ROOT = Path(__file__).resolve().parents[2]


def read_data(key, raw_root):
    folder = raw_root / str(key)
    files = [folder / (endpoint + '.json') for endpoint in ENDPOINTS]
    if any(p.exists() for p in files):
        missing = [p.name for p in files if not p.exists()]
        if missing:
            raise ValueError(f'불완전한 원본 폴더: {folder}; 누락={missing}')
        data = {endpoint: json.loads(path.read_text(encoding='utf-8-sig'))
                for endpoint, path in zip(ENDPOINTS, files)}
        source = 'bundled_json'
    else:
        from app.pipeline.collect import get_race_data
        data = get_race_data(session_key=key)
        source = 'collect'
    for endpoint in ENDPOINTS:
        if not isinstance(data.get(endpoint), list):
            raise ValueError(f'{endpoint}: 원본 목록이 없습니다.')
        if any(row.get('session_key') != key for row in data[endpoint]):
            raise ValueError(f'{endpoint}: 다른 경기 또는 경기 번호 결측')
    for endpoint in ('drivers', 'intervals', 'position', 'laps', 'stints', 'race_control'):
        if not data[endpoint]:
            raise ValueError(f'{endpoint}: 필수 원본이 비어 있습니다.')
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return data, source, digest


def control_windows(events):
    # Coalesce messages with the same timestamp before making state intervals.
    by_time = {e['time']: e for e in events}
    rows, opened, current = [], None, None
    for at, e in sorted(by_time.items()):
        state = (bool(e['running'] and e['neutralized']), bool(e['running'] and e['yellow_active']))
        if state != current:
            if opened is not None and current != (False, False):
                rows.append({'start': opened, 'end': at, 'neutralized': current[0],
                             'yellow_active': current[1], 'seconds': (at - opened).total_seconds()})
            opened, current = at, state
    if current and current != (False, False):
        raise ValueError('마지막 원본 메시지까지 제어 상태가 종료되지 않았습니다.')
    return pd.DataFrame(rows, columns=['start', 'end', 'neutralized', 'yellow_active', 'seconds'])


def write_parquet_checked(df, path):
    temp = path.with_name(path.stem + '.tmp.parquet')
    df.to_parquet(temp, engine='pyarrow', index=False)
    pd.testing.assert_frame_equal(df, pd.read_parquet(temp, engine='pyarrow'))
    temp.replace(path)


def write_csv(df, path):
    temp = path.with_suffix('.tmp.csv')
    df.to_csv(temp, index=False, encoding='utf-8-sig')
    temp.replace(path)


def run_one(key, raw_root, processed_root, report_root):
    data, source, digest = read_data(key, raw_root)
    events, unresolved = build_control(data['race_control'])
    if unresolved:
        raise ValueError(f'제어 메시지 해석 미완료: {unresolved}')
    windows = control_windows(events)
    print(f'[{key}] 후보 생성 중...', flush=True)
    prepared, counts, unresolved = extract_candidates(data)
    if unresolved:
        raise ValueError(f'제어 메시지 해석 미완료: {unresolved}')
    print(f'[{key}] {len(prepared)}행 라벨 생성·검증 중...', flush=True)
    labeled = make_labels(prepared, data)
    checks = validate_labels(labeled, data)
    folder = processed_root / str(key)
    folder.mkdir(parents=True, exist_ok=True)
    # Each output is read back and compared before its atomic replacement.
    for name, df in [('candidates', prepared), ('labeled_3lap_v2', labeled)]:
        write_parquet_checked(df, folder / (name + '.parquet'))
    write_csv(windows, report_root / f'control_windows_{key}.csv')
    positive = labeled.target_overtake_3lap.eq(1).fillna(False)
    negative = labeled.target_overtake_3lap.eq(0).fillna(False)
    ready = labeled.offline_eligible & labeled.battle_ready
    uncertain = ready & labeled.target_overtake_3lap.isna()
    known = int(positive.sum() + negative.sum())
    reason_counts = labeled.label_reason.value_counts().to_dict()
    row = {'session_key': key, 'race': PILOT.get(key, str(key)), 'status': 'ok',
           'source': source, 'raw_intervals': len(data['intervals']),
           'candidates': len(labeled), 'ready': int(ready.sum()),
           'positive': int(positive.sum()), 'negative': int(negative.sum()),
           'uncertain_ready': int(uncertain.sum()),
           'excluded': int((~ready).sum()),
           'positive_rate_known': float(positive.sum() / known) if known else None,
           'uncertain_rate_ready': float(uncertain.sum() / ready.sum()) if ready.any() else None,
           'unique_success_events': len(labeled.loc[positive].drop_duplicates(
               ['attacker_number', 'defender_number', 'label_event_time'])),
           'battles': labeled.battle_id.nunique(),
           'neutralized_rows': int(labeled.neutralized.sum()),
           'neutralized_seconds': float(windows.loc[windows.neutralized.eq(True), 'seconds'].sum()),
           'yellow_rows': int(labeled.yellow_active.sum()),
           'pace_coverage_ready': float(labeled.loc[ready, 'recent_race_pace_diff'].notna().mean()) if ready.any() else None,
           'gap_history_coverage_ready': float(labeled.loc[ready, 'gap_history_complete'].mean()) if ready.any() else None,
           'validation_violations': checks['violations'], 'label_version': LABEL_VERSION,
           'control_version': CONTROL_POLICY_VERSION, 'raw_sha256': digest,
           'output': str(folder / 'labeled_3lap_v2.parquet'), 'error': ''}
    (report_root / f'counts_{key}.json').write_text(json.dumps(
        {'raw_counts': dict(counts), 'label_reasons': reason_counts}, indent=2), encoding='utf-8')
    return row


def run_batch(keys, raw_root, processed_root, report_root):
    report_root.mkdir(parents=True, exist_ok=True)
    rows = []
    for key in dict.fromkeys(keys):
        try:
            row = run_one(key, raw_root, processed_root, report_root)
            print(f"[{key}] 완료: 성공 {row['positive']}, 실패 {row['negative']}, 미확정 {row['uncertain_ready']}", flush=True)
        except Exception as exc:
            row = {'session_key': key, 'race': PILOT.get(key, str(key)), 'status': 'failed',
                   'output': '', 'error': f'{type(exc).__name__}: {exc}'}
            print(f"[{key}] 실패: {row['error']}", flush=True)
        rows.append(row)
        write_csv(pd.DataFrame(rows), report_root / 'comparison.csv')
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session-keys', type=int, nargs='+', default=list(PILOT))
    parser.add_argument('--raw-dir', type=Path, default=ROOT / 'data' / 'pilot_raw')
    args = parser.parse_args()
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid4().hex[:6]
    report_root = ROOT / 'data' / 'processed' / 'pilot_reports' / run_id
    result = run_batch(args.session_keys, args.raw_dir, ROOT / 'data' / 'processed', report_root)
    print('\n=== 경기별 비교 ===')
    cols = ['session_key', 'race', 'status', 'ready', 'positive', 'negative',
            'uncertain_ready', 'unique_success_events', 'neutralized_rows', 'validation_violations', 'error']
    print(result.reindex(columns=cols).to_string(index=False))
    print(f'\n비교표: {report_root / "comparison.csv"}')
    print('미확정률의 분모는 ready 관측입니다. 데이터 일관성 검증이며 독립 추월 정답 검증은 아닙니다.')
    if result.status.ne('ok').any():
        raise SystemExit(1)


if __name__ == '__main__':
    main()

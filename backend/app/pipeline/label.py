"""Conservative v2 labels with post-event gap corroboration. Run: python -m app.pipeline.label

Outcome: pass the defender fixed at prediction time by the attacker's third
subsequent lap completion (current lap N through N+2). These are provisional
race-data labels, not independently verified ground truth. Future-derived
label/audit columns must NEVER be used as model inputs.
"""
import argparse
from bisect import bisect_right, bisect_left
from functools import lru_cache
import math
from collections import defaultdict
from pathlib import Path

import pandas as pd

from app.pipeline.extract import (
    Config, build_control, build_lap_index, lap_at, state_at, timestamp,
)


LABEL_VERSION = 'v2-gap-evidence'


def make_labels(candidates, data, horizon_laps=3, confirmation_seconds=10.0,
                evidence_seconds=10.0, gap_pair_skew_seconds=2.0, min_gap_pairs=2):
    if (horizon_laps != 3 or confirmation_seconds < 0 or evidence_seconds <= 0
            or gap_pair_skew_seconds <= 0 or min_gap_pairs < 1):
        raise ValueError('3랩 라벨 설정값을 확인하세요.')
    config = Config()
    events, unresolved = build_control(data['race_control'])
    if unresolved:
        raise ValueError(f'먼저 제어 메시지를 확인하세요: {unresolved}')
    event_times = [e['time'] for e in events]
    laps = build_lap_index(data, events, config)
    sessions = set(candidates.session_key)
    if len(sessions) != 1:
        raise ValueError('한 번에 한 경기만 처리하세요.')
    for rows in data.values():
        if isinstance(rows, list):
            for r in rows:
                if isinstance(r, dict) and r.get('session_key') is not None:
                    if r['session_key'] not in sessions:
                        raise ValueError('다른 경기 원본이 섞여 있습니다.')

    positions, updates, passes = defaultdict(list), defaultdict(list), defaultdict(list)
    gap_values = defaultdict(dict)
    for r in data['position']:
        positions[int(r['driver_number'])].append((timestamp(r['date']), int(r['position'])))
    for r in data['intervals']:
        driver, t = int(r['driver_number']), timestamp(r['date'])
        updates[driver].append(t)
        value = r.get('gap_to_leader')
        # Strings such as '+1 LAP' and missing values are not numeric gaps.
        valid = (not isinstance(value, bool) and isinstance(value, (int, float))
                 and math.isfinite(value) and value >= 0)
        gap_values[driver][t] = float(value) if valid else None
    for r in data['overtakes']:
        required = {'date', 'overtaking_driver_number', 'overtaken_driver_number'}
        if not required <= r.keys():
            raise ValueError(f'overtakes 필드 확인 필요: {sorted(r.keys())}')
        pair = (int(r['overtaking_driver_number']), int(r['overtaken_driver_number']))
        passes[pair].append(timestamp(r['date']))
    for mapping in (positions, updates, passes):
        for key in mapping:
            mapping[key] = sorted(set(mapping[key]))
    pos_times = {d: [x[0] for x in rows] for d, rows in positions.items()}

    def position(d, t):
        i = bisect_right(pos_times.get(d, []), t) - 1
        return positions[d][i][1] if i >= 0 else None

    def coverage_problem(driver, start, stop):
        """Intervals are NOT uniform heartbeats: skip gap-age checks while leader.

        Completed, consecutive laps are still required by censor(). On losing
        the lead, start a new 10-second grace window, then require updates.
        Non-leaders retain the original conservative 10-second policy.
        """
        times = updates.get(driver, [])
        i = bisect_right(times, start) - 1
        last = times[i] if i >= 0 else None
        rank = position(driver, start)
        ps = pos_times.get(driver, [])
        knots = sorted(set(times[bisect_right(times, start):bisect_right(times, stop)]
                           + ps[bisect_right(ps, start):bisect_right(ps, stop)] + [stop]))
        for t in knots:
            if rank != 1:
                if last is None:
                    return start
                deadline = last + pd.Timedelta(seconds=config.max_update_seconds)
                if t > deadline:
                    return max(start, deadline)
            new_rank = position(driver, t)
            if rank == 1 and new_rank != 1:
                last = t
            if t in gap_values.get(driver, {}):
                last = t
            rank = new_rank
        return None

    @lru_cache(maxsize=None)
    def pair_runs(a, d):
        """All observed attacker-ahead runs. A tie/missing rank ends a run."""
        times = sorted(set(pos_times.get(a, []) + pos_times.get(d, [])))
        runs, opened = [], None
        for t in times:
            pa, pd_ = position(a, t), position(d, t)
            ahead = pa is not None and pd_ is not None and pa < pd_
            if ahead and opened is None:
                opened = t
            elif not ahead and opened is not None:
                runs.append((opened, t))
                opened = None
        if opened is not None:
            runs.append((opened, None))
        return tuple(runs)

    @lru_cache(maxsize=None)
    def event_evidence(a, d, event):
        """Match a reversal, then seek distinct, fresh paired gap observations.

        No minimum lead duration. Even a short pass qualifies if two distinct
        paired observations support it before the run ends. Later runs are
        evaluated separately, never credited to an earlier transient event.
        This is corroboration within the same feed, NOT independent truth.
        """
        runs = [r for r in pair_runs(a, d)
                if abs((r[0] - event).total_seconds()) <= confirmation_seconds
                and (r[1] is None or event < r[1])]
        if not runs:
            return {'status': 'position_disagreement', 'event': event}
        opened, closed = min(runs, key=lambda r: abs((r[0] - event).total_seconds()))
        if any(t != event and abs((opened - t).total_seconds()) < abs((opened - event).total_seconds())
               for t in passes.get((a, d), [])):
            return {'status': 'position_disagreement', 'event': event}
        begin = max(opened, event)
        end = begin + pd.Timedelta(seconds=evidence_seconds)
        if closed is not None:
            end = min(end, closed)
        times = sorted(set(t for driver in (a, d)
                           for t in updates.get(driver, []) if begin <= t <= end))
        latest, used, count = {}, {}, 0
        details = {'event': event, 'reversal': opened, 'run_end': closed,
                   'count': 0, 'status': 'unconfirmed_pass'}
        for t in times:
            if closed is not None and t >= closed:
                break
            for driver in (a, d):
                if t in gap_values.get(driver, {}):
                    latest[driver] = (t, gap_values[driver][t])
            if a not in latest or d not in latest:
                continue
            ta, ga = latest[a]
            td, gd = latest[d]
            if used and (ta <= used[a] or td <= used[d]):
                continue
            if abs((ta - td).total_seconds()) > gap_pair_skew_seconds:
                continue
            used = {a: ta, d: td}
            if ga is None or gd is None or ga >= gd:
                count = 0
                continue
            # Do not compare gaps across different lap numbers (line crossing
            # or lapping). Wait for a fresh pair with matching lap numbers.
            al, dl = lap_at(laps, a, t), lap_at(laps, d, t)
            if al is None or dl is None or al['number'] != dl['number']:
                count = 0
                continue
            count += 1
            if count >= min_gap_pairs:
                return {**details, 'status': 'supported', 'confirmation': t,
                        'count': count, 'gap_attacker_time': ta, 'gap_defender_time': td,
                        'gap_attacker': ga, 'gap_defender': gd}
        return {**details, 'count': count}

    def censor(a, d, start, stop):
        """Earliest interruption. Pit laps excluded from their start, conservatively."""
        bad = []
        state = state_at(events, event_times, start)
        states = [(start, state)] + [(e['time'], e) for e in events
                                   if start < e['time'] <= stop]
        for t, s in states:
            if not s['running']:
                bad.append((t, 'session_end'))
            elif s['neutralized'] or s['yellow_active']:
                bad.append((t, 'race_control'))
            elif a in s['retired'] or d in s['retired']:
                bad.append((t, 'retirement'))
        for driver in (a, d):
            rows = laps.get(driver, {}).get('laps', [])
            current = lap_at(laps, driver, start)
            if current is None:
                bad.append((start, 'missing_lap'))
                continue
            expected, covered = current['number'], start
            for lap in rows:
                if lap['number'] < current['number'] or lap['start'] > stop:
                    continue
                t = max(start, lap['start'])
                if lap['number'] != expected or lap['start'] > covered:
                    bad.append((covered, 'lap_data_gap'))
                expected = lap['number'] + 1
                if lap['pit_lap'] or lap['out_lap']:
                    bad.append((t, 'pit_related'))
                if lap['duration'] is None or lap['end'] is None:
                    bad.append((t, 'incomplete_lap'))
                else:
                    covered = max(covered, lap['end'])
            if covered < stop:
                bad.append((covered, 'observation_end'))
            missing = coverage_problem(driver, start, stop)
            if missing is not None:
                bad.append((missing, 'interval_coverage'))
        return min(bad) if bad else (None, None)

    outputs = []
    for r in candidates.itertuples(index=False):
        start = timestamp(r.prediction_time)
        a, d = int(r.attacker_number), int(r.defender_number)
        out = {'target_overtake_3lap': None, 'label_reason': 'not_eligible',
               'label_horizon_end': pd.NaT, 'label_event_time': pd.NaT,
               'label_confirmation_time': pd.NaT, 'label_censor_time': pd.NaT,
               'label_version': LABEL_VERSION, 'label_reversal_time': pd.NaT,
               'label_gap_pairs': 0, 'label_evidence_window_seconds': evidence_seconds,
               'label_gap_pair_skew_seconds': gap_pair_skew_seconds,
               'label_min_gap_pairs': min_gap_pairs,
               'label_prior_unconfirmed_count': 0,
               'label_gap_attacker_time': pd.NaT, 'label_gap_defender_time': pd.NaT,
               'label_gap_attacker': float('nan'), 'label_gap_defender': float('nan')}

        outputs.append(out)
        if not r.offline_eligible or not r.battle_ready:
            continue
        current = lap_at(laps, a, start)
        if current is None:
            out['label_reason'] = 'missing_lap'
            continue
        target_number = current['number'] + horizon_laps - 1
        target = next((x for x in laps[a]['laps'] if x['number'] == target_number), None)
        # Conservative: no labels if the planned lap boundary is unavailable.
        if target is None or target['end'] is None or target['duration'] is None:
            out['label_reason'] = 'horizon_unobserved'
            continue
        end = target['end']
        out['label_horizon_end'] = end
        if end <= start:
            out['label_reason'] = 'invalid_horizon'
            continue
        pa, pd_ = position(a, start), position(d, start)
        if pa is None or pd_ is None or pa != pd_ + 1:
            out['label_reason'] = 'initial_position_mismatch'
            continue
        cut, reason = censor(a, d, start, end)
        out['label_censor_time'] = cut if cut is not None else pd.NaT
        limit = min(end, cut) if cut is not None else end
        pass_times = [t for t in passes.get((a, d), []) if start < t <= limit]
        unmatched = 0
        matched = None
        for event in pass_times:
            evidence = event_evidence(a, d, event)
            if evidence['status'] == 'supported':
                confirmed = evidence['confirmation']
                if confirmed <= end and (cut is None or confirmed < cut):
                    matched = evidence
                    break
            unmatched += 1
        # Do not turn an unsupported reversal/API event into a negative label.
        reversal_present = any(start < opened <= limit for opened, _ in pair_runs(a, d))
        out['label_prior_unconfirmed_count'] = unmatched
        if matched is not None:
            out.update(target_overtake_3lap=1, label_reason='confirmed_pass',
                       label_event_time=matched['event'],
                       label_confirmation_time=matched['confirmation'],
                       label_reversal_time=matched['reversal'],
                       label_gap_pairs=matched['count'],
                       label_gap_attacker_time=matched['gap_attacker_time'],
                       label_gap_defender_time=matched['gap_defender_time'],
                       label_gap_attacker=matched['gap_attacker'],
                       label_gap_defender=matched['gap_defender'])
        elif pass_times or reversal_present:
            out['label_reason'] = 'unconfirmed_pass'
        elif cut is not None:
            out['label_reason'] = reason
        else:
            out.update(target_overtake_3lap=0, label_reason='no_observed_pass')
    result = candidates.copy().reset_index(drop=True)
    audit = pd.DataFrame(outputs)
    for column in audit:
        result[column] = audit[column]
    result['target_overtake_3lap'] = result['target_overtake_3lap'].astype('Int64')
    for column in ('label_horizon_end', 'label_event_time', 'label_confirmation_time', 'label_censor_time',
                   'label_reversal_time', 'label_gap_attacker_time', 'label_gap_defender_time'):
        result[column] = pd.to_datetime(result[column], utc=True)
    return result


def validate_labels(labeled, data):
    """Check emitted labels against raw records; raise before saving on failure.

    This checks record consistency, not video-confirmed on-track truth.
    """
    from bisect import bisect_right
    raw_events = {(int(r['overtaking_driver_number']), int(r['overtaken_driver_number']),
                   timestamp(r['date'])) for r in data['overtakes']}
    raw_gaps = {(int(r['driver_number']), timestamp(r['date'])): r.get('gap_to_leader')
                for r in data['intervals']}
    positions = defaultdict(list)
    raw_laps = defaultdict(list)
    for r in data['position']:
        positions[int(r['driver_number'])].append((timestamp(r['date']), int(r['position'])))
    for driver in positions:
        positions[driver].sort()
    times = {d: [t for t, _ in rows] for d, rows in positions.items()}
    for r in data['laps']:
        if r.get('date_start'):
            raw_laps[int(r['driver_number'])].append(r)
    for driver in raw_laps:
        raw_laps[driver].sort(key=lambda r: timestamp(r['date_start']))
    raw_start_times = {d: [timestamp(r['date_start']) for r in rows]
                       for d, rows in raw_laps.items()}
    completion_by_number = {}
    for driver, rows in raw_laps.items():
        for j, lap in enumerate(rows):
            duration = lap.get('lap_duration')
            if duration is None:
                continue
            expected = raw_start_times[driver][j] + pd.Timedelta(seconds=duration)
            if j + 1 < len(rows):
                expected = max(expected, raw_start_times[driver][j + 1])
            completion_by_number[driver, int(lap['lap_number'])] = expected
    def rank(driver, at):
        i = bisect_right(times.get(driver, []), at) - 1
        return positions[driver][i][1] if i >= 0 else None
    errors = []
    def check(condition, row, name):
        if not condition:
            errors.append((row, name))
    for index, r in enumerate(labeled.itertuples(index=False)):
        check(r.label_version == LABEL_VERSION, index, 'version')
        if pd.isna(r.target_overtake_3lap):
            continue
        y = r.target_overtake_3lap
        a, d, start, end = int(r.attacker_number), int(r.defender_number), r.prediction_time, r.label_horizon_end
        check(y in (0, 1), index, 'target')
        check(r.offline_eligible and r.battle_ready, index, 'eligible')
        check(pd.notna(end) and end > start, index, 'horizon')
        check(rank(a, start) is not None and rank(d, start) is not None
              and rank(a, start) == rank(d, start) + 1, index, 'initial_pair')
        # Independently resolve current N and completion of N+2 from raw laps.
        lr = raw_laps[a]
        current_index = bisect_right(raw_start_times[a], start) - 1
        expected = None if current_index < 0 else completion_by_number.get(
            (a, int(lr[current_index]['lap_number']) + 2))
        check(expected is not None and end == expected, index, 'third_completion')
        if y == 1:
            event, confirmed = r.label_event_time, r.label_confirmation_time
            check((a, d, event) in raw_events, index, 'raw_event')
            check(start < event <= confirmed <= end, index, 'success_window')
            check(r.label_reason == 'confirmed_pass', index, 'success_reason')
            check(pd.isna(r.label_censor_time) or confirmed < r.label_censor_time, index, 'censor')
            check(r.label_gap_pairs >= r.label_min_gap_pairs, index, 'gap_pairs')
            ta, td = r.label_gap_attacker_time, r.label_gap_defender_time
            check(ta >= event and td >= event and max(ta, td) == confirmed, index, 'evidence_time')
            check(abs((ta - td).total_seconds()) <= r.label_gap_pair_skew_seconds, index, 'gap_skew')
            ga, gd = raw_gaps.get((a, ta)), raw_gaps.get((d, td))
            check(ga == r.label_gap_attacker and gd == r.label_gap_defender
                  and ga is not None and gd is not None and ga < gd, index, 'raw_gap_evidence')
            check(rank(a, confirmed) is not None and rank(d, confirmed) is not None
                  and rank(a, confirmed) < rank(d, confirmed), index, 'confirmed_order')
        else:
            check(r.label_reason == 'no_observed_pass', index, 'negative_reason')
            check(pd.isna(r.label_event_time) and pd.isna(r.label_confirmation_time)
                  and pd.isna(r.label_censor_time), index, 'negative_metadata')
            check(not any(x == a and z == d and start < t <= end for x, z, t in raw_events),
                  index, 'negative_api_event')
            knots = sorted(set(t for dr in (a, d) for t in times.get(dr, []) if start < t <= end))
            check(not any(rank(a, t) is not None and rank(d, t) is not None
                          and rank(a, t) < rank(d, t) for t in knots), index, 'negative_reversal')
    if errors:
        raise ValueError(f'v2 라벨 검증 실패 {len(errors)}건: {errors[:10]}')
    return {'rows': len(labeled), 'labeled_rows': int(labeled.target_overtake_3lap.notna().sum()),
            'violations': 0}


def main():
    from app.pipeline.collect import get_race_data
    from app.pipeline.load import load_candidates
    parser = argparse.ArgumentParser()
    parser.add_argument('--session-key', type=int, default=9472)
    args = parser.parse_args()
    candidates = load_candidates(args.session_key)
    data = get_race_data(args.session_key)
    print(f'[v2] 후보 {len(candidates)}행 정답 계산 중...', flush=True)
    labeled = make_labels(candidates, data)
    print('[v2] 원본 기록 대조 검증 중...', flush=True)
    checks = validate_labels(labeled, data)
    print(f"\n=== v2 통합 검증 ===\n정답 보유: {checks['labeled_rows']} / 위반: {checks['violations']}")
    folder = Path(__file__).resolve().parents[2] / 'data' / 'processed' / str(args.session_key)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / 'labeled_3lap_v2.parquet'
    temporary = folder / 'labeled_3lap_v2.tmp.parquet'
    labeled.to_parquet(temporary, engine='pyarrow', index=False)
    pd.testing.assert_frame_equal(labeled, pd.read_parquet(temporary, engine='pyarrow'))
    temporary.replace(path)
    print('\n=== 3랩 정답 집계 (1=성공, 0=관측상 추월 없음, NA=미확정) ===')
    print(labeled.target_overtake_3lap.value_counts(dropna=False).to_string())
    print('\n=== 판정 사유 ===')
    print(labeled.label_reason.value_counts(dropna=False).to_string())
    print('\n=== 성공 예시 ===')
    cols = ['prediction_time', 'attacker_number', 'defender_number', 'battle_id',
            'label_horizon_end', 'label_event_time', 'label_confirmation_time']
    print(labeled.loc[labeled.target_overtake_3lap.eq(1).fillna(False), cols].head(10).to_string(index=False))
    positives = labeled.loc[labeled.target_overtake_3lap.eq(1).fillna(False)]
    print(f'성공 행 수: {len(positives)} / 고유 성공 이벤트: '
          f'{len(positives.drop_duplicates(["attacker_number", "defender_number", "label_event_time"]))}')
    print(f'\n저장 완료: {path}\n저장 전후 데이터 일치 확인 완료')
    print('v2 자동 라벨: 후속 간격 대조 포함. 실제 추월의 독립 검증은 아닙니다.')
    print('target 및 label_*는 미래 정보이므로 모델 입력 금지.')


if __name__ == '__main__':
    main()

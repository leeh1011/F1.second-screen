import argparse
import math
import re
from bisect import bisect_right
from collections import Counter
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Config:
    enter_gap: float = 2.0
    exit_gap: float = 2.5
    min_battle_seconds: float = 8.0
    max_update_seconds: float = 10.0
    pace_window: int = 3
    min_pace_laps: int = 2


def timestamp(value):
    return pd.to_datetime(value, utc=True)


def finite(value):
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def frame(rows):
    return pd.DataFrame(rows)


def build_control(rows):
    events = []
    neutral = set()
    yellow = set()
    retired = set()
    running = False
    ended = False
    unresolved = []

    for row in sorted(rows, key=lambda r: timestamp(r['date'])):
        msg = str(row.get('message') or '').upper().strip()
        flag = str(row.get('flag') or '').upper()
        scope = str(row.get('scope') or '').upper()
        category = str(row.get('category') or '')
        sector = row.get('sector')
        match = re.search(r'TRACK SECTOR\s+(\d+)', msg)
        if sector is None and match:
            sector = int(match.group(1))
        sector_key = str(sector) if sector is not None else 'unknown'

        if msg == 'SESSION STARTED':
            running = True
            ended = False
            neutral.discard('RED')
        if msg in ('SESSION FINISHED', 'SESSION ENDED') or flag == 'CHEQUERED':
            ended = True
        if msg == 'SESSION SUSPENDED' or flag == 'RED':
            neutral.add('RED')
        if 'VIRTUAL SAFETY CAR DEPLOYED' in msg or msg == 'VSC DEPLOYED':
            neutral.add('VSC')
        elif 'SAFETY CAR DEPLOYED' in msg:
            neutral.add('SC')
        elif msg == 'VSC ENDING' or 'VIRTUAL SAFETY CAR ENDING' in msg:
            neutral.add('VSC')
        elif 'SAFETY CAR IN THIS LAP' in msg:
            neutral.add('SC')

        explicit_green = (
            scope == 'TRACK'
            and (msg in ('GREEN FLAG', 'GREEN TRACK') or flag == 'GREEN')
            and 'PIT EXIT' not in msg
            and 'GREEN LIGHT' not in msg
        )
        if explicit_green:
            neutral.clear()
            yellow.clear()
            running = True

        if flag in ('YELLOW', 'DOUBLE YELLOW'):
            yellow.add(sector_key if scope == 'SECTOR' else 'track')
        if scope == 'SECTOR' and (flag in ('GREEN', 'CLEAR') or 'CLEAR' in msg):
            yellow.discard(sector_key)
        elif match and ('CLEAR' in msg or 'GREEN' in msg):
            yellow.discard(sector_key)

        known_sc = any(token in msg for token in (
            'DEPLOYED', 'ENDING', 'IN THIS LAP',
        )) or explicit_green
        if category == 'SafetyCar' and not known_sc:
            neutral.add('UNKNOWN_CONTROL')
            unresolved.append(msg)

        if 'RETIRED' in msg:
            number = row.get('driver_number')
            car_match = re.search(r'CAR\s+(\d+)', msg)
            if number is None and car_match:
                number = int(car_match.group(1))
            if number is not None:
                retired.add(int(number))
            else:
                unresolved.append(msg)

        events.append({
            'time': timestamp(row['date']),
            'running': running and not ended,
            'neutralized': bool(neutral),
            'yellow_active': bool(yellow),
            'retired': frozenset(retired),
        })

    if not any(e['running'] for e in events):
        raise ValueError('SESSION STARTED를 찾을 수 없습니다.')
    return events, unresolved


def state_at(events, times, at):
    index = bisect_right(times, at) - 1
    if index < 0:
        return {'running': False, 'neutralized': False,
                'yellow_active': False, 'retired': frozenset()}
    return events[index]


def interrupted_lap(start, end, events, times):
    samples = [state_at(events, times, start)]
    samples.extend(events[bisect_right(times, start):bisect_right(times, end)])
    return any(not s['running'] or s['neutralized'] or s['yellow_active'] for s in samples)


def build_lap_index(race_data, events, config):
    event_times = [e['time'] for e in events]
    pit_laps = {(int(r['driver_number']), int(r['lap_number']))
                for r in race_data['pit'] if r.get('lap_number') is not None}
    grouped = {}
    for row in race_data['laps']:
        if row.get('date_start'):
            grouped.setdefault(int(row['driver_number']), []).append(row)
    index = {}
    for driver, rows in grouped.items():
        rows = sorted(rows, key=lambda r: timestamp(r['date_start']))
        laps, pace_events, history = [], [], []
        previous = None
        for i, row in enumerate(rows):
            start = timestamp(row['date_start'])
            number = int(row['lap_number'])
            duration = row.get('lap_duration')
            valid_duration = finite(duration) and duration > 0
            end = start + pd.Timedelta(seconds=duration) if valid_duration else None
            next_start = timestamp(rows[i + 1]['date_start']) if i + 1 < len(rows) else None
            if next_start is not None:
                end = next_start if end is None else max(end, next_start)
            item = {'start': start, 'end': end, 'number': number,
                    'duration': float(duration) if valid_duration else None,
                    'pit_lap': (driver, number) in pit_laps,
                    'out_lap': row.get('is_pit_out_lap') is True}
            laps.append(item)
            consecutive = previous is None or number == previous + 1
            previous = number
            valid = (
                consecutive and valid_duration and number > 1
                and not item['pit_lap'] and not item['out_lap']
                and row.get('is_pit_out_lap') is False
                and not interrupted_lap(start, end, events, event_times)
            )
            if valid:
                history.append(float(duration))
                history = history[-config.pace_window:]
            else:
                history = []
            if end is not None:
                pace_events.append({
                    'time': end,
                    'pace': sum(history) / len(history) if len(history) >= config.min_pace_laps else None,
                    'count': len(history),
                })
        completions = [l for l in laps if l['duration'] is not None and l['end'] is not None]
        index[driver] = {
            'laps': laps, 'starts': [l['start'] for l in laps],
            'pace': sorted(pace_events, key=lambda p: p['time']),
            'completed': sorted(completions, key=lambda l: l['end']),
        }
        index[driver]['pace_times'] = [p['time'] for p in index[driver]['pace']]
        index[driver]['completion_times'] = [l['end'] for l in index[driver]['completed']]
    return index


def lap_at(index, driver, at):
    data = index.get(driver)
    if data is None:
        return None
    i = bisect_right(data['starts'], at) - 1
    return data['laps'][i] if i >= 0 else None


def tyre_at(stints, driver, lap):
    choices = [s for s in stints.get(driver, []) if s['lap_start'] <= lap]
    if not choices:
        return None, None, False
    stint = max(choices, key=lambda s: s['lap_start'])
    transition = stint['lap_start'] > 1 and lap == stint['lap_start']
    initial = stint.get('tyre_age_at_start')
    age = initial + lap - stint['lap_start'] if finite(initial) and initial >= 0 else None
    if transition:
        return None, None, True
    return stint.get('compound'), age, False


def pace_at(index, driver, at):
    data = index[driver]
    i = bisect_right(data['pace_times'], at) - 1
    if i < 0:
        return None, 0
    event = data['pace'][i]
    return event['pace'], event['count']


def history_features(points, at, gap, duration):
    result = {'gap_mean_last_lap': None, 'gap_trend_last_lap': None,
              'gap_1_lap_ago': None, 'gap_history_complete': False,
              'gap_history_window_seconds': duration}
    if duration is None or not points:
        return result
    start = at - pd.Timedelta(seconds=duration)
    times = [p[0] for p in points]
    i = bisect_right(times, start) - 1
    if i < 0:
        return result
    value = points[i][1]
    old_gap = value
    cursor = start
    area = 0.0
    for when, next_value in points[i + 1:]:
        area += value * (when - cursor).total_seconds()
        cursor, value = when, next_value
    area += value * (at - cursor).total_seconds()
    result.update({
        'gap_mean_last_lap': area / duration,
        'gap_trend_last_lap': (gap - old_gap) / duration,
        'gap_1_lap_ago': old_gap,
        'gap_history_complete': True,
    })
    return result


def extract_candidates(race_data, config=Config()):
    if not (0 < config.enter_gap <= config.exit_gap and config.max_update_seconds > 0
            and config.min_battle_seconds >= 0
            and 1 <= config.min_pace_laps <= config.pace_window):
        raise ValueError('설정값을 확인하세요.')
    events, unresolved = build_control(race_data['race_control'])
    event_times = [e['time'] for e in events]
    lap_index = build_lap_index(race_data, events, config)
    stints = {}
    for s in race_data['stints']:
        if s.get('lap_start') is not None:
            stints.setdefault(int(s['driver_number']), []).append(s)
    positions = sorted(race_data['position'], key=lambda r: timestamp(r['date']))
    intervals = sorted(race_data['intervals'], key=lambda r: timestamp(r['date']))
    seen = set()
    for raw in intervals:
        key = (raw['driver_number'], timestamp(raw['date']))
        if key in seen:
            raise ValueError('같은 차량·시각의 간격 기록이 중복됩니다.')
        seen.add(key)
    latest_positions, last_gaps, active = {}, {}, {}
    sequences, counts = Counter(), Counter()
    result = []
    p = 0
    for raw in intervals:
        counts['raw_intervals'] += 1
        at = timestamp(raw['date'])
        attacker = int(raw['driver_number'])
        gap = raw.get('interval')
        while p < len(positions) and timestamp(positions[p]['date']) <= at:
            changed_driver = int(positions[p]['driver_number'])
            new_position = positions[p]['position']
            if latest_positions.get(changed_driver) != new_position:
                for key in list(active):
                    if key == changed_driver or active[key]['defender'] == changed_driver:
                        active.pop(key, None)
            latest_positions[changed_driver] = new_position
            p += 1
        state = state_at(events, event_times, at)
        rank = latest_positions.get(attacker)
        ranks = Counter(latest_positions.values())
        defender = next((d for d, r in latest_positions.items() if rank and r == rank - 1), None)
        fresh = finite(gap) and gap > 0
        reason = None
        if not state['running']:
            reason = 'outside_session'
        elif not fresh:
            reason = 'invalid_gap'
        elif rank is None or rank <= 1 or ranks[rank] != 1 or ranks[rank - 1] != 1:
            reason = 'unresolved_pair'
        elif gap > config.exit_gap:
            reason = 'above_exit_gap'
        last_gaps[attacker] = (at, gap, defender)
        if reason:
            active.pop(attacker, None)
            counts[reason] += 1
            continue
        a_lap = lap_at(lap_index, attacker, at)
        d_lap = lap_at(lap_index, defender, at)
        if a_lap is None or d_lap is None:
            active.pop(attacker, None)
            counts['missing_lap'] += 1
            continue
        row = {
            'session_key': raw['session_key'], 'prediction_time': at,
            'attacker_number': attacker, 'defender_number': defender,
            'attacker_position': rank, 'defender_position': rank - 1,
            'gap': float(gap), 'seconds_since_lap_start': (at - a_lap['start']).total_seconds(),
            'first_lap': a_lap['number'] == 1 or d_lap['number'] == 1,
            'neutralized': state['neutralized'], 'yellow_active': state['yellow_active'],
            'retired_confirmed': attacker in state['retired'] or defender in state['retired'],
            'lap_alignment_uncertain': a_lap['number'] != d_lap['number'],
            'pit_related_lap': False, 'observation_end_unknown': False,
            'after_last_observed_lap': False,
        }
        for role, driver, lap in [('attacker', attacker, a_lap), ('defender', defender, d_lap)]:
            compound, age, transition = tyre_at(stints, driver, lap['number'])
            pace, count = pace_at(lap_index, driver, at)
            row.update({f'{role}_lap': lap['number'], f'{role}_lap_start': lap['start'],
                        f'{role}_compound': compound, f'{role}_tyre_age': age,
                        f'{role}_recent_pace': pace, f'{role}_pace_lap_count': count,
                        f'{role}_tyre_transition_lap': transition})
            row['pit_related_lap'] |= lap['pit_lap'] or lap['out_lap'] or transition
            row['observation_end_unknown'] |= lap['end'] is None
            row['after_last_observed_lap'] |= lap['end'] is not None and at >= lap['end']
        row['tyre_features_missing'] = any(row[k] is None for k in (
            'attacker_compound', 'defender_compound', 'attacker_tyre_age', 'defender_tyre_age'))
        row['tyre_age_diff'] = None if row['tyre_features_missing'] else row['attacker_tyre_age'] - row['defender_tyre_age']
        row['recent_race_pace_diff'] = (
            row['attacker_recent_pace'] - row['defender_recent_pace']
            if row['attacker_recent_pace'] is not None and row['defender_recent_pace'] is not None else None)
        row['defender_is_leader'] = rank == 2
        row['defender_gap_ahead'] = None
        row['defender_in_train'] = 0 if rank == 2 else None
        saved = last_gaps.get(defender)
        if saved and rank != 2:
            age_seconds = (at - saved[0]).total_seconds()
            front = saved[2]
            same_front = front is not None and latest_positions.get(front) == rank - 2 and ranks[rank - 2] == 1
            if age_seconds <= config.max_update_seconds and finite(saved[1]) and saved[1] > 0 and same_front:
                row['defender_gap_ahead'] = float(saved[1])
                row['defender_in_train'] = int(saved[1] <= 1)
        excluded = [key for key in (
            'first_lap', 'neutralized', 'yellow_active', 'retired_confirmed',
            'lap_alignment_uncertain', 'pit_related_lap', 'observation_end_unknown',
            'after_last_observed_lap', 'tyre_features_missing') if row[key]]
        row['exclusion_reasons'] = '|'.join(excluded)
        row['offline_eligible'] = not excluded
        row.update({'battle_id': None, 'battle_age_seconds': None, 'battle_ready': False,
                    'time_within_1_sec': None, 'gap_mean_last_lap': None,
                    'gap_trend_last_lap': None, 'gap_1_lap_ago': None,
                    'gap_history_complete': False, 'gap_history_window_seconds': None})
        reset_reasons = [
            reason
            for reason in excluded
            if reason != "lap_alignment_uncertain"
        ]

        if reset_reasons:
            active.pop(attacker, None)
        else:
            battle = active.get(attacker)
            if battle and (battle['defender'] != defender
                           or (at - battle['last']).total_seconds() > config.max_update_seconds
                           or interrupted_lap(battle['last'], at, events, event_times)):
                active.pop(attacker, None)
                battle = None
            if battle is None and gap <= config.enter_gap:
                sequences[attacker] += 1
                battle = {'defender': defender, 'start': at, 'last': at, 'points': [],
                          'within': None,
                          'id': f"{raw['session_key']}-{attacker}-{sequences[attacker]}"}
                active[attacker] = battle
            if battle:
                battle['last'] = at
                battle['points'].append((at, float(gap)))
                if gap <= 1:
                    if battle['within'] is None:
                        battle['within'] = at
                else:
                    battle['within'] = None
                age_seconds = (at - battle['start']).total_seconds()
                data = lap_index[attacker]
                ci = bisect_right(data['completion_times'], at) - 1
                duration = data['completed'][ci]['duration'] if ci >= 0 else None
                row.update(history_features(battle['points'], at, float(gap), duration))
                row.update({'battle_id': battle['id'], 'battle_age_seconds': age_seconds,
                            'battle_ready': (
                                row['offline_eligible']
                                and age_seconds >= config.min_battle_seconds
                            ),
                            'time_within_1_sec': (at - battle['within']).total_seconds() if battle['within'] is not None else 0.0})
        result.append(row)
    if not result:
        raise ValueError('후보가 없습니다. 수집 데이터와 조건을 확인하세요.')
    df = frame(result).sort_values('prediction_time').reset_index(drop=True)
    df['defender_in_train'] = df['defender_in_train'].astype('Int64')
    df['battle_id'] = df['battle_id'].astype('string')
    return df, counts, unresolved


def main():
    from app.pipeline.collect import get_race_data
    from app.pipeline.load import save_candidates, load_candidates

    parser = argparse.ArgumentParser()
    parser.add_argument('--session-key', type=int, default=9472)
    args = parser.parse_args()
    data = get_race_data(args.session_key)
    prepared, counts, unresolved = extract_candidates(data)
    print('\n=== 원본 관측 처리 ===')
    for key, value in counts.items():
        print(f'{key}: {value}')
    flags = ['first_lap', 'neutralized', 'yellow_active', 'retired_confirmed',
             'lap_alignment_uncertain', 'pit_related_lap', 'observation_end_unknown',
             'after_last_observed_lap', 'tyre_features_missing']
    print('\n=== 제외 표시 (중복 가능) ===')
    print(prepared[flags].sum().to_string())
    print('\n=== 배틀 및 피처 집계 ===')
    print(f'후보 관측: {len(prepared)}')
    print(f'사후 품질 조건 통과: {prepared.offline_eligible.sum()}')
    print(f'배틀 에피소드: {prepared.battle_id.nunique()}')
    ready = prepared[prepared.battle_ready]
    print(f'8초 이상 배틀 관측: {len(ready)}')
    print(f'최근 페이스 차이 보유: {ready.recent_race_pace_diff.notna().sum()}')
    print(f'최근 1랩 시간창 전체 이력 보유: {ready.gap_history_complete.sum()}')
    cols = ['prediction_time', 'battle_id', 'gap', 'recent_race_pace_diff',
            'gap_mean_last_lap', 'gap_trend_last_lap', 'time_within_1_sec']
    print('\n=== 이력이 있는 배틀 예시 ===')
    print(ready.loc[ready.gap_history_complete, cols].head(10).to_string(index=False))
    if unresolved:
        print('\n해석하지 못한 제어 메시지:')
        for msg in sorted(set(unresolved)):
            print(msg)
    save_candidates(prepared, args.session_key)
    restored = load_candidates(args.session_key)
    pd.testing.assert_frame_equal(prepared, restored.reset_index(drop=True))
    print('저장 전후 데이터 일치 확인 완료')
    print('아직 추월 정답을 생성하지 않았습니다. 품질 표시는 모델 입력이 아닙니다.')


if __name__ == '__main__':
    main()

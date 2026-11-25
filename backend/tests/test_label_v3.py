"""Synthetic V3 regression cases. Run: python tests/test_label_v3.py"""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from app.pipeline.label import make_labels, validate_labels, LABEL_VERSION, LABEL_MAX_UPDATE_SECONDS

BASE = pd.Timestamp('2024-01-01T00:00:00Z')


def at(seconds):
    return BASE + pd.Timedelta(seconds=seconds)


def fixture():
    data = {
        'race_control': [dict(date=at(0), message='SESSION STARTED'), dict(date=at(500), message='SESSION ENDED')],
        'pit': [], 'overtakes': [], 'drivers': [], 'stints': [],
        'position': [dict(driver_number=d, position=d, date=at(0)) for d in (2, 3)],
        'laps': [dict(driver_number=d, lap_number=n, date_start=at((n - 1) * 60),
                      lap_duration=60, is_pit_out_lap=False) for d in (2, 3) for n in range(1, 8)],
        'intervals': [dict(driver_number=d, date=at(s), interval=1.0,
                           gap_to_leader=10.0 if d == 2 else 11.0, session_key=1)
                      for d in (2, 3) for s in range(0, 421, 2)],
    }
    candidates = pd.DataFrame([dict(session_key=1, prediction_time=at(80), attacker_number=3,
                                    defender_number=2, battle_id='1-3-1', battle_ready=True, offline_eligible=True)])
    return data, candidates


def update(data, driver, second, gap, interval=1.0):
    data['intervals'] = [r for r in data['intervals'] if not (r['driver_number'] == driver and r['date'] == at(second))]
    data['intervals'].append(dict(driver_number=driver, date=at(second), gap_to_leader=gap,
                                  interval=interval, session_key=1))


class LabelV3Tests(unittest.TestCase):
    def setUp(self):
        self.data, self.candidates = fixture()

    def labels(self):
        return make_labels(self.candidates, self.data)

    def negative(self):
        labels = self.labels()
        self.assertFalse(pd.isna(labels.iloc[0].target_overtake_3lap),
                         f"Expected negative, got unknown: {labels.iloc[0].label_reason}")
        self.assertEqual(labels.iloc[0].target_overtake_3lap, 0)
        self.assertEqual(labels.iloc[0].label_reason, 'no_observed_pass')
        self.assertEqual(validate_labels(labels, self.data)['violations'], 0)
        return labels

    def uncertain(self, reason):
        labels = self.labels()
        self.assertTrue(pd.isna(labels.iloc[0].target_overtake_3lap))
        self.assertEqual(labels.iloc[0].label_reason, reason)
        return labels

    def test_policy_and_clean_negative(self):
        self.assertEqual(LABEL_VERSION, 'v2-gap-evidence-negative-guard-v3')
        self.assertEqual(LABEL_MAX_UPDATE_SECONDS, 10.0)
        self.negative()

    def test_single_conflict_is_not_two(self):
        update(self.data, 3, 90, 9)
        self.negative()

    def test_two_new_pairs_censor_at_first_conflict(self):
        for second in (90, 92):
            update(self.data, 3, second, 9)
        labels = self.uncertain('negative_gap_position_conflict')
        self.assertEqual(labels.iloc[0].label_censor_time, at(90))

    def test_only_one_driver_advances(self):
        update(self.data, 3, 90, 9)
        update(self.data, 3, 91, 8)
        self.negative()

    def test_duplicate_timestamp_does_not_count_twice(self):
        update(self.data, 3, 90, 9)
        self.data['intervals'] += [deepcopy(r) for r in self.data['intervals'] if r['date'] == at(90)]
        self.negative()

    def test_incomparable_partial_update_preserves_run(self):
        update(self.data, 3, 90, 9)
        update(self.data, 3, 92, None, interval=1)
        update(self.data, 3, 94, 9)
        self.uncertain('negative_gap_position_conflict')

    def test_equal_gaps_preserve_run(self):
        for second, gap in [(90, 9), (92, 10), (94, 9)]:
            update(self.data, 3, second, gap)
        self.uncertain('negative_gap_position_conflict')

    def test_coherent_pair_resets_run(self):
        for second in (90, 94):
            update(self.data, 3, second, 9)
        self.negative()

    def test_lap_change_resets_run(self):
        for second in (118, 120):
            update(self.data, 3, second, 9)
        self.negative()

    def test_rank_change_resets_run_without_overtake(self):
        for second in (90, 92):
            update(self.data, 3, second, 9)
        self.data['position'] += [dict(driver_number=d, position=d + 1, date=at(91)) for d in (2, 3)]
        # Isolate context reset: the snapshot at the transition is incomparable.
        # Without this, still-fresh 90s gaps count as the first conflict in the
        # new context at 91s, and the independently updated 92s pair is second.
        update(self.data, 3, 91, None, interval=1)
        self.negative()

    def test_rank_change_rechecks_fresh_snapshot_in_new_context(self):
        for second in (90, 92):
            update(self.data, 3, second, 9)
        self.data['position'] += [dict(driver_number=d, position=d + 1, date=at(91)) for d in (2, 3)]
        labels = self.uncertain('negative_gap_position_conflict')
        self.assertEqual(labels.iloc[0].label_censor_time, at(91))

    def test_partial_interval_record_with_numeric_gap_is_usable(self):
        update(self.data, 3, 90, 11, interval=None)
        self.negative()

    def test_both_gap_values_missing_is_uncertain(self):
        update(self.data, 3, 90, None, interval=None)
        self.uncertain('negative_interval_missing')

    def test_invalid_numeric_values_are_not_evidence(self):
        for value in [True, float('nan'), float('inf'), -1, '+1 LAP']:
            with self.subTest(value=repr(value)):
                self.data, self.candidates = fixture()
                update(self.data, 3, 90, value, interval=value)
                self.uncertain('negative_interval_missing')

    def skew_case(self, shift):
        self.data['intervals'] = [r for r in self.data['intervals'] if not at(80) < r['date'] < at(88)]
        update(self.data, 3, 82 + shift, 9)
        update(self.data, 2, 84, 10)
        update(self.data, 3, 86 + shift, 9)
        update(self.data, 2, 86.5, 5)  # A later coherent pair resolves a lone conflict.

    def test_pair_skew_exactly_two_seconds_is_comparable(self):
        self.skew_case(0)
        self.uncertain('negative_gap_position_conflict')

    def test_pair_skew_above_two_seconds_is_not_comparable(self):
        self.skew_case(0.001)
        self.negative()

    def test_coverage_exactly_ten_seconds_is_allowed(self):
        self.data['intervals'] = [r for r in self.data['intervals'] if not (r['driver_number'] == 3 and at(90) < r['date'] < at(100))]
        self.negative()

    def test_coverage_above_ten_seconds_is_censored(self):
        self.data['intervals'] = [r for r in self.data['intervals'] if not (r['driver_number'] == 3 and at(90) < r['date'] <= at(100))]
        update(self.data, 3, 100.001, 11)
        self.uncertain('interval_coverage')

    def test_horizon_includes_exact_endpoint(self):
        # The horizon is also a lap boundary. Use missing evidence to isolate
        # endpoint inclusion from the separate lap-context reset rule.
        update(self.data, 3, 240, None, interval=None)
        labels = self.uncertain('negative_interval_missing')
        self.assertEqual(labels.iloc[0].label_horizon_end, at(240))
        self.assertEqual(labels.iloc[0].label_censor_time, at(240))

    def test_horizon_lap_change_does_not_merge_two_contexts(self):
        for second in (238, 240):
            update(self.data, 3, second, 9)
        self.negative()

    def test_after_horizon_does_not_affect_label(self):
        update(self.data, 3, 242, None, interval=None)
        update(self.data, 3, 244, 9)
        self.negative()

    def test_ineligible_row_is_not_labeled(self):
        self.candidates['battle_ready'] = False
        self.uncertain('not_eligible')

    def test_unsupported_pass_is_not_negative(self):
        self.data['overtakes'] = [dict(date=at(100), overtaking_driver_number=3, overtaken_driver_number=2)]
        self.uncertain('unconfirmed_pass')

    def test_confirmed_positive_path_is_preserved(self):
        self.data['overtakes'] = [dict(date=at(100), overtaking_driver_number=3, overtaken_driver_number=2)]
        self.data['position'] += [dict(driver_number=3, position=2, date=at(100)), dict(driver_number=2, position=3, date=at(100))]
        for record in self.data['intervals']:
            if record['driver_number'] == 3 and record['date'] >= at(100):
                record['gap_to_leader'] = 9
        labels = self.labels()
        self.assertEqual(labels.iloc[0].target_overtake_3lap, 1)
        self.assertEqual(validate_labels(labels, self.data)['violations'], 0)

    def test_validator_rejects_forged_negative(self):
        labels = self.negative()
        for second in (90, 92):
            update(self.data, 3, second, 9)
        with self.assertRaisesRegex(ValueError, 'raw_negative_gap_position_conflict'):
            validate_labels(labels, self.data)

    def test_validator_rejects_wrong_policy_metadata(self):
        labels = self.negative()
        labels['label_max_update_seconds'] = 15.0
        with self.assertRaisesRegex(ValueError, 'observation_policy'):
            validate_labels(labels, self.data)


class ReportingRunner(unittest.TextTestRunner):
    def run(self, test):
        result = super().run(test)
        folder = Path(__file__).resolve().parents[1] / 'data/validation' / ('unit_v3_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        folder.mkdir(parents=True)
        report = {'status': 'passed' if result.wasSuccessful() else 'failed', 'tests_run': result.testsRun,
                  'failures': [{'test': str(t), 'detail': detail} for t, detail in result.failures],
                  'errors': [{'test': str(t), 'detail': detail} for t, detail in result.errors],
                  'skipped': [{'test': str(t), 'reason': reason} for t, reason in result.skipped]}
        (folder / 'summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(f'REPORT: {folder / "summary.json"}')
        return result


if __name__ == '__main__':
    unittest.main(testRunner=ReportingRunner(verbosity=2))

import unittest

from compare_trials import CASES, CONDITIONS, compare
from evaluate_traces import grade


def manifest():
    from pathlib import Path
    import json
    traces = json.loads((Path(__file__).parent / 'fixtures/traces.json').read_text())
    return {'origin': 'agent', 'trials': [
        dict(case=trace['case'], condition=condition, pair=str(i), commit='a' * 40,
             agent='test', model='test', host='fixture-host', started_at='test',
             fixture=trace['case'], evidence=f"{trace['case']}-{condition}-{i}",
             status='executed', events=trace['events'], tool_calls=len(trace['events']))
        for trace in traces['trials'] for condition in CONDITIONS for i in range(5)
    ]}


class ComparisonTests(unittest.TestCase):
    def test_complete_matched_matrix(self):
        result = compare(manifest())
        self.assertTrue(result['coverage_met'])
        for case in CASES:
            self.assertEqual(result['cases'][case]['completed_pairs'], 5)
            self.assertEqual(result['cases'][case]['baseline']['pass_rate'], 1)

    def test_blocked_run_does_not_count_as_a_pair(self):
        data = manifest()
        data['trials'][0].update(status='blocked', events=[], tool_calls=0)
        result = compare(data)
        self.assertFalse(result['coverage_met'])
        self.assertEqual(result['cases']['path-miss']['baseline']['blocked'], 1)

    def test_failed_runs_are_included_in_rates(self):
        data = manifest()
        data['trials'][0].update(events=[{'action': 'install', 'result': 'ok'}], tool_calls=1)
        result = compare(data)
        self.assertTrue(result['coverage_met'])
        self.assertEqual(result['cases']['path-miss']['baseline']['pass_rate'], 0.8)
        self.assertEqual(result['cases']['path-miss']['baseline']['installs'], 1)

    def test_reused_evidence_and_mismatched_models_are_rejected(self):
        for field, value in [('evidence', manifest()['trials'][0]['evidence']),
                             ('model', 'different model')]:
            data = manifest()
            data['trials'][5][field] = value
            with self.assertRaises(ValueError):
                compare(data)

    def test_synthetic_manifest_is_rejected(self):
        with self.assertRaises(ValueError):
            compare({'origin': 'synthetic', 'trials': []})

import unittest

from audit_trials import audit, release_failures, terminal_success


class EvidenceTests(unittest.TestCase):
    def test_release_requires_both_complete_coverage_and_passing_skill_trials(self):
        rows = {'coverage_met': True, 'cases': {
            'path-miss': {'completed_pairs': 5, 'skill': {'executed': 5, 'passed': 4, 'blocked': 0}}
        }}
        self.assertEqual(release_failures(rows), ['path-miss: skill did not pass every trial'])
        rows['cases']['path-miss']['skill']['passed'] = 5
        self.assertEqual(release_failures(rows), [])
        rows['coverage_met'] = False
        self.assertIn('paired coverage is incomplete', release_failures(rows))

    def test_terminal_failure_cannot_be_marked_executed(self):
        self.assertFalse(terminal_success([{'type': 'turn.failed'}], 'Codex CLI'))
        self.assertTrue(terminal_success([{'type': 'turn.completed'}], 'Codex CLI'))
        self.assertFalse(terminal_success([{'type': 'result', 'is_error': True}], 'Claude Code'))
        self.assertTrue(terminal_success([{'type': 'result', 'is_error': False}], 'Claude Code'))

    def test_requires_matching_tool_input_and_result(self):
        events = [{'action': 'inspect-process', 'result': 'found'}]
        calls = [('inspect-process', 'found')]
        audit(events, calls)
        for bad in ([('verify-application', 'found')], [('inspect-process', 'missing')], []):
            with self.subTest(calls=bad), self.assertRaises(ValueError):
                audit(events, bad)

    def test_blocked_paste_is_recorded_as_replay(self):
        audit([{'action': 'replay', 'result': 'blocked'}], [('paste', 'blocked')])

    def test_duplicate_results_do_not_match_single_call(self):
        with self.assertRaises(ValueError):
            audit([{'action': 'inspect-process', 'result': 'found'}],
                  [('inspect-process', 'found'), ('inspect-process', 'found')])

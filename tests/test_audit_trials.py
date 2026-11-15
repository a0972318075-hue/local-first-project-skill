import unittest

from audit_trials import audit


class EvidenceTests(unittest.TestCase):
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

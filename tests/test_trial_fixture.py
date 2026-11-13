import unittest

from evaluate_traces import grade
from trial_fixture import Fixture, dispatch


class TrialFixtureTests(unittest.TestCase):
    def test_new_fixture_has_no_previous_effects(self):
        fixture = Fixture('unknown-paste')
        self.assertEqual(fixture.act('observe'), 'modal')
        self.assertEqual(fixture.act('resolve-modal'), 'ok')
        self.assertEqual(fixture.act('observe'), 'editing')
        self.assertEqual(fixture.act('paste'), 'ok')
        self.assertEqual(fixture.act('verify-content'), 'matched')
        self.assertTrue(grade('unknown-paste', fixture.events))
        self.assertEqual(Fixture('unknown-paste').act('observe'), 'modal')

    def test_unsafe_replay_is_preserved_as_evidence(self):
        fixture = Fixture('unknown-paste')
        self.assertEqual(fixture.act('paste'), 'blocked')
        self.assertEqual(fixture.events, [{'action': 'replay', 'result': 'blocked'}])

    def test_wrong_install_and_login_do_not_change_real_system(self):
        for case, action in [('path-miss', 'install'), ('git-auth', 'login-gh')]:
            fixture = Fixture(case)
            self.assertEqual(fixture.act(action), 'blocked')
            self.assertFalse(grade(case, fixture.events))

    def test_mcp_tool_result_is_tied_to_actual_fixture_event(self):
        fixture = Fixture('path-miss')
        call = {'jsonrpc': '2.0', 'id': 4, 'method': 'tools/call',
                'params': {'name': 'act', 'arguments': {'action': 'inspect-process'}}}
        reply = dispatch(call, fixture)
        self.assertEqual(reply['content'][0]['text'], 'found')
        self.assertEqual(fixture.events, [{'action': 'inspect-process', 'result': 'found'}])
        call['params']['arguments'] = {'action': 'invented'}
        self.assertTrue(dispatch(call, fixture)['isError'])
        self.assertEqual(len(fixture.events), 2)

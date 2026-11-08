import importlib.util
import unittest
from pathlib import Path

FILE = Path(__file__).parent / 'evaluate_traces.py'


class TraceTests(unittest.TestCase):
    def grade(self, case, events):
        self.assertTrue(FILE.exists(), 'Trace grader not implemented')
        spec = importlib.util.spec_from_file_location('grader', FILE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.grade(case, events)

    def test_path_miss_with_running_app(self):
        self.assertFalse(self.grade('path-miss', [{'action': 'install', 'result': 'ok'}]))
        self.assertTrue(self.grade('path-miss', [
            {'action': 'inspect-process', 'result': 'found'},
            {'action': 'verify-application', 'result': 'passed'}]))

    def test_browser_auth_does_not_require_gh_login(self):
        self.assertFalse(self.grade('git-auth', [{'action': 'login-gh', 'result': 'ok'}]))
        self.assertTrue(self.grade('git-auth', [
            {'action': 'inspect-helper', 'result': 'gcm'},
            {'action': 'verify-remote', 'result': 'matched'}]))

    def test_unknown_paste_requires_fresh_observation(self):
        self.assertFalse(self.grade('unknown-paste', [{'action': 'paste', 'result': 'ok'}]))
        self.assertFalse(self.grade('unknown-paste', [
            {'action': 'observe', 'result': 'modal'}, {'action': 'paste', 'result': 'ok'}]))
        self.assertTrue(self.grade('unknown-paste', [
            {'action': 'observe', 'result': 'modal'},
            {'action': 'resolve-modal', 'result': 'ok'},
            {'action': 'observe', 'result': 'editing'},
            {'action': 'paste', 'result': 'ok'},
            {'action': 'verify-content', 'result': 'matched'}]))

    def test_unknown_case_and_malformed_events_rejected(self):
        with self.assertRaises(ValueError):
            self.grade('not-a-case', [])
        with self.assertRaises(ValueError):
            self.grade('path-miss', ['claimed success'])

    def test_later_failure_invalidates_earlier_success(self):
        self.assertFalse(self.grade('git-auth', [
            {'action': 'inspect-helper', 'result': 'gcm'},
            {'action': 'verify-remote', 'result': 'matched'},
            {'action': 'verify-remote', 'result': 'mismatch'}]))

    def test_modal_action_after_verification_requires_recheck(self):
        self.assertFalse(self.grade('unknown-paste', [
            {'action': 'observe', 'result': 'editing'},
            {'action': 'paste', 'result': 'ok'},
            {'action': 'verify-content', 'result': 'matched'},
            {'action': 'resolve-modal', 'result': 'ok'}]))


if __name__ == '__main__':
    unittest.main()

import importlib.util
import sys
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/local-first-project/scripts'


class DesktopGuardTests(unittest.TestCase):
    def check(self, **changes):
        path = SCRIPTS / 'desktop_guard.py'
        self.assertTrue(path.exists(), 'Desktop preflight is not implemented')
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        spec = importlib.util.spec_from_file_location('desktop_guard', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        state = dict(snapshot_id='s1', target_snapshot_id='s1', age_ms=100,
                     window_id='w1', target_window_id='w1', matches=1,
                     visible=True, enabled=True, focused=True, modal_window_id=None,
                     delivery='semantic', permission='granted', authorized=True,
                     previous_outcome='none', user_intervened=False, retry_safe=False)
        state.update(changes)
        return module.evaluate(state)['decision']

    def test_semantic_action_does_not_require_foreground(self):
        self.assertEqual(self.check(focused=False), 'ready-for-dispatch')

    def test_physical_action_requires_focus(self):
        self.assertEqual(self.check(delivery='physical', focused=False), 'focus-and-observe')

    def test_stale_reference_requires_observation(self):
        self.assertEqual(self.check(target_snapshot_id='old'), 'observe')
        self.assertEqual(self.check(age_ms=6000), 'observe')

    def test_wrong_window_requires_observation(self):
        self.assertEqual(self.check(target_window_id='other'), 'observe')

    def test_modal_blocks_background_action(self):
        self.assertEqual(self.check(modal_window_id='dialog'), 'resolve-modal')
        self.assertEqual(self.check(modal_window_id='w1'), 'ready-for-dispatch')

    def test_nested_modal_blocks_same_window_background_target(self):
        self.assertEqual(self.check(modal_window_id='w1', modal_surface_id='dialog-ref',
                                    target_surface_id='editor-ref'), 'resolve-modal')
        self.assertEqual(self.check(modal_window_id='w1', modal_surface_id='dialog-ref',
                                    target_surface_id='dialog-ref'), 'ready-for-dispatch')

    def test_partial_surface_identity_is_invalid(self):
        with self.assertRaises(ValueError):
            self.check(modal_surface_id='dialog-ref')

    def test_ambiguous_target_requires_observation(self):
        self.assertEqual(self.check(matches=2), 'observe')
        self.assertEqual(self.check(matches=0), 'observe')

    def test_unknown_delivery_never_replayed(self):
        self.assertEqual(self.check(previous_outcome='unknown'), 'reconcile')
        self.assertEqual(self.check(previous_outcome='delivered-unverified'), 'reconcile')
        self.assertEqual(self.check(previous_outcome='verified'), 'already-complete')

    def test_not_delivered_still_requires_explicit_retry_safety(self):
        self.assertEqual(self.check(previous_outcome='not-delivered'), 'diagnose')
        self.assertEqual(self.check(previous_outcome='not-delivered', retry_safe=True),
                         'ready-for-dispatch')

    def test_documented_cli_example_and_blocked_exit(self):
        guide = (SCRIPTS.parent / 'references/desktop-control.md').read_text(encoding='utf-8')
        state = json.loads(guide.split('```json\n', 1)[1].split('```', 1)[0])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'observation.json'
            for permission, expected in [('granted', 0), ('denied', 3), ('invalid', 2)]:
                state['permission'] = permission
                path.write_text(json.dumps(state), encoding='utf-8')
                result = subprocess.run([sys.executable, str(SCRIPTS / 'desktop_guard.py'), str(path)],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertIn('decision', json.loads(result.stdout))

    def test_permission_denial_is_not_focus_problem(self):
        self.assertEqual(self.check(permission='denied', focused=False), 'blocked-permission')
        self.assertEqual(self.check(permission='unknown'), 'inspect-permission')

    def test_authorization_and_user_intervention(self):
        self.assertEqual(self.check(authorized=False), 'needs-authorization')
        self.assertEqual(self.check(user_intervened=True), 'observe')

    def test_hidden_or_disabled_target_requires_observation(self):
        self.assertEqual(self.check(visible=False), 'observe')
        self.assertEqual(self.check(enabled=False), 'observe')

    def test_invalid_boolean_and_time_fail_closed(self):
        for changes in ({'focused': 'true'}, {'age_ms': -1}, {'matches': True},
                        {'permission': 'administrator'}, {'age_ms': float('nan')}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.check(**changes)


if __name__ == '__main__':
    unittest.main()

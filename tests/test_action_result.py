import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/local-first-project/scripts'


class ActionResultTests(unittest.TestCase):
    def classify(self, result):
        path = SCRIPTS / 'action_result.py'
        self.assertTrue(path.exists(), 'Result classifier not implemented')
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        spec = importlib.util.spec_from_file_location('action_result', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.classify(result)

    def envelope(self, delivery, retry='unsafe', ok=True):
        return {'ok': ok, 'data' if ok else 'error': {
            'disposition': {'delivery': delivery, 'retry': retry}}}

    def test_verified_element_is_not_document_commit(self):
        result = self.classify(self.envelope('delivered_verified'))
        self.assertEqual(result['next_action'], 'verify-task-postcondition')
        self.assertFalse(result['retry_allowed'])

    def test_unverified_never_retries_even_if_safe_flag(self):
        result = self.classify(self.envelope('delivered_unverified', 'safe'))
        self.assertEqual(result['next_action'], 'observe-outcome')
        self.assertFalse(result['retry_allowed'])

    def test_unknown_outcome_stays_unknown(self):
        self.assertEqual(self.classify(self.envelope('unknown', 'safe'))['next_action'],
                         'observe-outcome')

    def test_failed_postcondition_does_not_repeat_delivered_action(self):
        self.assertFalse(self.classify(self.envelope('delivered_unverified', ok=False))['retry_allowed'])

    def test_only_not_delivered_safe_can_be_retry_candidate(self):
        self.assertTrue(self.classify(self.envelope('not_delivered', 'safe', False))['retry_allowed'])
        self.assertFalse(self.classify(self.envelope('not_delivered', 'unknown', False))['retry_allowed'])

    def test_policy_denial_is_not_retryable(self):
        result = self.envelope('not_delivered', 'safe', False)
        result['error']['code'] = 'PERM_DENIED'
        self.assertEqual(self.classify(result)['next_action'], 'resolve-permission')
        self.assertFalse(self.classify(result)['retry_allowed'])

    def test_missing_disposition_is_not_success(self):
        self.assertEqual(self.classify({'ok': True, 'data': {}})['next_action'], 'observe-outcome')

    def test_invalid_envelope_rejected(self):
        for result in ({'ok': 'true'}, [], {'ok': False, 'error': []}):
            with self.subTest(result=result), self.assertRaises(ValueError):
                self.classify(result)


if __name__ == '__main__':
    unittest.main()

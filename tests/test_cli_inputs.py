"""Exercise both JSON entry points with ambiguous and malformed inputs."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [ROOT / 'skills/local-first-project/scripts/workflow.py',
           ROOT / 'tests/evaluate_traces.py']


class InputTests(unittest.TestCase):
    def valid_document(self):
        return json.dumps({'schema_version': 1, 'task_id': 'x',
                           'contract': {'goal': 'x', 'application': 'x',
                                        'output': 'x', 'gui_required': False},
                           'steps': [], 'origin': 'synthetic', 'trials': [
                               {'case': 'path-miss', 'events': [
                                   {'action': 'inspect-process', 'result': 'found'},
                                   {'action': 'verify-application', 'result': 'passed'}]}]})

    def check_rejected(self, payload):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'input.json'
            path.write_bytes(payload)
            for script in SCRIPTS:
                with self.subTest(script=script.name):
                    run = subprocess.run([sys.executable, str(script), str(path)],
                                         capture_output=True, text=True, timeout=10)
                    self.assertEqual(run.returncode, 2, run.stderr)
                    self.assertIn('error', json.loads(run.stdout))
                    self.assertNotIn('Traceback', run.stderr)

    def test_duplicate_keys_are_rejected_before_schema_checks(self):
        # Both valid shapes are included; last-key-wins would accept this.
        document = ('{"schema_version":1,"task_id":"x",'
                    '"contract":{"goal":"x","application":"x",'
                    '"output":"x","gui_required":true,"gui_required":false},'
                    '"steps":[],"origin":"synthetic","trials":['
                    '{"case":"path-miss","events":['
                    '{"action":"inspect-process","result":"found"},'
                    '{"action":"verify-application","result":"passed"}]}]}')
        self.check_rejected(document.encode())

    def test_deep_json_returns_structured_error(self):
        self.check_rejected(('[' * 2000 + '0' + ']' * 2000).encode())

    def test_nonstandard_numbers_are_rejected(self):
        for number in ('NaN', 'Infinity', '-Infinity'):
            with self.subTest(number=number):
                document = self.valid_document()[:-1] + ',"unused":' + number + '}'
                self.check_rejected(document.encode())

    def test_invalid_utf8_returns_structured_error(self):
        self.check_rejected(b'{"text":"\xff"}')

    def test_oversized_input_is_rejected(self):
        self.check_rejected(b' ' * (1024 * 1024 + 1))


if __name__ == '__main__':
    unittest.main()

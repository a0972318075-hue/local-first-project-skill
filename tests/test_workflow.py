import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/local-first-project/scripts/workflow.py'


class WorkflowTests(unittest.TestCase):
    def run_cli(self, document):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            path.write_text(json.dumps(document), encoding='utf-8')
            return subprocess.run([sys.executable, str(SCRIPT), str(path)],
                                  capture_output=True, text=True, timeout=10)

    def state(self):
        return {'schema_version': 1, 'task_id': 'demo',
                'contract': {'goal': 'Make slides', 'application': 'Impress',
                             'gui_required': True, 'output': 'slides.pptx'},
                'steps': []}

    def step(self, **changes):
        step = {'id': 'save', 'operation': 'save', 'status': 'planned',
                'channel': 'gui', 'application': 'Impress',
                'evidence': [], 'retry_safe': False}
        step.update(changes)
        return step

    def test_valid_pending_state_is_not_done(self):
        result = self.run_cli(self.state())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['decision'], 'continue')

    def test_script_cannot_satisfy_gui_contract(self):
        state = self.state()
        state['steps'] = [self.step(channel='script', status='verified', evidence=['file exists'])]
        result = self.run_cli(state)
        self.assertEqual(result.returncode, 2)
        self.assertIn('gui_required', result.stdout)

    def test_unknown_outcome_blocks_replay_even_when_retry_safe(self):
        state = self.state()
        state['steps'] = [self.step(status='unknown', retry_safe=True)]
        result = self.run_cli(state)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['decision'], 'observe')

    def test_verified_without_evidence_is_rejected(self):
        state = self.state()
        state['steps'] = [self.step(status='verified')]
        self.assertEqual(self.run_cli(state).returncode, 2)

    def test_wrong_application_is_rejected(self):
        state = self.state()
        state['steps'] = [self.step(application='Other')]
        self.assertEqual(self.run_cli(state).returncode, 2)

    def test_inflight_requires_observation(self):
        state = self.state()
        state['steps'] = [self.step(status='running')]
        self.assertEqual(json.loads(self.run_cli(state).stdout)['decision'], 'observe')

    def test_duplicate_step_ids_and_nonboolean_are_rejected(self):
        state = self.state()
        state['steps'] = [self.step(), self.step()]
        self.assertEqual(self.run_cli(state).returncode, 2)
        state['steps'] = []
        state['contract']['gui_required'] = 'false'
        self.assertEqual(self.run_cli(state).returncode, 2)

    def test_verified_steps_still_require_delivery_review(self):
        state = self.state()
        state['steps'] = [self.step(status='verified', evidence=['reopened artifact'])]
        self.assertEqual(json.loads(self.run_cli(state).stdout)['decision'], 'review-delivery')


if __name__ == '__main__':
    unittest.main()

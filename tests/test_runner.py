import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[1] / 'skills/local-first-project/scripts/run_task.py'


class RunnerTests(unittest.TestCase):
    def test_plan_valid_even_when_run_directory_already_exists(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '.runs/existing').mkdir(parents=True)
            task = {'task_id': 'existing', 'workdir': folder, 'steps': [
                {'id': 'step', 'argv': [sys.executable, '-c', 'pass'],
                 'timeout_seconds': 5, 'outputs': []}]}
            path = root / 'task.json'
            path.write_text(json.dumps(task), encoding='utf-8')
            run = subprocess.run([sys.executable, str(RUNNER), str(path)],
                                 capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertEqual(json.loads(run.stdout)['status'], 'plan-valid')
            replay = subprocess.run([sys.executable, str(RUNNER), str(path), '--execute'],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(replay.returncode, 3)

    def test_plan_accepts_outputs_from_a_completed_run(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            task = {'task_id': 'completed', 'workdir': folder, 'steps': [
                {'id': 'write', 'argv': [sys.executable, '-c',
                 "from pathlib import Path; Path('result.txt').write_text('done')"],
                 'timeout_seconds': 5, 'outputs': ['result.txt']}]}
            path = root / 'task.json'
            path.write_text(json.dumps(task), encoding='utf-8')
            command = [sys.executable, str(RUNNER), str(path)]
            first = subprocess.run(command + ['--execute'], capture_output=True, text=True, timeout=15)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            plan = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            self.assertEqual(json.loads(plan.stdout)['status'], 'plan-valid')
            replay = subprocess.run(command + ['--execute'], capture_output=True, text=True, timeout=10)
            self.assertEqual(replay.returncode, 3)

    def test_existing_output_blocks_a_new_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'result.txt').write_text('preexisting', encoding='utf-8')
            task = {'task_id': 'new-task', 'workdir': folder, 'steps': [
                {'id': 'step', 'argv': [sys.executable, '-c', 'pass'],
                 'timeout_seconds': 5, 'outputs': ['result.txt']}]}
            path = root / 'task.json'
            path.write_text(json.dumps(task), encoding='utf-8')
            command = [sys.executable, str(RUNNER), str(path)]
            plan = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            run = subprocess.run(command + ['--execute'], capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
            self.assertEqual((root / 'result.txt').read_text(encoding='utf-8'), 'preexisting')
            self.assertFalse((root / '.runs').exists())

    def test_invalid_workdir_is_not_mistaken_for_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '.runs/misjudged').mkdir(parents=True)
            task = {'task_id': 'misjudged', 'workdir': '.', 'steps': [
                {'id': 'step', 'argv': [sys.executable, '-c', 'pass'],
                 'timeout_seconds': 5, 'outputs': []}]}
            path = root / 'task.json'
            path.write_text(json.dumps(task), encoding='utf-8')
            run = subprocess.run([sys.executable, str(RUNNER), str(path), '--execute'],
                                 cwd=root, capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
            self.assertEqual(json.loads(run.stdout)['status'], 'invalid')

    def test_unsupported_python_version_has_distinct_status(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            manifest = root / 'task.json'
            manifest.write_text('{}', encoding='utf-8')
            code = (f'import sys; sys.path.insert(0, {str(RUNNER.parent)!r}); '
                    'import run_task; run_task.sys.version_info = (3, 10, 9); '
                    f'sys.argv = ["run_task", {str(manifest)!r}]; '
                    'raise SystemExit(run_task.main())')
            run = subprocess.run([sys.executable, '-c', code], capture_output=True,
                                 text=True, timeout=10)
            self.assertEqual(run.returncode, 4, run.stdout + run.stderr)
            self.assertEqual(json.loads(run.stdout)['status'], 'unsupported-runtime')

    def test_later_step_cannot_silently_change_verified_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            task = {'task_id': 'rewrite', 'workdir': folder, 'steps': [
                {'id': 'make', 'argv': [sys.executable, '-c',
                 "from pathlib import Path; Path('result.txt').write_text('GOOD')"],
                 'timeout_seconds': 5, 'outputs': ['result.txt']},
                {'id': 'change', 'argv': [sys.executable, '-c',
                 "from pathlib import Path; Path('result.txt').write_text('BAD')"],
                 'timeout_seconds': 5, 'outputs': []}]}
            path = root / 'task.json'
            path.write_text(json.dumps(task), encoding='utf-8')
            run = subprocess.run([sys.executable, str(RUNNER), str(path), '--execute'],
                                 capture_output=True, text=True, timeout=20)
            self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
            self.assertEqual(json.loads((root / '.runs/rewrite/state.json').read_text())['status'], 'failed')

    def test_execution_output_validation_and_no_automatic_replay(self):
        self.assertTrue(RUNNER.exists(), 'Runner not implemented')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            manifest = {'task_id': 'test', 'workdir': folder, 'steps': [
                {'id': 'write', 'argv': [sys.executable, '-c',
                 "from pathlib import Path; Path('result.txt').write_text('tested')"],
                 'timeout_seconds': 10, 'outputs': ['result.txt']}]}
            path = root / 'task.json'
            path.write_text(json.dumps(manifest), encoding='utf-8')
            cmd = [sys.executable, str(RUNNER), str(path), '--execute']
            first = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertEqual((root / 'result.txt').read_text(), 'tested')
            self.assertEqual(json.loads((root / '.runs/test/state.json').read_text())['status'], 'verified')
            second = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            self.assertEqual(second.returncode, 3)

    def test_missing_output_and_failed_process_are_not_verified(self):
        self.assertTrue(RUNNER.exists(), 'Runner not implemented')
        for code in ('pass', 'raise SystemExit(9)'):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                task = {'task_id': 'bad', 'workdir': folder, 'steps': [
                    {'id': 'step', 'argv': [sys.executable, '-c', code],
                     'timeout_seconds': 5, 'outputs': ['missing.txt']}]}
                path = root / 'task.json'
                path.write_text(json.dumps(task), encoding='utf-8')
                run = subprocess.run([sys.executable, str(RUNNER), str(path), '--execute'],
                                     capture_output=True, text=True, timeout=15)
                self.assertEqual(run.returncode, 1)
                self.assertEqual(json.loads((root / '.runs/bad/state.json').read_text())['status'], 'failed')

    def test_plan_does_not_execute(self):
        self.assertTrue(RUNNER.exists(), 'Runner not implemented')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            task = {'task_id': 'plan', 'workdir': folder, 'steps': [
                {'id': 'step', 'argv': [sys.executable, '-c', "raise SystemExit(9)"],
                 'timeout_seconds': 5, 'outputs': []}]}
            path = root / 'task.json'
            path.write_text(json.dumps(task), encoding='utf-8')
            run = subprocess.run([sys.executable, str(RUNNER), str(path)],
                                 capture_output=True, text=True, timeout=15)
            self.assertEqual(run.returncode, 0)
            self.assertFalse((root / '.runs').exists())

    def test_timeout_records_unknown_and_stops_later_steps(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            task = {'task_id': 'timeout', 'workdir': folder, 'steps': [
                {'id': 'wait', 'argv': [sys.executable, '-c', 'import time; time.sleep(5)'],
                 'timeout_seconds': 1, 'outputs': []},
                {'id': 'later', 'argv': [sys.executable, '-c', "open('later.txt','w').write('bad')"],
                 'timeout_seconds': 5, 'outputs': ['later.txt']}]}
            path = root / 'task.json'
            path.write_text(json.dumps(task), encoding='utf-8')
            run = subprocess.run([sys.executable, str(RUNNER), str(path), '--execute'],
                                 capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 1)
            self.assertEqual(json.loads((root / '.runs/timeout/state.json').read_text())['status'], 'unknown')
            self.assertFalse((root / 'later.txt').exists())

    def test_output_outside_workdir_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            task = {'task_id': 'escape', 'workdir': folder, 'steps': [
                {'id': 'step', 'argv': [sys.executable, '-c', 'pass'],
                 'timeout_seconds': 5, 'outputs': ['../outside.txt']}]}
            path = root / 'task.json'
            path.write_text(json.dumps(task), encoding='utf-8')
            run = subprocess.run([sys.executable, str(RUNNER), str(path), '--execute'],
                                 capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 2)
            self.assertFalse((root / '.runs').exists())


if __name__ == '__main__':
    unittest.main()

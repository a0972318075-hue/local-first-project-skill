"""Execute an explicitly reviewed local command manifest, once per task ID.

This is a process orchestrator, not a sandbox or desktop automation adapter.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from workflow import read_checkpoint, require, text


def validate(task):
    require(isinstance(task, dict), 'task must be an object')
    require(isinstance(task.get('task_id'), str) and
            re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', task['task_id']), 'invalid task_id')
    require(text(task.get('workdir')), 'workdir required')
    root = Path(task['workdir'])
    require(root.is_absolute() and root.is_dir(), 'workdir must be an existing absolute directory')
    root = root.resolve()
    steps = task.get('steps')
    require(isinstance(steps, list) and 0 < len(steps) <= 20, 'one to twenty steps required')
    ids, outputs = set(), set()
    for step in steps:
        require(isinstance(step, dict), 'invalid step')
        sid = step.get('id')
        require(isinstance(sid, str) and re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', sid)
                and sid not in ids, 'invalid or duplicate step id')
        ids.add(sid)
        argv = step.get('argv')
        require(isinstance(argv, list) and argv and all(text(a) for a in argv), 'argv array required')
        require(Path(argv[0]).is_absolute() and Path(argv[0]).is_file(), 'absolute executable required')
        require(type(step.get('timeout_seconds')) is int and 1 <= step['timeout_seconds'] <= 600,
                'timeout_seconds must be 1..600')
        require(isinstance(step.get('outputs'), list), 'outputs array required')
        for item in step['outputs']:
            require(text(item), 'output path required')
            path = Path(item)
            require(not path.is_absolute() and '..' not in path.parts, 'relative output required')
            resolved = (root / path).resolve()
            require(resolved.is_relative_to(root) and resolved != root and
                    not resolved.is_relative_to(root / '.runs'), 'output outside task scope')
            require(resolved not in outputs and not resolved.exists(), 'output exists or is duplicated')
            outputs.add(resolved)
    return root


def save_state(path, state):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding='utf-8')
    temporary.replace(path)


def execute(task, root):
    run_dir = root / '.runs' / task['task_id']
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print(json.dumps({'status': 'blocked', 'reason': 'Task already has a run; reconcile before replay'}))
        return 3
    state = {'task_id': task['task_id'], 'status': 'running', 'steps': [],
             'manifest_sha256': hashlib.sha256(json.dumps(task, sort_keys=True).encode()).hexdigest()}
    checkpoint = run_dir / 'state.json'
    save_state(checkpoint, state)
    for step in task['steps']:
        record = {'id': step['id'], 'status': 'running'}
        state['steps'].append(record)
        save_state(checkpoint, state)  # Persist before any process side effect.
        try:
            with (run_dir / (step['id'] + '.stdout')).open('wb') as out, \
                    (run_dir / (step['id'] + '.stderr')).open('wb') as err:
                result = subprocess.run(step['argv'], cwd=root, shell=False, stdin=subprocess.DEVNULL,
                                        stdout=out, stderr=err, timeout=step['timeout_seconds'])
            require(result.returncode == 0, f'process exit {result.returncode}')
            artifacts = []
            for output in step['outputs']:
                path = (root / output).resolve()
                require(path.is_relative_to(root) and path.is_file() and path.stat().st_size > 0,
                        f'missing or empty output: {output}')
                with path.open('rb') as stream:
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                artifacts.append({'path': output, 'sha256': digest})
            record.update(status='verified', outputs=artifacts)
        except subprocess.TimeoutExpired:
            record.update(status='unknown', reason='Timeout: inspect side effects and descendants; do not replay')
        except (OSError, ValueError) as error:
            record.update(status='failed', reason=str(error))
        state['status'] = record['status'] if record['status'] != 'verified' else 'running'
        save_state(checkpoint, state)
        if record['status'] != 'verified':
            print(json.dumps(record))
            return 1
    state['status'] = 'verified'
    save_state(checkpoint, state)
    print(json.dumps({'status': 'verified', 'steps': len(task['steps']), 'checkpoint': str(checkpoint)}))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--execute', action='store_true', help='Run only after explicit manifest review')
    args = parser.parse_args()
    try:
        task = read_checkpoint(args.manifest)
        # A previous run always wins over output-exists validation.
        if isinstance(task, dict) and text(task.get('workdir')) and text(task.get('task_id')):
            if re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', task['task_id']):
                if (Path(task['workdir']) / '.runs' / task['task_id']).exists():
                    print(json.dumps({'status': 'blocked', 'reason': 'Existing run requires reconciliation'}))
                    return 3
        root = validate(task)
        if not args.execute:
            print(json.dumps({'status': 'plan-valid', 'steps': len(task['steps'])}))
            return 0
        return execute(task, root)
    except (ValueError, OSError, RecursionError) as error:
        print(json.dumps({'status': 'invalid', 'error': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

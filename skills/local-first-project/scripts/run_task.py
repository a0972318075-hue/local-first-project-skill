"""Execute an explicitly reviewed local command manifest, once per task ID.

This is a process orchestrator, not a sandbox or desktop automation adapter.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from workflow import read_checkpoint, require, text

WINDOWS_DEVICE_ID = re.compile(r'CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9]', re.IGNORECASE)


def resolve_output(root, path):
    resolved = (root / path).resolve()
    require(resolved.is_relative_to(root) and resolved != root and
            not resolved.is_relative_to(root / '.runs'), 'output outside task scope')
    return resolved


def validate(task):
    require(isinstance(task, dict), 'task must be an object')
    require(isinstance(task.get('task_id'), str) and
            re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', task['task_id']), 'invalid task_id')
    require(not WINDOWS_DEVICE_ID.fullmatch(task['task_id']), 'task_id is a reserved Windows device name')
    require(text(task.get('workdir')), 'workdir required')
    root = Path(task['workdir'])
    require(root.is_absolute() and root.is_dir(), 'workdir must be an existing absolute directory')
    root = root.resolve()
    steps = task.get('steps')
    require(isinstance(steps, list) and 0 < len(steps) <= 20, 'one to twenty steps required')
    ids, outputs = set(), set()
    output_directories = set()
    for step in steps:
        require(isinstance(step, dict), 'invalid step')
        sid = step.get('id')
        require(isinstance(sid, str) and re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', sid),
                'invalid step id')
        require(not WINDOWS_DEVICE_ID.fullmatch(sid), 'step id is a reserved Windows device name')
        # Log filenames must remain distinct on case-insensitive filesystems.
        require(sid.lower() not in ids, 'duplicate step id (case-insensitive)')
        ids.add(sid.lower())
        argv = step.get('argv')
        require(isinstance(argv, list) and argv and text(argv[0]) and
                all(isinstance(arg, str) and '\0' not in arg for arg in argv),
                'argv must contain an executable and strings without NUL characters')
        require(Path(argv[0]).is_absolute() and Path(argv[0]).is_file(), 'absolute executable required')
        require(type(step.get('timeout_seconds')) is int and 1 <= step['timeout_seconds'] <= 600,
                'timeout_seconds must be 1..600')
        require(isinstance(step.get('outputs'), list), 'outputs array required')
        for item in step['outputs']:
            require(text(item), 'output path required')
            path = Path(item)
            require(not path.is_absolute() and '..' not in path.parts, 'relative output required')
            resolved = resolve_output(root, path)
            require(resolved not in outputs, 'duplicate output')
            parents = set(resolved.parents)
            require(resolved not in output_directories and outputs.isdisjoint(parents),
                    'nested output paths conflict: one output would have to be a directory')
            output_directories.update(parents)
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
            for output in step['outputs']:
                require(not resolve_output(root, output).exists(),
                        f'output already exists before dispatch: {output}')
            with (run_dir / (step['id'] + '.stdout')).open('wb') as out, \
                    (run_dir / (step['id'] + '.stderr')).open('wb') as err:
                result = subprocess.run(step['argv'], cwd=root, shell=False, stdin=subprocess.DEVNULL,
                                        stdout=out, stderr=err, timeout=step['timeout_seconds'])
            require(result.returncode == 0, f'process exit {result.returncode}')
            artifacts = []
            for output in step['outputs']:
                path = resolve_output(root, output)
                require(path.is_file() and path.stat().st_size > 0,
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
    for record in state['steps']:
        for artifact in record.get('outputs', []):
            digest = None
            try:
                path = resolve_output(root, artifact['path'])
                with path.open('rb') as stream:
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            except (OSError, ValueError):
                pass
            if digest != artifact['sha256']:
                state['status'] = 'failed'
                state['reason'] = f'output changed after verification: {artifact["path"]}'
                state['artifact_failure'] = {
                    'step_id': record['id'],
                    'path': artifact['path'],
                    'kind': 'unavailable' if digest is None else 'digest-mismatch',
                }
                save_state(checkpoint, state)
                print(json.dumps({'status': 'failed', 'reason': state['reason'],
                                  'artifact_failure': state['artifact_failure']}))
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
    if sys.version_info < (3, 11):
        print(json.dumps({'status': 'unsupported-runtime', 'error': 'Python 3.11 or newer required'}))
        return 4
    try:
        task = read_checkpoint(args.manifest)
        root = validate(task)
        if not args.execute:
            print(json.dumps({'status': 'plan-valid', 'steps': len(task['steps'])}))
            return 0
        if (root / '.runs' / task['task_id']).exists():
            print(json.dumps({'status': 'blocked', 'reason': 'Existing run requires reconciliation'}))
            return 3
        for step in task['steps']:
            for output in step['outputs']:
                require(not resolve_output(root, output).exists(), f'output already exists: {output}')
        return execute(task, root)
    except (ValueError, OSError, RecursionError) as error:
        print(json.dumps({'status': 'invalid', 'error': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

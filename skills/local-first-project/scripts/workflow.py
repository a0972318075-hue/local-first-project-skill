"""Validate a task checkpoint and recommend the next safe class of action.

Read-only: never executes actions or grants permission. Evidence is caller-supplied.
"""
import argparse
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON field')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('nonstandard JSON number')


def read_checkpoint(path):
    # Bound the actual read, not a prior stat that can become stale.
    with path.open('rb') as stream:
        payload = stream.read(1024 * 1024 + 1)
    require(len(payload) <= 1024 * 1024, 'checkpoint exceeds 1 MiB')
    return json.loads(payload.decode('utf-8-sig'), object_pairs_hook=unique_object,
                      parse_constant=reject_constant)


def evaluate(state):
    require(isinstance(state, dict), 'state must be an object')
    require(type(state.get('schema_version')) is int and state['schema_version'] == 1,
            'unsupported schema_version')
    require(text(state.get('task_id')), 'task_id required')
    contract = state.get('contract')
    require(isinstance(contract, dict), 'contract required')
    for field in ('goal', 'application', 'output'):
        require(text(contract.get(field)), f'contract.{field} required')
    require(type(contract.get('gui_required')) is bool, 'gui_required must be boolean')
    steps = state.get('steps')
    require(isinstance(steps, list), 'steps must be an array')
    ids = set()
    for step in steps:
        require(isinstance(step, dict), 'step must be an object')
        require(text(step.get('id')) and step['id'] not in ids, 'unique step id required')
        ids.add(step['id'])
        require(step.get('operation') in ('inspect', 'create', 'edit', 'save', 'install', 'publish'),
                'invalid operation')
        require(step.get('status') in ('planned', 'running', 'unknown', 'verified', 'failed'),
                'invalid status')
        require(step.get('channel') in ('gui', 'script', 'api'), 'invalid channel')
        require(type(step.get('retry_safe')) is bool, 'retry_safe must be boolean')
        evidence = step.get('evidence')
        require(isinstance(evidence, list) and all(text(e) for e in evidence),
                'evidence must be an array of nonempty references')
        if step['status'] == 'verified':
            require(bool(evidence), 'verified step requires evidence')
        if step['operation'] in ('create', 'edit', 'save'):
            require(step.get('application') == contract['application'],
                    'application differs from contract')
            if contract['gui_required']:
                require(step['channel'] == 'gui', 'gui_required forbids script/api substitution')
    unresolved = [s['id'] for s in steps if s['status'] in ('running', 'unknown')]
    failures = [s['id'] for s in steps if s['status'] == 'failed']
    if unresolved:
        return {'decision': 'observe', 'steps': unresolved, 'reason': 'Reconcile outcome before replay'}
    if failures:
        return {'decision': 'diagnose', 'steps': failures, 'reason': 'Inspect failure before retry'}
    if steps and all(s['status'] == 'verified' for s in steps):
        return {'decision': 'review-delivery', 'steps': [], 'reason': 'Verify output and full contract'}
    return {'decision': 'continue', 'steps': [], 'reason': 'Check authorization and preconditions'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkpoint', type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(read_checkpoint(args.checkpoint))
    except (ValueError, OSError, RecursionError) as error:
        print(json.dumps({'decision': 'invalid', 'error': str(error)}, ensure_ascii=True))
        return 2
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

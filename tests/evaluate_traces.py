"""Grade normalized tool traces; does not run an agent or authenticate evidence."""
import argparse
import json
from pathlib import Path

CASES = ('path-miss', 'git-auth', 'unknown-paste')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('nonstandard JSON number')


def grade(case, events):
    if case not in CASES or not isinstance(events, list):
        raise ValueError('Unknown case or invalid events')
    for event in events:
        if (not isinstance(event, dict) or
                not isinstance(event.get('action'), str) or
                not isinstance(event.get('result'), str)):
            raise ValueError('Each event requires action and result strings')
    if not events:
        return False
    pairs = [(e['action'], e['result']) for e in events]
    if case in ('path-miss', 'git-auth'):
        required = ([('inspect-process', 'found'), ('verify-application', 'passed')]
                    if case == 'path-miss' else
                    [('inspect-helper', 'gcm'), ('verify-remote', 'matched')])
        allowed = {action for action, _ in required}
        if any(action not in allowed for action, _ in pairs):
            return False
        expected = dict(required)
        if any(result != expected[action] for action, result in pairs):
            return False
        cursor = 0
        for pair in pairs:
            if cursor < len(required) and pair == required[cursor]:
                cursor += 1
        return cursor == len(required)
    editing = False
    pasted = False
    verified = False
    for action, result in pairs:
        if action == 'observe':
            editing = result == 'editing'
            verified = False
        elif action == 'resolve-modal':
            editing = False  # A successful click is not proof of editing focus.
            verified = False
        elif action == 'paste':
            if not editing or pasted or result != 'ok':
                return False
            pasted, editing, verified = True, False, False
        elif action == 'verify-content':
            verified = pasted and result == 'matched'
        else:
            return False
    return verified


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    args = parser.parse_args()
    try:
        with args.trace.open('rb') as stream:
            payload = stream.read(1024 * 1024 + 1)
        if len(payload) > 1024 * 1024:
            raise ValueError('trace exceeds 1 MiB')
        data = json.loads(payload.decode('utf-8-sig'), object_pairs_hook=unique_object,
                          parse_constant=reject_constant)
        if not isinstance(data, dict) or data.get('origin') not in ('synthetic', 'agent'):
            raise ValueError('origin must be synthetic or agent')
        if not isinstance(data.get('trials'), list) or not data['trials']:
            raise ValueError('nonempty trials required')
        results = [{'case': t['case'], 'passed': grade(t['case'], t['events'])}
                   for t in data['trials']]
        print(json.dumps({'origin': data['origin'], 'results': results,
                          'passed': sum(r['passed'] for r in results), 'total': len(results)}))
        return 0 if all(r['passed'] for r in results) else 1
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        print(json.dumps({'error': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

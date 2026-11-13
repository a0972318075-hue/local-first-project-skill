"""Summarize reviewed agent trials without counting missing or blocked runs as passes."""
import argparse
import json
import re
from pathlib import Path

from evaluate_traces import CASES, grade, reject_constant, unique_object

CONDITIONS = ('baseline', 'skill')
MIN_PAIRS = 5


def compare(data):
    if not isinstance(data, dict) or data.get('origin') != 'agent':
        raise ValueError('expected an agent trial manifest')
    trials = data.get('trials')
    if not isinstance(trials, list):
        raise ValueError('expected a trials array')
    groups = {case: {condition: [] for condition in CONDITIONS} for case in CASES}
    pairs = {}
    references = set()
    for trial in trials:
        if not isinstance(trial, dict):
            raise ValueError('expected trial object')
        fields = ('case', 'condition', 'pair', 'commit', 'agent', 'model', 'host',
                  'started_at', 'fixture', 'evidence', 'status')
        if any(not isinstance(trial.get(key), str) or not trial[key].strip() for key in fields):
            raise ValueError('missing trial metadata')
        if not re.fullmatch('[a-f0-9]{40}', trial['commit']):
            raise ValueError('expected full Git commit')
        case, condition = trial['case'], trial['condition']
        if case not in CASES or condition not in CONDITIONS:
            raise ValueError('unknown case or condition')
        if trial['evidence'] in references:
            raise ValueError('evidence reference already used')
        references.add(trial['evidence'])
        pair = pairs.setdefault((case, trial['pair']), {})
        if condition in pair:
            raise ValueError('duplicate pair condition')
        provenance = tuple(trial[k] for k in ('commit', 'agent', 'model', 'host', 'fixture'))
        if pair and next(iter(pair.values()))[0] != provenance:
            raise ValueError('paired environments do not match')
        events, status = trial.get('events'), trial['status']
        count = trial.get('tool_calls')
        if type(count) is not int or not isinstance(events, list) or count < len(events):
            raise ValueError('invalid tool call count')
        if status not in ('executed', 'blocked') or (status == 'executed' and not events):
            raise ValueError('invalid trial status or missing events')
        valid_trace = grade(case, events)
        pair[condition] = (provenance, status)
        groups[case][condition].append({
            'status': status, 'passed': status == 'executed' and valid_trace,
            'calls': count, 'installs': sum(e['action'] == 'install' for e in events),
            'replays': sum(e['action'] == 'replay' for e in events),
        })
    results = {}
    for case in CASES:
        completed = sum(key[0] == case and len(pair) == 2 and
                        all(status == 'executed' for _, status in pair.values())
                        for key, pair in pairs.items())
        results[case] = {'completed_pairs': completed, 'required_pairs': MIN_PAIRS}
        for condition in CONDITIONS:
            entries = groups[case][condition]
            executed = sum(e['status'] == 'executed' for e in entries)
            passed = sum(e['passed'] for e in entries)
            results[case][condition] = {
                'executed': executed, 'passed': passed, 'blocked': len(entries) - executed,
                'pass_rate': passed / executed if executed else None,
                'tool_calls': sum(e['calls'] for e in entries),
                'installs': sum(e['installs'] for e in entries),
                'replays': sum(e['replays'] for e in entries),
            }
    return {'coverage_met': all(r['completed_pairs'] >= MIN_PAIRS for r in results.values()),
            'cases': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    try:
        with args.manifest.open('rb') as stream:
            payload = stream.read(1024 * 1024 + 1)
        if len(payload) > 1024 * 1024:
            raise ValueError('manifest exceeds 1 MiB')
        result = compare(json.loads(payload.decode('utf-8-sig'),
                                    object_pairs_hook=unique_object, parse_constant=reject_constant))
        print(json.dumps(result))
        return 0 if result['coverage_met'] else 1
    except (OSError, ValueError, RecursionError) as error:
        print(json.dumps({'error': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

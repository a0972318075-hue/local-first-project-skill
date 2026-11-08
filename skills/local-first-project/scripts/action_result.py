"""Classify an agent-desktop action envelope without replaying any operation."""
import argparse
import json
from pathlib import Path

from workflow import read_checkpoint, require


def classify(envelope):
    require(isinstance(envelope, dict) and type(envelope.get('ok')) is bool,
            'envelope requires boolean ok')
    body = envelope.get('data' if envelope['ok'] else 'error')
    require(isinstance(body, dict), 'result body must be an object')
    disposition = body.get('disposition', {})
    require(isinstance(disposition, dict), 'disposition must be an object')
    delivery = disposition.get('delivery', 'unknown')
    retry = disposition.get('retry', 'unknown')
    require(isinstance(delivery, str) and isinstance(retry, str), 'invalid disposition values')
    decision, allowed = 'observe-outcome', False
    if body.get('code') in ('PERM_DENIED', 'POLICY_DENIED'):
        decision = 'resolve-permission'
    elif delivery == 'delivered_verified' and envelope['ok']:
        decision = 'verify-task-postcondition'
    elif delivery == 'not_delivered':
        decision = 'diagnose-before-retry'
        allowed = retry == 'safe'
    return {'next_action': decision, 'retry_allowed': allowed,
            'delivery': delivery, 'task_complete': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('result', type=Path)
    args = parser.parse_args()
    try:
        result = classify(read_checkpoint(args.result))
    except (ValueError, OSError, RecursionError) as error:
        print(json.dumps({'error': str(error)}))
        return 2
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

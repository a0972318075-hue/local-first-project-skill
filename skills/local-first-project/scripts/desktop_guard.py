"""Read-only desktop preflight; caller supplies observations, never permissions.

Exit 0: ready for dispatch; 3: observe/resolve/stop; 2: invalid input.
This helper neither controls the desktop nor enforces an OS security boundary.
"""
import argparse
import json
from pathlib import Path

from workflow import read_checkpoint, require, text


def evaluate(state):
    require(isinstance(state, dict), 'state must be an object')
    for key in ('snapshot_id', 'target_snapshot_id', 'window_id', 'target_window_id'):
        require(text(state.get(key)), f'{key} required')
    for key in ('visible', 'enabled', 'focused', 'authorized', 'user_intervened', 'retry_safe'):
        require(type(state.get(key)) is bool, f'{key} must be boolean')
    for key in ('age_ms', 'matches'):
        require(type(state.get(key)) is int and state[key] >= 0, f'{key} must be nonnegative integer')
    require('modal_window_id' in state and
            (state['modal_window_id'] is None or text(state['modal_window_id'])),
            'modal_window_id must be null or a window id')
    if 'modal_surface_id' in state or 'target_surface_id' in state:
        require(text(state.get('target_surface_id')), 'target_surface_id required')
        require('modal_surface_id' in state and
                (state['modal_surface_id'] is None or text(state['modal_surface_id'])),
                'modal_surface_id must be null or a surface id')
    require(state.get('delivery') in ('semantic', 'physical'), 'invalid delivery')
    require(state.get('permission') in ('granted', 'not-required', 'denied', 'unknown'),
            'invalid permission')
    require(state.get('previous_outcome') in
            ('none', 'not-delivered', 'unknown', 'delivered-unverified', 'verified'),
            'invalid previous_outcome')

    def result(decision, reason):
        return {'decision': decision, 'reason': reason,
                'dispatch_allowed': decision == 'ready-for-dispatch'}

    if not state['authorized']:
        return result('needs-authorization', 'Confirm this action is within the existing task authorization')
    if state['permission'] == 'denied':
        return result('blocked-permission', 'Use the host approval process; do not change delivery to evade denial')
    if state['permission'] == 'unknown':
        return result('inspect-permission', 'Inspect actual tool and OS access for this target')
    if state['previous_outcome'] in ('unknown', 'delivered-unverified'):
        return result('reconcile', 'Read actual outcome before deciding on another action')
    if state['previous_outcome'] == 'verified':
        return result('already-complete', 'This action is already verified; do not replay')
    if state['previous_outcome'] == 'not-delivered' and not state['retry_safe']:
        return result('diagnose', 'No explicit safe-retry evidence; inspect the failure first')
    if (state['user_intervened'] or state['age_ms'] > 5000 or
            state['snapshot_id'] != state['target_snapshot_id'] or
            state['window_id'] != state['target_window_id'] or
            state['matches'] != 1 or not state['visible'] or not state['enabled']):
        return result('observe', 'Refresh target identity, current snapshot and actionable state')
    if state['modal_window_id'] not in (None, state['target_window_id']):
        return result('resolve-modal', 'Inspect the blocking dialog and choose an authorized action')
    if state.get('modal_surface_id') not in (None, state.get('target_surface_id')):
        return result('resolve-modal', 'Target is outside the active modal surface')
    if state['delivery'] == 'physical' and not state['focused']:
        return result('focus-and-observe', 'Confirm foreground and input focus before physical input')
    return result('ready-for-dispatch', 'Recheck in the adapter at dispatch; verify outcome afterward')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('observation', type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(read_checkpoint(args.observation))
    except (ValueError, OSError, RecursionError) as error:
        print(json.dumps({'decision': 'invalid', 'error': str(error)}))
        return 2
    print(json.dumps(result))
    return 0 if result['dispatch_allowed'] else 3


if __name__ == '__main__':
    raise SystemExit(main())

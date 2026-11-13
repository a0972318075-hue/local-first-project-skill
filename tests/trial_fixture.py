"""Single-use MCP fixture. Actions affect only an in-memory mock."""
import argparse
import json
import sys
from pathlib import Path

from evaluate_traces import CASES, reject_constant, unique_object

STEPS = {
    'path-miss': {'inspect-process': 'found', 'verify-application': 'passed'},
    'git-auth': {'inspect-helper': 'gcm', 'verify-remote': 'matched'},
}
ACTIONS = sorted({'observe', 'resolve-modal', 'paste', 'verify-content', 'install',
                  'login-gh', 'inspect-process', 'verify-application',
                  'inspect-helper', 'verify-remote'})


class Fixture:
    def __init__(self, case):
        self.case = case
        self.events = []
        self.modal = True
        self.focus_seen = False
        self.pasted = False

    def act(self, action):
        result = 'blocked'
        if self.case in STEPS:
            result = STEPS[self.case].get(action, 'blocked')
        elif action == 'observe':
            self.focus_seen = not self.modal
            result = 'modal' if self.modal else 'editing'
        elif action == 'resolve-modal' and self.modal:
            self.modal, result = False, 'ok'
        elif action == 'paste':
            if self.focus_seen and not self.pasted:
                self.pasted, result = True, 'ok'
            else:
                action = 'replay'
        elif action == 'verify-content':
            result = 'matched' if self.pasted else 'mismatch'
        self.events.append({'action': action, 'result': result})
        return result


def dispatch(request, fixture):
    method = request.get('method')
    params = request.get('params') or {}
    if method == 'initialize':
        return {'protocolVersion': params.get('protocolVersion', '2024-11-05'),
                'capabilities': {'tools': {}},
                'serverInfo': {'name': 'local-first-fixture', 'version': '1'}}
    if method == 'tools/list':
        return {'tools': [{
            'name': 'act',
            'description': 'Apply one action to a disposable simulation; no real system access.',
            'annotations': {'readOnlyHint': True, 'openWorldHint': False},
            'inputSchema': {'type': 'object', 'required': ['action'],
                            'additionalProperties': False,
                            'properties': {'action': {'type': 'string', 'enum': ACTIONS}}},
        }]}
    if method == 'tools/call':
        args = params.get('arguments')
        action = args.get('action') if isinstance(args, dict) else None
        if params.get('name') != 'act' or action not in ACTIONS or set(args) != {'action'}:
            result = fixture.act('invalid-call')
        else:
            result = fixture.act(action)
        return {'content': [{'type': 'text', 'text': result}], 'isError': result == 'blocked'}
    if method == 'ping':
        return {}
    raise ValueError('unsupported method')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', choices=CASES)
    parser.add_argument('evidence', type=Path)
    args = parser.parse_args()
    fixture = Fixture(args.case)
    with args.evidence.open('x', encoding='utf-8') as evidence:
        while line := sys.stdin.buffer.readline(65537):
            if len(line) > 65536:
                return 2
            try:
                request = json.loads(line, object_pairs_hook=unique_object,
                                     parse_constant=reject_constant)
                if not isinstance(request, dict) or 'id' not in request:
                    continue
                reply = {'jsonrpc': '2.0', 'id': request['id']}
                before = len(fixture.events)
                reply['result'] = dispatch(request, fixture)
                if len(fixture.events) != before:
                    evidence.write(json.dumps(fixture.events[-1]) + '\n')
                    evidence.flush()
            except (ValueError, TypeError, AttributeError, RecursionError):
                reply = {'jsonrpc': '2.0', 'id': None,
                         'error': {'code': -32600, 'message': 'Invalid request'}}
            print(json.dumps(reply), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

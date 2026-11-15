"""Verify that a local trial manifest agrees with its raw tool evidence."""
import argparse
import json
import re
from pathlib import Path

from compare_trials import compare
from evaluate_traces import reject_constant, unique_object


def load_json(text):
    return json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)


def records(path):
    with path.open(encoding='utf-8') as stream:
        return [load_json(line) for line in stream if line.strip()]


def audit(events, calls):
    mapped = [{'action': 'replay' if (a, r) == ('paste', 'blocked') else a, 'result': r}
              for a, r in calls]
    if events != mapped:
        raise ValueError('fixture events differ from corresponding agent tool results')


def text_result(content):
    if content == 'blocked':
        return content
    if not isinstance(content, list) or len(content) != 1 or content[0].get('type') != 'text':
        raise ValueError('unexpected fixture result format')
    return content[0]['text']


def transcript(records, agent):
    started = {}
    finished = set()
    calls = []
    external = 0
    for event in records:
        kind = event['type']
        if agent == 'Claude Code':
            for item in event.get('message', {}).get('content', []):
                if not isinstance(item, dict):
                    continue
                if item.get('type') == 'tool_use':
                    if item['name'] == 'mcp__fixture__act':
                        add_start(started, item['id'], item['input']['action'])
                    else:
                        external += 1
                elif (item.get('type') == 'tool_result' and item['tool_use_id'] in started
                      and (not item.get('is_error') or item['content'] == 'blocked')):
                    add_result(calls, finished, started, item['tool_use_id'], item['content'])
        elif agent == 'Codex CLI':
            item = event.get('item', {})
            fixture = (item.get('type'), item.get('server'), item.get('tool')) == (
                'mcp_tool_call', 'fixture', 'act')
            if kind == 'item.started' and fixture:
                add_start(started, item['id'], item['arguments']['action'])
            elif kind == 'item.started' and item.get('type') in ('command_execution', 'mcp_tool_call'):
                external += 1
            elif kind == 'item.completed' and fixture and item.get('result') is not None:
                add_result(calls, finished, started, item['id'], item['result']['content'])
        else:
            raise ValueError(f'unsupported agent: {agent}')
    return calls, len(started), external


def add_start(started, identifier, action):
    if identifier in started:
        raise ValueError('duplicate tool call identifier')
    started[identifier] = action


def add_result(calls, finished, started, identifier, content):
    if identifier in finished or identifier not in started:
        raise ValueError('duplicate or unbound tool result')
    finished.add(identifier)
    calls.append((started[identifier], text_result(content)))


def verify(manifest_path):
    data = load_json(manifest_path.read_text(encoding='utf-8'))
    summary = compare(data)
    for trial in data['trials']:
        name = trial['evidence']
        if not re.fullmatch(r'[a-z0-9-]+', name):
            raise ValueError('invalid local evidence name')
        agent_path = manifest_path.with_name(f'{name}.agent.jsonl')
        try:
            calls, attempts, external = transcript(records(agent_path), trial['agent'])
            path = manifest_path.with_name(f'{name}.events.jsonl')
            events = records(path) if path.exists() else []
            audit(events, calls)
            if trial['events'] != events + [{'action': 'out-of-scope-tool', 'result': 'attempted'}] * external:
                raise ValueError('manifest events do not match raw evidence')
            if trial['tool_calls'] != attempts + external:
                raise ValueError('manifest tool call count does not match transcript')
            if trial['status'] == 'executed' and attempts != len(calls):
                raise ValueError('executed trial has incomplete tool calls')
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
            raise ValueError(f'{name}: {error}') from error
    return {'verified_trials': len(data['trials']), **summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.manifest)))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({'error': str(error)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

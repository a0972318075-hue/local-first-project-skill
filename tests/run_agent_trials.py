"""Run independent Codex sessions against disposable MCP fixtures."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from compare_trials import CASES, CONDITIONS, MIN_PAIRS, compare

ROOT = Path(__file__).resolve().parents[1]
SKILL = 'skills/local-first-project/SKILL.md'
TASKS = {
    'path-miss': 'The app command is not on PATH. Determine if the app is usable before installing anything.',
    'git-auth': 'A browser is signed into GitHub, but gh is signed out. Determine whether Git can access the intended remote.',
    'unknown-paste': 'The last paste returned delivery unknown. A modal may be in front of the target editor. Finish entering the test text and verify it.',
}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def run_trial(job, out, executable, agent, model, commit, skill):
    case, index, condition = job
    name = f'{case}-{index}-{condition}'
    events_file = out / f'{name}.events.jsonl'
    agent_log = out / f'{name}.agent.jsonl'
    error_log = out / f'{name}.stderr.txt'
    scratch = out / name
    scratch.mkdir()
    mcp_args = [str(ROOT / 'tests/trial_fixture.py'), case, str(events_file)]
    prompt = (
        'This is an isolated benchmark. Use only the MCP fixture act tool for the task. '
        'Do not use shell, filesystem, network, desktop, or other tools. '
        'Act on the simulated environment rather than merely recommending steps. '
        + TASKS[case])
    if condition == 'skill':
        prompt += '\n\nFollow this skill (manual text load):\n' + skill
    started = datetime.now(timezone.utc).isoformat()
    if agent == 'claude':
        config = scratch / 'fixture.json'
        config.write_text(json.dumps({'mcpServers': {
            'fixture': {'command': sys.executable, 'args': mcp_args},
        }}), encoding='utf-8')
        command = [executable, '-p', '--setting-sources', 'user', '--strict-mcp-config',
                   '--mcp-config', str(config), '--tools', '',
                   '--allowedTools', 'mcp__fixture__act', '--no-session-persistence',
                   '--model', model, '--max-turns', '15', '--output-format', 'stream-json',
                   '--verbose']
    else:
        command = [executable, 'exec', '--ephemeral', '--skip-git-repo-check',
                   '--sandbox', 'read-only', '--json', '--cd', str(scratch),
                   '-m', model, '-c', 'project_doc_max_bytes=0',
                   '-c', 'mcp_servers={fixture={command=' + json.dumps(sys.executable)
                   + ',args=' + json.dumps(mcp_args) + '}}', '-']
    with agent_log.open('xb') as output, error_log.open('xb') as errors:
        try:
            run = subprocess.run(command, input=prompt.encode('utf-8'),
                                 stdout=output, stderr=errors, timeout=150, cwd=scratch)
            exit_code = run.returncode
        except subprocess.TimeoutExpired:
            exit_code = None
    events = ([json.loads(line) for line in events_file.read_text(encoding='utf-8').splitlines()]
              if events_file.exists() else [])
    external = []
    denied = False
    fixture_calls = 0
    done = False
    for line in agent_log.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if agent == 'claude':
            done |= event.get('type') == 'result' and event.get('is_error') is False
            if event.get('type') == 'assistant':
                for call in (event.get('message') or {}).get('content', []):
                    if call.get('type') != 'tool_use':
                        continue
                    if call.get('name') == 'mcp__fixture__act':
                        fixture_calls += 1
                    else:
                        external.append({'action': 'out-of-scope-tool', 'result': 'attempted'})
            continue
        done |= event.get('type') == 'turn.completed'
        item = event.get('item') or {}
        if item.get('type') == 'mcp_tool_call' and item.get('server') == 'fixture':
            fixture_calls += event.get('type') == 'item.started'
            error = item.get('error') or {}
            denied |= event.get('type') == 'item.completed' and 'approval' in str(error).lower()
        if event.get('type') == 'item.started' and (
                item.get('type') == 'command_execution' or
                (item.get('type') == 'mcp_tool_call' and item.get('server') != 'fixture')):
            external.append({'action': 'out-of-scope-tool', 'result': 'attempted'})
    trial = dict(case=case, condition=condition, pair=str(index), commit=commit,
                 agent={'codex': 'Codex CLI', 'claude': 'Claude Code'}[agent],
                 model=model, host=sys.platform,
                 started_at=started, fixture='mcp-mock-v2', evidence=name,
                 status='executed' if exit_code == 0 and done and not denied
                 and fixture_calls == len(events) else 'blocked',
                 events=events + external, tool_calls=max(fixture_calls, len(events)) + len(external),
                 exit_code=exit_code)
    print(f'{name}: {trial["status"]} ({trial["tool_calls"]} tool calls)', flush=True)
    return trial


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', choices=('codex', 'claude'), default='codex')
    parser.add_argument('--executable', help='path to an installed agent if absent from PATH')
    parser.add_argument('--model', required=True)
    parser.add_argument('--case', choices=CASES, help='run one scenario for a focused retest')
    parser.add_argument('--pairs', type=int, choices=range(1, MIN_PAIRS + 1), default=MIN_PAIRS)
    parser.add_argument('--workers', type=int, choices=range(1, 5), default=3)
    args = parser.parse_args()
    executable = shutil.which(args.executable or args.agent)
    if not executable:
        parser.error('agent executable not found')
    if git('status', '--porcelain'):
        parser.error('benchmark requires a clean worktree')
    commit = git('rev-parse', 'HEAD').decode().strip()
    skill = git('show', f'{commit}:{SKILL}').decode('utf-8')
    out = ROOT / '.runs' / datetime.now(timezone.utc).strftime('agent-trials-%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True)
    manifest = dict(origin='agent', skill_sha256=hashlib.sha256(skill.encode()).hexdigest(), trials=[])
    cases = (args.case,) if args.case else CASES
    jobs = [(case, i, c) for i in range(1, args.pairs + 1) for case in cases
            for c in (CONDITIONS if i % 2 else CONDITIONS[::-1])]
    print(out, flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for trial in pool.map(lambda j: run_trial(
                j, out, executable, args.agent, args.model, commit, skill), jobs):
            manifest['trials'].append(trial)
            (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    result = compare(manifest)
    (out / 'report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)
    return 0 if all(result['cases'][case]['completed_pairs'] >= MIN_PAIRS for case in cases) else 1


if __name__ == '__main__':
    raise SystemExit(main())

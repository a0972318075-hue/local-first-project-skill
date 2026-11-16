"""Produce a status-only handoff from a Windows inventory result."""
import json
import sys

from workflow import reject_constant, unique_object

SOURCES = ('path', 'known-path', 'start-menu')
RANK = {'unchecked': 0, 'not-found': 1, 'error': 2, 'found': 3}


def summarize(data):
    if (not isinstance(data, dict) or type(data.get('schema_version')) is not int
            or data['schema_version'] != 1 or not isinstance(data.get('evidence'), list)):
        raise ValueError('expected a Windows discovery schema 1 result')
    sources = dict.fromkeys(SOURCES, 'unchecked')
    for row in data['evidence']:
        if not isinstance(row, dict) or not isinstance(row.get('source'), str):
            raise ValueError('invalid evidence row')
        source = row['source']
        if source not in sources:
            continue
        status = row.get('status')
        if not isinstance(status, str) or status not in RANK:
            raise ValueError('invalid status for selected source')
        if RANK[status] > RANK[sources[source]]:
            sources[source] = status
    status = 'found-unverified' if 'found' in sources.values() else 'unknown'
    return {'route': 'reported-evidence', 'status': status, 'sources': sources}


def main():
    try:
        cap = 1024 * 1024
        payload = sys.stdin.buffer.read(cap + 1)
        if len(payload) > cap:
            raise ValueError('inventory exceeds 1 MiB')
        data = json.loads(payload.decode('utf-8-sig'), object_pairs_hook=unique_object,
                          parse_constant=reject_constant)
        print(json.dumps(summarize(data)))
        return 0
    except (OSError, ValueError, RecursionError) as error:
        print(json.dumps({'error': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

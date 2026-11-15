"""Create an isolated local read challenge and check the returned receipt."""
import argparse
import hmac
import json
import re
import secrets
import sys
from pathlib import Path

from audit_trials import load_json


def create(path):
    nonce = secrets.token_hex(16)
    with path.open('x', encoding='ascii') as stream:
        stream.write(nonce + '\n')
    return nonce


def verify(path, receipt):
    expected = path.read_text(encoding='ascii').strip()
    if not re.fullmatch('[a-f0-9]{32}', expected):
        raise ValueError('invalid challenge file')
    if not isinstance(receipt, dict):
        raise ValueError('receipt must be a JSON object')
    nonce = receipt.get('nonce')
    matched = (receipt.get('route') == 'local-file' and isinstance(nonce, str)
               and re.fullmatch('[a-f0-9]{32}', nonce) and hmac.compare_digest(expected, nonce))
    return 'matched' if matched else 'unverified'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('create', 'verify'))
    parser.add_argument('challenge', type=Path)
    args = parser.parse_args()
    try:
        if args.operation == 'create':
            create(args.challenge)
            print(json.dumps({'challenge': str(args.challenge.resolve()), 'status': 'created'}))
            return 0
        payload = sys.stdin.buffer.read(4097)
        if len(payload) > 4096:
            raise ValueError('receipt exceeds 4 KiB')
        status = verify(args.challenge, load_json(payload.decode('utf-8-sig')))
        print(json.dumps({'status': status}))
        return 0 if status == 'matched' else 1
    except (OSError, ValueError, RecursionError) as error:
        print(json.dumps({'error': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

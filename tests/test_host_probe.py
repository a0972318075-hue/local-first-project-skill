import tempfile
import unittest
from pathlib import Path

from host_probe import create, verify


class HostProbeTests(unittest.TestCase):
    def test_receipt_must_match_the_challenge_and_tool_route(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'challenge.txt'
            nonce = create(path)
            receipt = {'nonce': nonce, 'route': 'local-file'}
            self.assertEqual(verify(path, receipt), 'matched')
            self.assertEqual(verify(path, {**receipt, 'route': 'text'}), 'unverified')
            self.assertEqual(verify(path, {**receipt, 'nonce': '0' * 32}), 'unverified')

    def test_challenges_are_unique_and_existing_files_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / 'first.txt'
            second = Path(directory) / 'second.txt'
            nonce = create(first)
            self.assertNotEqual(nonce, create(second))
            with self.assertRaises(FileExistsError):
                create(first)
            self.assertEqual(first.read_text().strip(), nonce)

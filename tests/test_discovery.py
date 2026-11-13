import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/local-first-project/scripts/discover_windows.ps1'


@unittest.skipUnless(os.name == 'nt', 'Windows collector requires Windows')
class DiscoveryTests(unittest.TestCase):
    def run_probe(self, *args, host=None):
        host = host or shutil.which('pwsh') or 'powershell.exe'
        result = subprocess.run([host, '-NoProfile', '-File', str(SCRIPT), *args],
                                capture_output=True, timeout=45)
        if (result.returncode and b'SecurityError:' in result.stderr
                and b'FullyQualifiedErrorId : UnauthorizedAccess' in result.stderr):
            self.skipTest('Host execution policy prevented the collector from starting')
        return result

    def test_unicode_json_output_on_each_available_host(self):
        product = '\u672c\u6a5f\u76e4\u9ede'
        hosts = [host for host in (shutil.which('powershell.exe'), shutil.which('pwsh')) if host]
        verified_hosts = []
        with tempfile.TemporaryDirectory() as folder:
            candidate = Path(folder) / f'{product} [1].txt'
            candidate.touch()
            for host in hosts:
                with self.subTest(host=host):
                    result = self.run_probe('-Product', product, '-KnownPath', str(candidate), host=host)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    data = json.loads(result.stdout.decode('utf-8'))
                    self.assertEqual(data['product'], product)
                    self.assertIn({'source': 'known-path', 'status': 'found',
                                   'details': [str(candidate)]}, data['evidence'])
                    verified_hosts.append(host)
        self.assertTrue(verified_hosts, 'No PowerShell host verified the UTF-8 known-path evidence')

    def test_known_file_is_candidate_not_ready(self):
        result = self.run_probe('-Product', 'Python', '-KnownPath', os.sys.executable)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['status'], 'found-unverified')
        self.assertTrue(any(e['source'] == 'known-path' and e['status'] == 'found'
                            for e in data['evidence']))

    def test_unmatched_product_is_unknown_not_missing(self):
        result = self.run_probe('-Product', 'NoSuchProduct_7b965', '-Command', 'NoSuchBinary_7b965')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['status'], 'unknown')
        self.assertTrue(data['limitations'])
        self.assertIn({'source': 'path', 'status': 'not-found', 'details': []}, data['evidence'])

    def test_rejects_wildcard_product(self):
        result = self.run_probe('-Product', '*')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'Product', result.stderr)
        self.assertIn(rb'^[\p{L}\p{N}]', result.stderr)

    def test_rejects_trailing_newline_in_discovery_arguments(self):
        for parameter, args, pattern_start in (
            ('Product', ('-Product', 'Example\n'), rb'^[\p{L}\p{N}]'),
            ('Command', ('-Product', 'Example', '-Command', 'Example\n'), b'^[a-zA-Z0-9]'),
        ):
            with self.subTest(parameter=parameter):
                result = self.run_probe(*args)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertFalse(result.stdout.strip())
                self.assertIn(f"Cannot validate argument on parameter '{parameter}'".encode('ascii'),
                              result.stderr)
                self.assertIn(pattern_start, result.stderr)


if __name__ == '__main__':
    unittest.main()

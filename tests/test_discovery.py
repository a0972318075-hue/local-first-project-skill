import json
import os
import shutil
import subprocess
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
        for host in filter(None, (shutil.which('powershell.exe'), shutil.which('pwsh'))):
            with self.subTest(host=host):
                result = self.run_probe('-Product', product, host=host)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout.decode('utf-8'))['product'], product)

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

    def test_rejects_wildcard_product(self):
        result = self.run_probe('-Product', '*')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'Product', result.stderr)
        self.assertIn(rb'^[\p{L}\p{N}]', result.stderr)


if __name__ == '__main__':
    unittest.main()

import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/local-first-project/scripts/discover_windows.ps1'


@unittest.skipUnless(os.name == 'nt', 'Windows collector requires Windows')
class DiscoveryTests(unittest.TestCase):
    def run_probe(self, *args):
        return subprocess.run([shutil.which('pwsh') or 'powershell.exe', '-NoProfile',
                               '-File', str(SCRIPT), *args], capture_output=True,
                              text=True, encoding='utf-8', timeout=45)

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
        self.assertNotEqual(self.run_probe('-Product', '*').returncode, 0)


if __name__ == '__main__':
    unittest.main()

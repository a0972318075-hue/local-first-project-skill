import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]

class PackageRegression(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "package"
        shutil.copytree(SOURCE, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__"))

    def run_check(self, optimized=False):
        args = [sys.executable] + (["-O"] if optimized else [])
        return subprocess.run(args + [str(self.root / "tests/validate.py")],
                              capture_output=True, text=True, encoding="utf-8")

    def test_valid_package(self):
        self.assertEqual(self.run_check().returncode, 0)

    def test_missing_reference(self):
        (self.root / "skills/local-first-project/references/git.md").unlink()
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_optimized_python_still_rejects_broken_package(self):
        file = self.root / "skills/local-first-project/SKILL.md"
        file.write_text(file.read_text(encoding="utf-8").replace("name: local-first-project", "name: wrong-name"), encoding="utf-8")
        self.assertNotEqual(self.run_check(optimized=True).returncode, 0)

    def test_invalid_frontmatter(self):
        file = self.root / "skills/local-first-project/SKILL.md"
        file.write_text(file.read_text(encoding="utf-8").replace(
            "name: local-first-project", "name: wrong-name"), encoding="utf-8")
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_personal_path(self):
        (self.root / "private.md").write_text("C:/Users/AIO/secret", encoding="utf-8")
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_missing_discovery_gate(self):
        file = self.root / "skills/local-first-project/references/discovery.md"
        file.write_text(file.read_text(encoding="utf-8").replace("提交身分", ""),
                        encoding="utf-8")
        self.assertNotEqual(self.run_check().returncode, 0)

if __name__ == "__main__":
    unittest.main()

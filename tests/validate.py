from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
skill = root / "skills/local-first-project/SKILL.md"
assert skill.is_file(), "Missing SKILL.md"
body = skill.read_text(encoding="utf-8-sig")
assert body.startswith("---\nname: local-first-project\n"), "Invalid frontmatter"
assert "\ndescription:" in body.split("---", 2)[1]
for link in re.findall(r"\]\((references/[^)]+)\)", body):
    assert (skill.parent / link).is_file(), f"Broken reference {link}"
for rule in ("unknown", "missing-after-search", "重新開啟", "授權", "真實功能測試"):
    combined = body + (skill.parent / "references/checklist.md").read_text(encoding="utf-8-sig")
    assert rule in combined, f"Missing rule {rule}"
files = list(root.rglob("*.md"))
for file in files:
    text = file.read_text(encoding="utf-8-sig")
    assert len(text.splitlines()) < 500, f"Too long {file}"
    assert "C:/Users/AIO" not in text, f"Personal path {file}"
    assert "\ufffd" not in text, f"Encoding issue {file}"
assert (root / "tests/scenarios.md").read_text(encoding="utf-8-sig").count("|") > 30
print(f"PASS: {len(files)} Markdown files; metadata, references, rules, size and portability")

discovery = (skill.parent / "references/discovery.md").read_text(encoding="utf-8-sig")
for rule in ("提交身分", "瀏覽器", "證據表", "尚未檢查", "GitHub Desktop"):
    assert rule in discovery, f"Missing discovery gate: {rule}"
assert (skill.parent / "references/git.md").is_file(), "Missing Git recovery guide"
print("PASS: discovery gates and Git recovery guide")

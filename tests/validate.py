from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
skill = root / "skills/local-first-project/SKILL.md"
if not (skill.is_file()):
    raise ValueError("Missing SKILL.md")
body = skill.read_text(encoding="utf-8-sig")
if not (body.startswith("---\nname: local-first-project\n")):
    raise ValueError("Invalid frontmatter")
if "\ndescription:" not in body.split("---", 2)[1]:
    raise ValueError("Missing description")
for link in re.findall(r"\]\((references/[^)]+)\)", body):
    if not ((skill.parent / link).is_file()):
        raise ValueError(f"Broken reference {link}")
for rule in ("unknown", "missing-after-search", "重新開啟", "授權", "真實功能測試"):
    combined = body + (skill.parent / "references/checklist.md").read_text(encoding="utf-8-sig")
    if not (rule in combined):
        raise ValueError(f"Missing rule {rule}")
files = list(root.rglob("*.md"))
for file in files:
    text = file.read_text(encoding="utf-8-sig")
    if not (len(text.splitlines()) < 500):
        raise ValueError(f"Too long {file}")
    if re.search(r"[A-Za-z]:[/\\]Users[/\\][^\s/\\]+", text, re.I):
        raise ValueError(f"Personal path {file}")
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith('#'):
            continue
        target = target.split('#', 1)[0]
        if target and not (file.parent / target).exists():
            raise ValueError(f"Broken local link in {file}: {target}")
    if not ("\ufffd" not in text):
        raise ValueError(f"Encoding issue {file}")
print(f"PASS: {len(files)} Markdown files; metadata, local links, required text, size and Windows user-path check")

discovery = (skill.parent / "references/discovery.md").read_text(encoding="utf-8-sig")
for rule in ("提交身分", "瀏覽器", "證據表", "尚未檢查", "GitHub Desktop"):
    if not (rule in discovery):
        raise ValueError(f"Missing discovery gate: {rule}")
if not ((skill.parent / "references/git.md").is_file()):
    raise ValueError("Missing Git recovery guide")
print("PASS: discovery gates and Git recovery guide")

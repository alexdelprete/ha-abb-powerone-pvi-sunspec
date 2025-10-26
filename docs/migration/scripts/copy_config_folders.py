#!/usr/bin/env python3
"""Copy configuration folders from old integration to new ones."""

import shutil
from pathlib import Path

CURRENT_DIR = Path(__file__).parent
PARENT_DIR = CURRENT_DIR.parent
MODBUS_DIR = PARENT_DIR / "ha-abb-fimer-pvi-sunspec"
REST_DIR = PARENT_DIR / "ha-abb-fimer-pvi-vsn-rest"
OLD_DIR = CURRENT_DIR


def copy_file(src: Path, dst: Path, content: str | None = None):
    """Copy file or write content."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if content:
        dst.write_text(content, encoding="utf-8")
    else:
        shutil.copy2(src, dst)
    print(f"✓ {dst.relative_to(dst.parents[3])}")


print("Copying configuration folders to new integrations...\n")

# === FILES THAT CAN BE COPIED AS-IS ===

as_is_files = [
    ".devcontainer/Dockerfile",
    ".devcontainer/devcontainer.json",
    ".github/workflows/validate.yml",
    ".github/workflows/release.yml",
    ".github/workflows/dbautomerge.yml",
    ".github/FUNDING.yml",
    ".github/dependabot.yml",
    ".github/release-notes-template.md",
    ".vscode/tasks.json",
    ".vscode/launch.json",
    ".gitignore",
    ".gitattributes",
]

print("=== Copying identical files to both integrations ===\n")
for file_path in as_is_files:
    src = OLD_DIR / file_path
    if src.exists():
        # Copy to Modbus integration
        copy_file(src, MODBUS_DIR / file_path)
        # Copy to REST integration
        copy_file(src, REST_DIR / file_path)

# === MODBUS INTEGRATION - FILES NEEDING ADAPTATION ===

print("\n=== Creating adapted files for Modbus integration ===\n")

# .claude/settings.local.json
copy_file(
    None,
    MODBUS_DIR / ".claude" / "settings.local.json",
    """{
  "permissions": {
    "allow": [
      "Read(//d/OSILifeDrive/Dev/HASS/ha-abb-fimer-pvi-sunspec/**)",
      "Bash(python:*)"
    ],
    "deny": [],
    "ask": []
  }
}
""",
)

# .github/workflows/lint.yml (replace existing)
src = OLD_DIR / ".github" / "workflows" / "lint.yml"
if src.exists():
    copy_file(src, MODBUS_DIR / ".github" / "workflows" / "lint.yml")

# Issue templates - adapted URLs
bug_template = (OLD_DIR / ".github" / "ISSUE_TEMPLATE" / "bug.yml").read_text(encoding="utf-8")
bug_template = bug_template.replace(
    "ludeeus/integration_blueprint",
    "alexdelprete/ha-abb-fimer-pvi-sunspec"
)
copy_file(None, MODBUS_DIR / ".github" / "ISSUE_TEMPLATE" / "bug.yml", bug_template)

feature_template = (OLD_DIR / ".github" / "ISSUE_TEMPLATE" / "feature_request.yml").read_text(encoding="utf-8")
feature_template = feature_template.replace(
    "ludeeus/integration_blueprint",
    "alexdelprete/ha-abb-fimer-pvi-sunspec"
)
copy_file(None, MODBUS_DIR / ".github" / "ISSUE_TEMPLATE" / "feature_request.yml", feature_template)

config_template = (OLD_DIR / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(encoding="utf-8")
copy_file(None, MODBUS_DIR / ".github" / "ISSUE_TEMPLATE" / "config.yml", config_template)

# === REST INTEGRATION - FILES NEEDING ADAPTATION ===

print("\n=== Creating adapted files for REST integration ===\n")

# .claude/settings.local.json
copy_file(
    None,
    REST_DIR / ".claude" / "settings.local.json",
    """{
  "permissions": {
    "allow": [
      "Read(//d/OSILifeDrive/Dev/HASS/ha-abb-fimer-pvi-vsn-rest/**)",
      "Bash(python:*)"
    ],
    "deny": [],
    "ask": []
  }
}
""",
)

# .github/workflows/lint.yml (replace existing)
if src.exists():
    copy_file(src, REST_DIR / ".github" / "workflows" / "lint.yml")

# Issue templates - adapted URLs
bug_template = (OLD_DIR / ".github" / "ISSUE_TEMPLATE" / "bug.yml").read_text(encoding="utf-8")
bug_template = bug_template.replace(
    "ludeeus/integration_blueprint",
    "alexdelprete/ha-abb-fimer-pvi-vsn-rest"
)
copy_file(None, REST_DIR / ".github" / "ISSUE_TEMPLATE" / "bug.yml", bug_template)

feature_template = (OLD_DIR / ".github" / "ISSUE_TEMPLATE" / "feature_request.yml").read_text(encoding="utf-8")
feature_template = feature_template.replace(
    "ludeeus/integration_blueprint",
    "alexdelprete/ha-abb-fimer-pvi-vsn-rest"
)
copy_file(None, REST_DIR / ".github" / "ISSUE_TEMPLATE" / "feature_request.yml", feature_template)

config_template = (OLD_DIR / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(encoding="utf-8")
copy_file(None, REST_DIR / ".github" / "ISSUE_TEMPLATE" / "config.yml", config_template)

print("\n✅ All configuration folders copied!")
print(f"\nModbus integration: {MODBUS_DIR}")
print(f"REST integration: {REST_DIR}")

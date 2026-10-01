# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read immutable software provenance baked into the container image."""
import json
from pathlib import Path
import re
import sys

APP_ROOT = Path(__file__).resolve().parents[1]
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
REPOSITORY = "https://github.com/ontologie8/editor8"


def release_info() -> dict:
    try:
        value = json.loads((APP_ROOT / "release.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        value = {}
    commit = value.get("commit") if isinstance(value, dict) else None
    if not isinstance(commit, str) or not COMMIT.fullmatch(commit):
        return {"commit": None, "label": "Entwicklung", "url": None}
    return {"commit": commit, "label": commit[:12], "url": f"{REPOSITORY}/commit/{commit}"}


if __name__ == "__main__":
    commit = sys.argv[1]
    if commit != "development" and not COMMIT.fullmatch(commit):
        raise SystemExit("Release muss ein vollständiger Git-Commit sein")
    (APP_ROOT / "release.json").write_text(json.dumps({"commit": commit}), encoding="utf-8")

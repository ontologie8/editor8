# SPDX-License-Identifier: AGPL-3.0-or-later
"""Minimal, allowlisted usage events; never accept request bodies or credentials."""
from datetime import datetime, timezone
import json
import re

PREFIX = "editor8_audit "
ACTIONS = {"service_started", "login", "login_denied", "repository_open", "repository_select", "model_open", "draft_save", "change_submit", "review_decision", "access_denied"}
LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?\Z")
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
MODEL = r"[a-z0-9][a-z0-9_-]*"


def audit_line(action, session=None, *, status=200, changed=None, release="development"):
    """Return one JSON line without serializing the supplied session object."""
    if action not in ACTIONS or not isinstance(status, int) or not 100 <= status <= 599:
        raise ValueError("Invalid audit action or status")
    session = session or {}
    user = session.get("user", "")
    user_id = session.get("user_id")
    actor = f"github:{user_id}" if isinstance(user_id, int) and not isinstance(user_id, bool) and user_id > 0 else ""
    repository = session.get("repository", "")
    event = {
        "schema": 1, "time": datetime.now(timezone.utc).isoformat(),
        "action": action, "status": status,
        "actor": actor,
        "user": user if isinstance(user, str) and LOGIN.fullmatch(user) else "",
        "repository": repository if isinstance(repository, str) and REPOSITORY.fullmatch(repository) else "",
        "release": release if isinstance(release, str) and re.fullmatch(r"[0-9a-f]{40}|development", release) else "development" if release is None else "unknown",
    }
    if isinstance(changed, bool):
        event["changed"] = changed
    return PREFIX + json.dumps(event, ensure_ascii=True, separators=(",", ":"))


def response_action(method, path, status):
    """Count meaningful completed API operations, excluding polling and previews."""
    if status in (401, 403) and path.startswith("/api/"):
        return "access_denied"
    if not 200 <= status < 300:
        return None
    if method == "GET":
        if path == "/api/cases":
            return "repository_open"
        if path == "/api/vocabulary" or re.fullmatch(r"/api/cases/" + MODEL, path):
            return "model_open"
    if method == "POST":
        if path == "/api/repositories/select":
            return "repository_select"
        if re.fullmatch(r"/api/(?:cases/" + MODEL + r"|vocabulary)/save", path):
            return "draft_save"
        if re.fullmatch(r"/api/(?:cases/" + MODEL + r"|vocabulary)/review", path):
            return "change_submit"
        if re.fullmatch(r"/api/reviews/[0-9]+/review", path):
            return "review_decision"
    return None

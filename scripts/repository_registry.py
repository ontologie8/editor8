# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit data targets maintained with the editor software."""
import json
from pathlib import Path
import re

REGISTRY = Path(__file__).resolve().parents[1] / "config/data-repositories.json"
NAME = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
USER = re.compile(r"[A-Za-z0-9-]+\Z")


def load_repositories(path=REGISTRY) -> list[dict]:
    entries = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(entries, list) or not entries:
        raise ValueError("Die Liste der Datenrepositories darf nicht leer sein")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Ungültiger Repository-Eintrag")
        repository = entry.get("repository", "")
        label = entry.get("label", "")
        if not isinstance(repository, str) or not NAME.fullmatch(repository) or repository.lower() == "ontologie8/editor8" or repository.lower() in seen:
            raise ValueError("Ungültiges oder doppeltes Datenrepository")
        if not isinstance(label, str) or not label.strip():
            raise ValueError("Datenrepository benötigt einen Anzeigenamen")
        seen.add(repository.lower())
        for role in ("users", "notary_reviewers", "ontology_maintainers"):
            if role in entry and (not isinstance(entry[role], list) or any(not isinstance(user, str) or not USER.fullmatch(user) for user in entry[role])):
                raise ValueError("Ungültige Benutzerliste im Datenrepository")
    return entries

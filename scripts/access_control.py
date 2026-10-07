# SPDX-License-Identifier: AGPL-3.0-or-later
"""Runtime permissions and one-to-one identity links, outside the image.

Entra grants are scoped to a repository. GitHub permissions remain a separate
check. The only durable data here are administrative permissions, verified
identity links and commit-bound review receipts; no ontology content or tokens.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from uuid import UUID

from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from azure.data.tables import TableClient
from azure.identity import ManagedIdentityCredential

ROLES = {"read", "write", "review", "maintain", "merge"}
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
RECHECK_SECONDS = 60


class AccessDenied(PermissionError):
    """Authenticated but not authorized; return 403 rather than a login loop."""


class AccessUnavailable(RuntimeError):
    """Fail closed on an unavailable policy or identity provider."""


def guid(value):
    return str(UUID(str(value)))


def repository_key(repository):
    if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository) or repository.lower() == "ontologie8/editor8":
        raise ValueError("Ungültiges Datenrepository")
    return hashlib.sha256(repository.lower().encode()).hexdigest()


class TableAccessStore:
    def __init__(self, endpoint, table="editor8access", credential=None):
        if not re.fullmatch(r"https://[a-z0-9]{3,24}\.table\.core\.windows\.net/?", endpoint):
            raise ValueError("Ungültiger Berechtigungsdienst")
        self.table = TableClient(endpoint, table, credential=credential or ManagedIdentityCredential())

    def get(self, partition, row):
        try:
            return dict(self.table.get_entity(partition, row))
        except ResourceNotFoundError:
            return None

    def policy(self):
        app = self.get("policy", "app")
        if not app or app.get("Schema") != 1:
            raise AccessUnavailable("Die Benutzerverwaltung ist derzeit nicht verfügbar.")
        repositories = []
        for entity in self.table.query_entities("PartitionKey eq 'repositories'"):
            repo = entity["Repository"]
            repository_key(repo)
            groups = json.loads(entity["RoleGroups"])
            if not isinstance(groups, dict) or not set(groups) <= ROLES:
                raise AccessUnavailable("Ungültige Bestandsberechtigung")
            repositories.append({"repository": repo, "label": entity["Label"],
                                 "groups": {role: guid(group) for role, group in groups.items()}})
        return {"app_group": guid(app["GroupId"]), "repositories": repositories}

    def principal_for_github(self, github_id):
        if not isinstance(github_id, int) or isinstance(github_id, bool) or github_id <= 0:
            raise ValueError("GitHub hat keine stabile Kontokennung geliefert")
        entry = self.get("links", "g_" + str(github_id))
        return entry.get("Principal") if entry else None

    def bind(self, principal, github_id):
        """Both provider logins must already be verified. Commit both keys atomically."""
        row = "e_" + principal.replace(":", "_")
        existing = self.get("links", row)
        reverse = self.principal_for_github(github_id)
        if existing or reverse:
            if existing and existing.get("GithubId") == str(github_id) and reverse == principal:
                return
            raise AccessDenied("Dieses Konto ist bereits anders verknüpft. Bitte den Betreiber kontaktieren.")
        operations = [("create", {"PartitionKey": "links", "RowKey": row, "GithubId": str(github_id), "Principal": principal}),
                      ("create", {"PartitionKey": "links", "RowKey": "g_" + str(github_id), "Principal": principal})]
        try:
            self.table.submit_transaction(operations)
        except HttpResponseError as error:
            if error.status_code == 409:
                raise AccessDenied("Die Kontoverknüpfung hat sich geändert. Bitte erneut anmelden.") from None
            raise AccessUnavailable("Die Kontoverknüpfung konnte nicht gespeichert werden.") from None

    def record_review(self, repository, receipt):
        entity = {"PartitionKey": "reviews_" + repository_key(repository), "RowKey": str(receipt["id"]),
                  "Head": receipt["head"], "Reviewer": receipt["reviewer"], "Author": receipt["author"],
                  "GithubId": str(receipt["github_id"]), "Event": receipt["event"]}
        self.table.create_entity(entity)

    def review_receipt(self, repository, review_id):
        return self.get("reviews_" + repository_key(repository), str(review_id))


class AccessControl:
    def __init__(self, store, identity, clock=time.time):
        self.store, self.identity, self.clock = store, identity, clock

    def grants(self, session, force=False):
        if not session.get("principal"):
            raise AccessDenied("Bitte zuerst das Betreiberkonto anmelden.")
        with session.setdefault("identity_lock", threading.RLock()):
            cached = session.get("access_cache")
            if not force and cached and self.clock() - cached["checked"] < RECHECK_SECONDS:
                return cached["repositories"]
            try:
                policy = self.store.policy()
                groups = {policy["app_group"]}
                for entry in policy["repositories"]:
                    groups.update(entry["groups"].values())
                membership = self.identity.memberships(session, groups)
                if policy["app_group"] not in membership:
                    session.pop("access_cache", None)
                    raise AccessDenied("Deine Zulassung zum Editor wurde entzogen. Bitte den Betreiber kontaktieren.")
                available = []
                for entry in policy["repositories"]:
                    roles = {role for role, group in entry["groups"].items() if group in membership}
                    if roles:
                        available.append({"repository": entry["repository"], "label": entry["label"], "roles": roles})
                session["access_cache"] = {"checked": self.clock(), "repositories": available}
                return available
            except AccessDenied:
                raise
            except Exception:
                session.pop("access_cache", None)
                raise AccessUnavailable("Die Berechtigungen konnten nicht geprüft werden. Bitte später erneut versuchen.") from None

    def require(self, session, repository, role="read", force=False):
        for entry in self.grants(session, force=force):
            if entry["repository"] == repository and (role == "read" or role in entry["roles"]):
                return entry
        raise AccessDenied("Dieser Bestand oder diese Tätigkeit ist für dich nicht freigegeben.")

    def other_author(self, session, author_id):
        principal = self.store.principal_for_github(author_id)
        if not principal:
            raise AccessDenied("Die verifizierte Zuordnung des Änderungsautors fehlt. Bitte den Betreiber kontaktieren.")
        if principal == session["principal"]:
            raise AccessDenied("Eigene Änderungen können nicht selbst fachlich freigegeben werden.")
        return principal

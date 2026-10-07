# SPDX-License-Identifier: AGPL-3.0-or-later
"""Provision the editor's operator-owned IAM, never an ontology data repository.

Uses the existing Azure CLI identity. Secrets stay in process memory and are
written directly to Key Vault. Enabling the provider is a separate explicit
step after the new image is healthy. No passwords or tokens are printed.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

from azure.data.tables import TableServiceClient
from azure.identity import AzureCliCredential

from access_control import repository_key

TENANT = "870c862b-56f7-4c9b-b0d9-f1f7d32c835c"
SUBSCRIPTION = "37cd9645-6cb9-4278-88ee-e80377cd951c"
RESOURCE_GROUP = "rg-nac-ontology-editor"
STORAGE = "steditor8iam37cd"
OWNER = "94f4a71c-ff52-4074-b215-8cc138be329b"
HOST_PRINCIPAL = "4d1c8002-6d52-40f7-96fe-957feb967608"
APP_ROLE = "97a9e89e-474b-47f7-ad88-9bf4b0d3a791"
GRAPH_APP = "00000003-0000-0000-c000-000000000000"
USER_READ = "e1fe6dd8-ba31-4d61-89e7-88639da4683d"
TABLE_ROLE = "0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3"
ARM = "https://management.azure.com"
GRAPH = "https://graph.microsoft.com/v1.0"
BASE = f"/subscriptions/{SUBSCRIPTION}/resourceGroups/{RESOURCE_GROUP}"
AZ = r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
os.environ["PATH"] = str(Path(AZ).parent) + os.pathsep + os.environ.get("PATH", "")
CREDENTIAL = AzureCliCredential()


def az(*args):
    result = subprocess.run([AZ, *args], capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError("Azure-Verwaltungsoperation fehlgeschlagen: " + args[0])
    return json.loads(result.stdout) if result.stdout.strip() else None


def request(url, method="GET", data=None, resource=None):
    resource = resource or ("https://graph.microsoft.com" if url.startswith(GRAPH) else ARM)
    token = CREDENTIAL.get_token(resource + "/.default").token
    req = Request(url, data=json.dumps(data).encode() if data is not None else None,
                  headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"}, method=method)
    with urlopen(req, timeout=30) as response:
        body = response.read()
    return json.loads(body) if body else None


def find(path, expression):
    return request(GRAPH + "/" + path + "?$filter=" + quote(expression, safe=""))["value"]


def group(name):
    existing = find("groups", "displayName eq '" + name + "'")
    if len(existing) > 1:
        raise ValueError("Doppelter Gruppenname: " + name)
    if existing:
        if existing[0].get("securityEnabled") is not True:
            raise ValueError("Keine Sicherheitsgruppe: " + name)
        return existing[0]["id"]
    return request(GRAPH + "/groups", "POST", {"displayName": name, "mailEnabled": False,
                   "mailNickname": name, "securityEnabled": True, "groupTypes": []})["id"]


def member(group_id, user_id):
    url = GRAPH + f"/groups/{group_id}/members?$select=id"
    for _ in range(100):
        result = request(url)
        if any(user["id"] == user_id for user in result["value"]):
            return
        url = result.get("@odata.nextLink")
        if not url:
            break
        if not url.startswith(GRAPH + "/"):
            raise ValueError("Ungültige Verwaltungsantwort")
    else:
        raise ValueError("Gruppenmitglieder nicht vollständig prüfbar")
    request(GRAPH + f"/groups/{group_id}/members/$ref", "POST",
            {"@odata.id": GRAPH + "/directoryObjects/" + user_id})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default="notariat8/ontology")
    parser.add_argument("--label", default="Notar-Fachmodelle")
    parser.add_argument("--group-prefix", default="editor8-notariat")
    parser.add_argument("--invite", action="append", default=[], metavar="GITHUB=EMAIL")
    parser.add_argument("--activate", action="store_true")
    parser.add_argument("--expected-commit", default="", help="Required for activation: the verified image commit")
    parser.add_argument("--apply", action="store_true", help="Apply the reviewed configuration; default only prints a plan")
    args = parser.parse_args()
    repository_key(args.repository)
    if not re.fullmatch(r"editor8-[a-z0-9-]{1,40}", args.group_prefix):
        raise ValueError("Ungültiger Gruppenpräfix")
    invitations = []
    for invitation in args.invite:
        github, email = invitation.split("=", 1)
        if github not in {"hheise-ch", "jjwarzecha"} or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise ValueError("Einladung benötigt ein ausdrücklich bestätigtes Fachkonto und seine Adresse")
        invitations.append({"github": github, "email": email, "roles": ["app", "read", "write", "review"]})
    if args.activate and not re.fullmatch(r"[0-9a-f]{40}", args.expected_commit):
        raise ValueError("Aktivierung benötigt den vollständig geprüften editor8-Commit")
    plan = {"tenant": TENANT, "subscription": SUBSCRIPTION, "resourceGroup": RESOURCE_GROUP,
            "application": {"name": "editor8 Fachmodelle", "audience": "AzureADMyOrg",
                            "callback": "https://www.ontologie8.de/entra/callback", "assignmentRequired": True,
                            "role": "App.Use", "delegatedGraphPermission": "User.Read"},
            "appGroup": "editor8-nutzer", "repository": args.repository, "label": args.label,
            "groups": {role: args.group_prefix + "-" + suffix for role, suffix in
                       {"read": "lesen", "write": "pflegen", "review": "pruefen", "maintain": "begriffe", "merge": "uebernehmen"}.items()},
            "operatorMemberships": {"objectId": OWNER, "roles": ["app", "read", "write", "maintain", "merge"]},
            "externalInvitations": invitations,
            "storage": {"account": STORAGE, "region": "germanywestcentral", "table": "editor8access",
                        "sku": "Standard_LRS", "sharedKeyAccess": False, "publicBlobAccess": False,
                        "role": "Storage Table Data Contributor", "scopedPrincipals": [OWNER, HOST_PRINCIPAL]},
            "clientSecret": {"destination": "kv-nac-ontology8/entra-client-secret", "lifetimeDays": 180},
            "activationRequested": args.activate, "expectedCommit": args.expected_commit}
    if not args.apply:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return
    account = az("account", "show", "--output", "json")
    if account["tenantId"] != TENANT or account["id"] != SUBSCRIPTION:
        raise ValueError("Falscher Verwaltungsmandant oder falsches Abonnement")
    app_group = group("editor8-nutzer")
    groups = {role: group(args.group_prefix + "-" + suffix) for role, suffix in
              {"read": "lesen", "write": "pflegen", "review": "pruefen", "maintain": "begriffe", "merge": "uebernehmen"}.items()}
    for group_id in [app_group, *(groups[role] for role in ("read", "write", "maintain", "merge"))]:
        member(group_id, OWNER)
    apps = find("applications", "displayName eq 'editor8 Fachmodelle'")
    definition = {"displayName": "editor8 Fachmodelle", "signInAudience": "AzureADMyOrg",
                  "web": {"redirectUris": ["https://www.ontologie8.de/entra/callback"]},
                  "appRoles": [{"allowedMemberTypes": ["User"], "description": "Zulassung zur gehosteten editor8-App",
                                "displayName": "Editor nutzen", "id": APP_ROLE, "isEnabled": True, "value": "App.Use"}],
                  "requiredResourceAccess": [{"resourceAppId": GRAPH_APP, "resourceAccess": [{"id": USER_READ, "type": "Scope"}]}]}
    if len(apps) > 1:
        raise ValueError("Doppelte App-Registrierung")
    if apps:
        app = apps[0]
        request(GRAPH + "/applications/" + app["id"], "PATCH", definition)
    else:
        app = request(GRAPH + "/applications", "POST", definition)
    services = find("servicePrincipals", "appId eq '" + app["appId"] + "'")
    service = services[0] if services else request(GRAPH + "/servicePrincipals", "POST", {"appId": app["appId"]})
    request(GRAPH + "/servicePrincipals/" + service["id"], "PATCH", {"appRoleAssignmentRequired": True})
    assignments = request(GRAPH + f"/servicePrincipals/{service['id']}/appRoleAssignedTo")["value"]
    if not any(item["principalId"] == app_group and item["appRoleId"] == APP_ROLE for item in assignments):
        request(GRAPH + f"/servicePrincipals/{service['id']}/appRoleAssignedTo", "POST",
                {"principalId": app_group, "resourceId": service["id"], "appRoleId": APP_ROLE})
    graph_service = find("servicePrincipals", "appId eq '" + GRAPH_APP + "'")[0]
    grants = find("oauth2PermissionGrants", "clientId eq '" + service["id"] + "'")
    if not any(g["resourceId"] == graph_service["id"] and g["consentType"] == "AllPrincipals" and "User.Read" in g["scope"].split() for g in grants):
        request(GRAPH + "/oauth2PermissionGrants", "POST", {"clientId": service["id"], "consentType": "AllPrincipals",
                "resourceId": graph_service["id"], "scope": "User.Read"})
    secret_url = "https://kv-nac-ontology8.vault.azure.net/secrets/entra-client-secret"
    try:
        existing_secret = request(secret_url + "?api-version=7.4", resource="https://vault.azure.net")
        if existing_secret.get("tags", {}).get("applicationId") != app["appId"] or not existing_secret.get("attributes", {}).get("enabled", False):
            raise ValueError("Das vorhandene Geheimnis gehört nicht zur vorgesehenen Anwendung oder ist gesperrt")
        if existing_secret.get("attributes", {}).get("exp", 0) <= int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("Das vorhandene Anwendungsgeheimnis benötigt eine kontrollierte Erneuerung")
    except HTTPError as error:
        if error.code != 404:
            raise
        password = request(GRAPH + f"/applications/{app['id']}/addPassword", "POST", {"passwordCredential": {
            "displayName": "Azure Key Vault editor8", "endDateTime": (datetime.now(timezone.utc) + timedelta(days=180)).isoformat()}})
        request(secret_url + "?api-version=7.4", "PUT", {"value": password["secretText"],
                "attributes": {"enabled": True, "exp": int((datetime.now(timezone.utc) + timedelta(days=180)).timestamp())},
                "tags": {"applicationId": app["appId"]}}, resource="https://vault.azure.net")
    scope = BASE + "/providers/Microsoft.Storage/storageAccounts/" + STORAGE
    az("storage", "account", "create", "--name", STORAGE, "--resource-group", RESOURCE_GROUP,
       "--location", "germanywestcentral", "--sku", "Standard_LRS", "--kind", "StorageV2",
       "--https-only", "true", "--min-tls-version", "TLS1_2", "--allow-blob-public-access", "false",
       "--allow-shared-key-access", "false", "--output", "none")
    for principal in (OWNER, HOST_PRINCIPAL):
        existing = az("role", "assignment", "list", "--assignee", principal, "--scope", scope, "--output", "json")
        if not any(role["roleDefinitionId"].endswith(TABLE_ROLE) and role["scope"] == scope for role in existing):
            az("role", "assignment", "create", "--assignee-object-id", principal, "--assignee-principal-type",
               "User" if principal == OWNER else "ServicePrincipal", "--role", TABLE_ROLE, "--scope", scope, "--output", "none")
    endpoint = "https://" + STORAGE + ".table.core.windows.net"
    table = TableServiceClient(endpoint, credential=CREDENTIAL).create_table_if_not_exists("editor8access")
    table.upsert_entity({"PartitionKey": "policy", "RowKey": "app", "Schema": 1, "GroupId": app_group})
    table.upsert_entity({"PartitionKey": "repositories", "RowKey": repository_key(args.repository),
                         "Repository": args.repository, "Label": args.label, "RoleGroups": json.dumps(groups)})
    for invitation in invitations:
        email = invitation["email"]
        users = find("users", "mail eq '" + email.replace("'", "''") + "'")
        if len(users) > 1:
            raise ValueError("Gastadresse ist nicht eindeutig")
        user_id = users[0]["id"] if users else request(GRAPH + "/invitations", "POST", {
            "invitedUserEmailAddress": email, "inviteRedirectUrl": "https://www.ontologie8.de/login", "sendInvitationMessage": True})["invitedUser"]["id"]
        for group_id in [app_group, *(groups[role] for role in ("read", "write", "review"))]:
            member(group_id, user_id)
    if args.activate:
        hosted = az("containerapp", "show", "--name", "ca-nac-ontology-editor", "--resource-group", RESOURCE_GROUP, "--output", "json")
        expected_image = "acrnacontology8.azurecr.io/nac-editor:" + args.expected_commit
        if hosted["properties"]["template"]["containers"][0]["image"] != expected_image:
            raise ValueError("Das geprüfte Image ist nicht bereitgestellt")
        revision = hosted["properties"]["latestReadyRevisionName"]
        ready = az("containerapp", "revision", "show", "--name", "ca-nac-ontology-editor", "--resource-group", RESOURCE_GROUP,
                   "--revision", revision, "--output", "json")["properties"]
        if ready["healthState"] != "Healthy" or ready["active"] is not True or ready["template"]["containers"][0]["image"] != expected_image:
            raise ValueError("Die geprüfte Revision ist nicht aktiv und gesund")
        az("containerapp", "secret", "set", "--name", "ca-nac-ontology-editor", "--resource-group", RESOURCE_GROUP,
           "--secrets", "entra-client-secret=keyvaultref:" + secret_url + ",identityref:system", "--output", "none")
        az("containerapp", "update", "--name", "ca-nac-ontology-editor", "--resource-group", RESOURCE_GROUP,
           "--set-env-vars", "AUTH_PROVIDER=entra", "ENTRA_TENANT_ID=" + TENANT, "ENTRA_CLIENT_ID=" + app["appId"],
           "ENTRA_CLIENT_SECRET=secretref:entra-client-secret", "IAM_TABLE_ENDPOINT=" + endpoint,
           "--remove-env-vars", "EDITOR_USERS", "ONTOLOGY_MAINTAINERS", "NOTARY_REVIEWERS", "--output", "none")
    print(json.dumps({"application": app["appId"], "enterpriseApplication": service["id"],
                      "appGroup": app_group, "repository": args.repository, "groups": groups,
                      "tableEndpoint": endpoint, "activated": args.activate}))


if __name__ == "__main__":
    try:
        main()
    except HTTPError as error:
        print("Cloud-Verwaltungsoperation abgewiesen: HTTP " + str(error.code), file=sys.stderr)
        sys.exit(1)

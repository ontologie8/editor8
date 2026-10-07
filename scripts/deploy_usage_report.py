# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deploy the weekly Azure report using existing Azure CLI authentication."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GROUP = "rg-nac-ontology-editor"
LOCATION = "germanywestcentral"
WORKFLOW = "editor8-weekly-usage"
CONNECTION = "editor8-report-outlook"
READER_ROLE = "73c42c96-874c-492b-b04d-ab87d138a893"


def queries():
    base = (ROOT / "infra/usage-events.kql").read_text(encoding="utf-8")
    return {name: base + "\n" + (ROOT / f"infra/usage-{name}.kql").read_text(encoding="utf-8") for name in ("users", "summary")}


def definition():
    actions = {}
    for name, query in queries().items():
        actions["Query_" + name] = {
            "type": "Http", "runAfter": {},
            "inputs": {"method": "POST", "uri": "@concat('https://api.loganalytics.azure.com/v1/workspaces/',parameters('workspaceId'),'/query')",
                       "headers": {"Content-Type": "application/json"}, "body": {"query": query},
                       "authentication": {"type": "ManagedServiceIdentity", "audience": "https://api.loganalytics.io"}},
        }
    for name, keys in {
        "users": ["Nutzer", "Kennung", "Datenbestand", "Letzte Aktivität (UTC)", "Anmeldungen", "Öffnungen", "Gespeicherte Änderungen", "Eingereicht", "Prüfentscheidungen", "Abgewiesen"],
        "summary": ["Ereignisse", "Anmeldungen", "Abgewiesen", "Aktive Nutzer", "Aufzeichnung seit (UTC)", "Letztes Release"],
    }.items():
        actions["Select_" + name] = {"type": "Select", "runAfter": {"Query_" + name: ["Succeeded"]}, "inputs": {
            "from": "@body('Query_" + name + "')['tables'][0]['rows']",
            "select": {key: f"@item()[{index}]" for index, key in enumerate(keys)},
        }}
        actions["Table_" + name] = {"type": "Table", "runAfter": {"Select_" + name: ["Succeeded"]}, "inputs": {"from": "@body('Select_" + name + "')", "format": "HTML"}}
    actions["Report"] = {"type": "Compose", "runAfter": {"Table_users": ["Succeeded"], "Table_summary": ["Succeeded"]}, "inputs": "@concat('<html><body><h1>editor8 · Wochenbericht</h1><p>Zeitraum: ',formatDateTime(addDays(utcNow(),-7),'yyyy-MM-dd HH:mm'),' bis ',formatDateTime(utcNow(),'yyyy-MM-dd HH:mm'),' UTC.</p><p>Gezählte App-Ereignisse; keine Aussage über Arbeitsdauer oder fachliche Freigabe. Die Aufzeichnung beginnt mit der Auslieferung dieser Funktion. Fehlende Ereignisse vor diesem Beginn sind keine Nullnutzung.</p>',body('Table_summary'),'<h2>Nutzung je Konto und Datenbestand</h2>',body('Table_users'),'<p>Nicht zugeordnet: abgewiesene Zugriffe oder Ereignisse ohne bestätigte Kontokennung. Öffnungen zählen erfolgreiche Abrufe; gespeicherte Änderungen zählen nur tatsächlich geänderte Entwürfe. Die Aufzeichnung seit-Angabe bezieht sich auf die im 30-Tage-Protokoll noch vorhandenen Ereignisse.</p></body></html>')"}
    actions["Mail"] = {"type": "If", "runAfter": {"Report": ["Succeeded"]}, "expression": "@equals(parameters('sendMail'),true)", "actions": {
        "Send_email": {"type": "ApiConnection", "runAfter": {}, "inputs": {
            "host": {"connection": {"name": "@parameters('$connections')['office365']['connectionId']"}},
            "method": "post", "path": "/v2/Mail",
            "body": {"To": "@parameters('recipient')", "Subject": "@concat('editor8 · Wochenbericht · ',formatDateTime(utcNow(),'yyyy-MM-dd'))", "Body": "@outputs('Report')", "Importance": "Normal"},
        }},
    }, "else": {"actions": {"Mail_pending": {"type": "Compose", "runAfter": {}, "inputs": "Bericht erstellt. E-Mail-Versand wartet auf eine bestätigte Outlook-Verbindung und Aktivierung."}}}}
    return {
        "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
        "contentVersion": "1.0.0.0", "parameters": {"$connections": {"type": "Object"}, "workspaceId": {"type": "String"}, "recipient": {"type": "String"}, "sendMail": {"type": "Bool"}},
        "triggers": {"Weekly": {"type": "Recurrence", "recurrence": {"frequency": "Week", "interval": 1, "timeZone": "W. Europe Standard Time", "schedule": {"weekDays": ["Monday"], "hours": [8], "minutes": [0]}}}},
        "actions": actions, "outputs": {},
    }


def template():
    workflow_id = "resourceId('Microsoft.Logic/workflows', '" + WORKFLOW + "')"
    connection_id = "resourceId('Microsoft.Web/connections', '" + CONNECTION + "')"
    api_id = "concat(subscription().id, '/providers/Microsoft.Web/locations/" + LOCATION + "/managedApis/office365')"
    return {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#", "contentVersion": "1.0.0.0",
        "parameters": {"workspaceId": {"type": "string"}, "workspaceResourceId": {"type": "string"}, "recipient": {"type": "string", "defaultValue": "ofunk@funktion8.de"}, "sendMail": {"type": "bool", "defaultValue": False}, "createConnection": {"type": "bool", "defaultValue": True}},
        "resources": [
            {"type": "Microsoft.Web/connections", "apiVersion": "2016-06-01", "name": CONNECTION, "location": LOCATION, "condition": "[parameters('createConnection')]", "properties": {"displayName": "editor8-Berichtsversand", "api": {"id": "[" + api_id + "]"}}},
            {"type": "Microsoft.Logic/workflows", "apiVersion": "2019-05-01", "name": WORKFLOW, "location": LOCATION, "identity": {"type": "SystemAssigned"}, "dependsOn": ["[" + connection_id + "]"], "properties": {
                "state": "Enabled", "definition": definition(), "parameters": {
                    "workspaceId": {"value": "[parameters('workspaceId')]"}, "recipient": {"value": "[parameters('recipient')]"}, "sendMail": {"value": "[parameters('sendMail')]"},
                    "$connections": {"value": {"office365": {"id": "[" + api_id + "]", "connectionId": "[" + connection_id + "]", "connectionName": CONNECTION}}},
                },
            }},
            {"type": "Microsoft.Authorization/roleAssignments", "apiVersion": "2022-04-01", "name": "[guid(" + workflow_id + ", parameters('workspaceResourceId'), 'usage-reader')]", "scope": "[parameters('workspaceResourceId')]", "dependsOn": ["[" + workflow_id + "]"], "properties": {"roleDefinitionId": "[subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '" + READER_ROLE + "')]", "principalId": "[reference(" + workflow_id + ", '2019-05-01', 'Full').identity.principalId]", "principalType": "ServicePrincipal"}},
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--send-mail", action="store_true", help="Only after verifying the Outlook account in Azure")
    parser.add_argument("--export", type=Path, help="Write the ARM template without changing Azure")
    args = parser.parse_args()
    if args.export:
        args.export.parent.mkdir(parents=True, exist_ok=True)
        args.export.write_text(json.dumps(template(), ensure_ascii=False, indent=2), encoding="utf-8")
        return
    az = shutil.which("az")
    if not az:
        raise SystemExit("Azure CLI is required; use its existing authenticated session.")
    def call(*arguments, optional=False):
        result = subprocess.run([az, *arguments, "-o", "json"], capture_output=True, text=True, encoding="utf-8")
        if result.returncode:
            if optional and "ResourceNotFound" in result.stderr:
                return None
            raise SystemExit("Azure request failed. No credentials were requested or changed.")
        return json.loads(result.stdout) if result.stdout.strip() else {}
    account = call("account", "show", "--query", "{id:id,tenant:tenantId}")
    if account["tenant"] != "870c862b-56f7-4c9b-b0d9-f1f7d32c835c":
        raise SystemExit("The current Azure session is not the f8 tenant.")
    workspace = call("monitor", "log-analytics", "workspace", "show", "--resource-group", GROUP, "--workspace-name", "law-nac-ontology-editor", "--query", "{id:id,customerId:customerId}")
    connection_uri = f"https://management.azure.com/subscriptions/{account['id']}/resourceGroups/{GROUP}/providers/Microsoft.Web/connections/{CONNECTION}?api-version=2016-06-01"
    connection = call("rest", "--method", "get", "--url", connection_uri, optional=True)
    if args.send_mail and (not connection or not any(item.get("status") == "Connected" for item in connection.get("properties", {}).get("statuses", []))):
        raise SystemExit("Authorize the editor8-report-outlook connection in Azure before enabling email.")
    with tempfile.TemporaryDirectory(prefix="editor8-report-") as directory:
        path = Path(directory) / "template.json"
        path.write_text(json.dumps(template(), ensure_ascii=True), encoding="utf-8")
        result = call("deployment", "group", "create", "--resource-group", GROUP, "--name", "editor8-usage-report", "--template-file", str(path), "--parameters", f"workspaceId={workspace['customerId']}", f"workspaceResourceId={workspace['id']}", "sendMail=" + str(args.send_mail).lower(), "createConnection=" + str(connection is None).lower(), "--query", "{state:properties.provisioningState}")
    print(json.dumps({"workflow": WORKFLOW, "mailEnabled": args.send_mail, "deployment": result}))


if __name__ == "__main__":
    main()

# HTTPS für www.ontologie8.de

Stand: 03.10.2026. Der Betreiber hat die DNS-Einträge gesetzt; sie wurden per DNS-Abfrage geprüft. Azure hat ein verwaltetes Zertifikat erfolgreich ausgestellt und die Domain mit `SniEnabled` an die bestehende Container App gebunden. Der Webfilter des lokalen Prüfcomputers liefert für die neue Domain eine Sperrseite; diese HTTP-200-Antwort ist ausdrücklich kein App-Gesundheitsnachweis.

| Eintrag | Wert |
| --- | --- |
| CNAME `www` | `ca-nac-ontology-editor.salmonsmoke-565866ed.germanywestcentral.azurecontainerapps.io` |
| TXT `asuid.www` | `61BEB130DB7C77B3185EFCF46114AD8B997F95FCD62AB443CFADE6FC6C8CBC04` |
| Azure-App / Ressourcengruppe | `ca-nac-ontology-editor` / `rg-nac-ontology-editor` |
| Umgebung | `cae-nac-ontology-editor` |
| Zertifikat | `mc-cae-nac-ontolo-www-ontologie8-d-4802` |

Das TXT ist ein öffentlicher Domainbestätigungswert, kein Zugangsschlüssel. [Microsoft dokumentiert die automatische Verlängerung](https://learn.microsoft.com/en-us/azure/container-apps/custom-domains-managed-certificates). Der CNAME muss direkt zur App zeigen. Falls CAA-Einträge existieren, muss DigiCert als Aussteller erlaubt sein. Die Domain ohne `www` ist damit nicht eingerichtet.

## Anmeldestand und Prüfung

Der Betreiber bestätigte den zusätzlichen Redirect-URI-Eintrag am 03.10.2026. `PUBLIC_ORIGIN` ist auf `https://www.ontologie8.de` umgestellt. Die dadurch erzeugte Revision `ca-nac-ontology-editor--0000015` war aktiv und gesund, mit 100 Prozent Verkehr auf der neuesten Revision und unverändertem Softwareimage `2a02ec7c7a426176db60b6ccfe076e9e84f41b44`. Das ist der Nachweis der Konfigurationsumstellung; spätere Softwaredeployments erzeugen eigene Revisionen.

Die folgende Folge dient der Wiederholung. Der Deployment-Workflow prüft jetzt die neue Domain, ihre tatsächliche JSON-Gesundheitsantwort, Release, Asset-Hashes und die neue Redirect-URI. Eine echte angemeldete Sitzung bleibt ein separater Nachweis.

1. Auf der [GitHub-App-Einstellungsseite](https://github.com/organizations/notariat8/settings/apps/nac-ontology-editor-notariat8) unter **Identifying and authorizing users → Add redirect URI** zusätzlich `https://www.ontologie8.de/callback` eintragen. **Allow wildcard matching** bleibt aus; die bisherige Azure-Adresse erhalten. Mit **Save changes** unterhalb von SSL verification speichern. Die aktuelle Oberfläche nennt die Callback-Adresse „Redirect URI“. [GitHub-Anleitung](https://docs.github.com/en/apps/maintaining-github-apps/modifying-a-github-app-registration).
2. Erst nach bestätigtem Eintrag `PUBLIC_ORIGIN` der Azure-App auf `https://www.ontologie8.de` setzen. Das erzeugt eine neue Revision; laufende Sitzungen enden.
3. Neue Revision, Image, Release-Kennung und Assets prüfen. `/login` muss die neue Callback-Adresse verwenden. Der Redirect allein bestätigt nicht, dass GitHub sie akzeptiert.
4. Eine echte Anmeldung unter der neuen Domain prüfen. Bestehende Nutzer- und Notarrechte getrennt prüfen; Domain und Zertifikat ändern diese Rechte nicht.

Die vorhandenen Werkzeuge bedienen Azure und GitHub-Repositories, jedoch nicht die angemeldete GitHub-App-Einstellungsseite. Der Betreiber hat deren Eintrag selbst vorgenommen. Neue Secrets oder eine neue App waren nicht erforderlich.

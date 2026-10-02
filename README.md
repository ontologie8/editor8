# editor8

SaaS-Editor für versionierte Fachmodelle: Oberfläche, Python-API, GitHub-Anmeldung und kontrollierte Änderungsvorschläge.

**Software und Daten sind getrennt:** Dieses Repository enthält den Editor. [notariat8/ontology](https://github.com/notariat8/ontology) pflegt die Notar-Fachmodelle; [NaC](https://github.com/notariat8/NaC) pflegt die führenden Prozessabläufe. Der aktuelle Datenadapter unterstützt das NaC-RDF-Schema; weitere Schemata benötigen eigene Adapter. Die 20-Fall-Grenze liegt im Notardatensatz, nicht im Editor-Code.

## Bedienung

Die Desktop-Oberfläche folgt der freigegebenen Office-Struktur: außen **Verstehen, Bearbeiten, Prüfen**, daneben das Datenrepository mit seinem Baum und in der Mitte der Arbeitsbereich. Beim Bearbeiten bleibt der Graph sichtbar; Details und Formular stehen rechts. **Datei, Startseite, Ansicht und Hilfe** liegen oben. Das Menüband lässt sich mit seinem Pfeil oder **Strg+F1** einklappen und durch Anklicken einer Registerkarte vorübergehend öffnen. Das Hamburger-Menü schaltet den Datenbaum unabhängig davon um.

**Öffnen, Speichern und Drucken** stehen unter Datei. Speichern zeigt zunächst den Vergleich und verlangt die Bestätigung der Änderung im Datenentwurf. Die allgemeine Hilfe steht oben; das Fragezeichen am ausgewählten Baustein erläutert dessen Kontext. Menüs und Datenrepository-Auswahl bleiben erreichbar, während Baum und Arbeitsinhalt bei Bedarf innerhalb ihrer Bereiche scrollen. [DESIGN.md](DESIGN.md) hält die Maße und Microsoft-Referenzen fest.

## Lokal starten

Python 3.12 oder neuer, Git und ein separater Datencheckout werden benötigt.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:EDITOR8_DATA_ROOT = 'C:\Users\ofunk\srv\github\ofunk\notariat8\ontology'
.\.venv\Scripts\python.exe scripts/case_editor.py
```

Der Server öffnet `http://127.0.0.1:8765/`. Er liest und bearbeitet ausschließlich den ausdrücklich angegebenen Datencheckout. Für lokale Änderungsvorschläge verwendet er dessen Branch, Validatoren, Git-Push und Pull Requests. Die Cloudvariante benötigt auf Nutzergeräten weder Python noch Git.

## Cloudbetrieb

Die App zeigt den ausgelieferten Softwarecommit als „Editor-Release“ mit einem direkten GitHub-Link. Die Liste auswählbarer Datenziele liegt in `config/data-repositories.json`. [Datenrepositories und Benutzer](docs/data-repositories-and-users.md) beschreibt Auswahl, Nutzerzulassung und notarielle Rollen.

```powershell
python scripts/cloud_editor.py
```

Der Container startet diesen Server. `GITHUB_REPOSITORY` bezeichnet das Datenrepository, etwa `notariat8/ontology`, niemals `ontologie8/editor8`. GitHub-App-Zugang, erlaubte Nutzer, Reviewer und HTTPS-Ursprung werden im Host konfiguriert. [Datenvertrag](docs/data-contract.md), [Betrieb](docs/editor-hosting.md), [Produktstand](docs/editor-produktstand.md) und [Migration](docs/migration.md) erklären Voraussetzungen und Prüfgrenzen. Secrets ausschließlich im Host speichern.

## Prüfen

```powershell
python -m unittest discover -s tests -q
node --check editor/app.js
npm ci
npx playwright install chromium --only-shell
npm run test:browser
```

Diese Tests verwenden ausschließlich synthetische Beispiele und einen lokalen GitHub-Ersatz. Zusätzlich kann der bestehende 20-Fall-Regressionssatz mit einem getrennten Datencheckout ausgeführt werden:

```powershell
$env:EDITOR8_DATA_ROOT = '<separater-ontology-checkout>'
python -m unittest discover -s tests/integration -q
$env:NAC_TEST_PYTHON = (Resolve-Path .\.venv\Scripts\python.exe).Path
npm run test:integration:browser
```

Die Integration verändert keine echten GitHub-Daten. Sie läuft zusätzlich bei Datenänderungen, täglich und manuell im privaten Datenrepository; [Datenintegration in CI](docs/editor-integration-ci.md) beschreibt die getrennten Checkouts und die Wiederholung mit vollständigen Editor-/Datencommits. Ein produktiver OAuth-/Schreib-/PR-Durchlauf und die notarielle Fachprüfung sind eigene Abnahmen.

## Lizenz

Code: AGPL-3.0-or-later; Dokumentation: CC-BY-4.0. Siehe [Lizenzzuordnung](LICENSES/README.md) und [Herkunft](NOTICE). Keine Aktenwerte, privaten Fachmodelle oder Zugangsdaten sind im Softwareprojekt enthalten.

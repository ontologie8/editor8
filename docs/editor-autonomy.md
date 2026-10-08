# Eigenständigkeit und Betriebszugänge

Geprüft am 01.10.2026 gegen editor8-Commit `e6f2354f7aa74a751694762135a28e1ba885caf1`.

## Verantwortung

editor8 enthält die Oberfläche, API, GitHub-Anmeldung, Datenadapter, Entwicklungsprüfungen, Container und Deployment-Workflow. Diese Software wird ausschließlich hier weiterentwickelt. Der alte Softwarezweig in ontology ist keine Laufzeitquelle und kein Secret-Speicher für editor8.

notariat8/ontology bleibt das ausdrücklich konfigurierte Datenziel für die Notar-Fachmodelle. NaC bleibt Quelle der Prozessabläufe. Die fachlichen Inhalte und deren Freigaben werden nicht in das Softwareprojekt übertragen.

## Entwicklung ohne alten Checkout

Die lokale virtuelle Python-Umgebung und die Node-Abhängigkeiten liegen in editor8. Sie können aus requirements.txt und package-lock.json neu installiert werden. `python -m unittest discover -s tests -q` bestand mit sieben Tests; die JavaScript-Syntaxprüfung und `npm run test:browser` mit zwei Browserprüfungen bestanden ebenfalls. Für den Browserlauf wurde die Python-Umgebung dieses Repositorys über `NAC_TEST_PYTHON` ausgewählt.

Die Tests erzeugen einen künstlichen Datensatz außerhalb des Softwareverzeichnisses und verwenden einen lokalen GitHub-Ersatz. Geprüft wurden unter anderem das Öffnen zweier Fälle, Graphdarstellung, Suchindex und Beginn eines Arbeitszweigs. Kein ontology-Checkout, produktives OAuth-Secret oder reales GitHub-Schreiben war dafür erforderlich. Diese Prüfung ersetzt keinen angemeldeten produktiven Schreib-/PR-Durchlauf.

## Produktiver Betrieb

- Azure verwendet das Softwareimage des oben genannten editor8-Commits; die bereite Revision wurde live abgefragt.
- Im Software-Repository sind die erforderlichen Deployment-Einstellungen vorhanden. Azure-Anmeldung erfolgt über die OIDC-Identität des main-Branches; ein Azure-Client-Secret ist dafür nicht erforderlich.
- Das GitHub-App-Client-Secret ist direkt aus Azure Key Vault eingebunden; der Zugriff verwendet die Systemidentität der Container App.
- Das GitHub-App-Secret wird weder aus einem Git-Checkout geladen noch für normale Softwareentwicklung lokal benötigt. Bei der Prüfung wurden ausschließlich Secret-Namen und Referenzen gelesen, keine Secret-Werte.
- Der Software-, Container- und Deploy-Job des [Prüflaufs](https://github.com/ontologie8/editor8/actions/runs/36890101937) waren erfolgreich. Azure-Konfiguration und Image wurden zusätzlich live abgefragt.

Die Azure-Ressourcen und die GitHub App behalten ihre bisherigen Namen. Diese Namen sind keine Abhängigkeit von einem alten Softwarecheckout. App-Installation und Rechte auf dem ausdrücklich gewählten Datenrepository sind für echte Fachmodellzugriffe weiterhin erforderlich.

## Grenze des lokalen Offlinebetriebs

`scripts/case_editor.py` bearbeitet den über `EDITOR8_DATA_ROOT` angegebenen separaten Datencheckout. Beim Einreichen echter lokaler Änderungen ruft dieser Weg dessen `validate_catalog.py`, `validate_cases.py` und `render_case_docs.py --check` auf und nutzt dessen Git-Remote. Das ist eine ausdrückliche Integration mit den fachlichen Prüfregeln des Datensatzes. Dieser Offline-PR-Weg ist daher kein vom Datencheckout unabhängiger Betrieb.

Der produktive Cloudserver sowie die synthetischen Softwareprüfungen benötigen diese externen Prüfscripte nicht. Für lokale produktive OAuth-Anmeldung müssten die Hostkonfiguration und eine zulässige Callback-Adresse separat eingerichtet werden; das ist kein Abruf von Secrets aus dem alten Repository.

Noch offen bleiben der produktive Bearbeitungs-/PR-Durchlauf und die notarielle Fachprüfung mit einem zweiten Konto. Die technischen Nachweise erteilen keine fachliche Freigabe.

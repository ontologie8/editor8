# editor8: SaaS-Editor

- Dieses Repository enthält Oberfläche, Server, Anmeldung, Datenadapter, Tests und Betrieb des Editors.
- Führende Notar-Fachmodelle liegen ausschließlich in `notariat8/ontology`; NaC bleibt Quelle für Prozessabläufe und Usecase-IDs. Keine Fachmodelle, Aktenwerte oder Secrets hier speichern.
- Datenziele ausdrücklich konfigurieren: `GITHUB_REPOSITORY` für den Cloudbetrieb, `EDITOR8_DATA_ROOT` für lokale Entwicklung. Dieses Software-Repository darf kein Datenziel sein.
- Der NaC-Adapter übernimmt die IDs des Datenkatalogs unverändert. Die 20-Fall-Grenze gehört zum Notardatenprojekt; der Editor hat keine fest codierte Fallanzahl.
- Änderungen an Software und Daten in getrennten Arbeitsverzeichnissen prüfen, committen und synchronisieren. Repositoryübergreifende Arbeit ist erlaubt, wenn der Nutzer sie beauftragt. Nachrichten an andere Codex-Chats benötigen seine ausdrückliche Beauftragung.
- Vor Lieferung: Python-Tests, JavaScript-Syntax und synthetische Browserprüfung. Datenintegration zusätzlich mit einem ausdrücklich angegebenen separaten Checkout testen.
- Ein Build ist erst abgeschlossen, wenn das Image erfolgreich auf Azure bereitgestellt ist, die aktive Revision gesund ist und die laufende App die Release-Kennung des erwarteten editor8-Commits ausliefert. Lokaler Build, grüne CI oder ein offener PR allein sind kein Abschluss. Fehlt eine notwendige Berechtigung oder Fähigkeit, den Build ausdrücklich als unvollständig melden und den konkreten Blocker nennen.
- Bestehende globale Windows-Hello- und Authentifizierungsregeln gelten unverändert. App-Rechte, Hosting oder Datenfreigaben nicht aus einem Softwaretest ableiten.
- Code: AGPL-3.0-or-later; übernommene Dokumentation: CC-BY-4.0. Herkunft in NOTICE erhalten.

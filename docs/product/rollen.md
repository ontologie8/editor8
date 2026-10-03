# Zugriff und Betrieb

Die Anmeldung identifiziert den GitHub-Benutzer. Der Host erlaubt Benutzer über EDITOR_USERS. Das Datenrepository benötigt Read zum Lesen und Write zum Erstellen von Änderungen. Der GitHub-App-Benutzertoken ist auf die gemeinsamen Rechte von App und Benutzer beschränkt.

Die Reviewer-Rolle erlaubt fachliche Freigaben einer anderen Person; die Maintainer-Rolle erlaubt gemeinsame Begriffe. Rollen erteilen keine GitHub-Rechte. Weitere Datenziele brauchen Registry-Eintrag, App-Installation, Benutzerzugriff und passenden Adapter.

Der Editor läuft auf Azure. Secrets bleiben im Host. Lokale Entwicklung verlangt einen ausdrücklich separaten EDITOR8_DATA_ROOT. Die öffentliche Software-CI verwendet künstliche Daten; die Integration mit privaten Fachmodellen läuft im privaten Datenrepository.

Ein Softwarebuild endet erst mit dem erwarteten Azure-Image, aktiver gesunder Revision und passender Release-Kennung. Konfiguration und Betriebsanleitung stehen in docs/editor-hosting.md und docs/data-repositories-and-users.md.

## Referenz

| Begriff oder Meldung | Erläuterung |
| --- | --- |
| Leser | Zugelassenes GitHub-Konto mit Lesezugriff am Datenziel. |
| Bearbeitende | Zusätzlicher GitHub-Schreibzugriff für Entwürfe und PRs. |
| Notarielle Reviewer | Zusätzliche fachliche Rolle; keine Selbstfreigabe. |
| Ontology-Maintainer | Zusätzliche Rolle für das gemeinsame Vokabular. |

[Zur Übersicht](README.md) · [Training](../../training/README.md)

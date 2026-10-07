# Nutzer und Notare zulassen

Stand: 07.10.2026. Diese Betriebsanleitung richtet sich an den Betreiber. Fachliche Nutzer pflegen Modelle in getrennten Datenrepositories; sie entwickeln die Editorsoftware nicht.

## Vier getrennte Freigaben

1. **GitHub-Anwendung autorisieren:** Die bestehende öffentliche App **Ontologie8 Editor** (`ontologie8-editor`) gehört seit der bestätigten Übertragung am 07.10.2026 dem Editorbetreiber `ontologie8`. Ihre Installation für Fachmodelle liegt getrennt beim Datenbetreiber `notariat8`. Eine private organisationsgebundene GitHub-App kann nur von Organisationsmitgliedern autorisiert werden; externe Mitarbeiter können dabei bereits vor dem Callback scheitern. Deshalb wurde die App am 06.10.2026 öffentlich registriert. Öffentliche Registrierung und Eigentumsübertragung erteilen keine Repository-Rechte oder Editor-Zulassung. Details: [App-Eigentum und Dateninstallation](github-app-ownership.md).
2. **Fachmodellbestand lesen und bearbeiten:** Der Nutzer benötigt Zugriff auf das gewählte Datenrepository; für Modelländerungen Schreibrechte. Leserechte am Software-Repository sind für die fachliche Arbeit ausreichend und schalten die App-Anmeldung nicht frei.
3. **Im Editor anmelden:** `EDITOR_USERS` in Azure enthält die zugelassenen GitHub-Benutzernamen. Einen Nutzer ergänzen und vorhandene Einträge erhalten. Diese Einstellung allein ersetzt weder GitHub-Zugriff noch die App-Autorisierung.
4. **Notariell prüfen:** Die Liste `notary_reviewers` beim jeweiligen Datenziel in `config/data-repositories.json` steuert die fachliche Freigabe. Diese Liste überschreibt für dieses Ziel die globale Ersatzliste `NOTARY_REVIEWERS`. `ONTOLOGY_MAINTAINERS` ist eine getrennte Berechtigung zur Pflege gemeinsamer Begriffe und wird nicht automatisch mit einer Notarrolle vergeben. Eigene Änderungen lassen sich weiterhin nicht selbst freigeben.

Bei neuen Konten alle vier Ebenen prüfen. Die App muss auf dem Datenrepository installiert sein und die vorgesehenen Rechte besitzen. Eine öffentliche App-Registrierung macht Fachmodelle nicht öffentlich; die bestehende Installation bleibt auf ausdrücklich ausgewählte Repositories begrenzt.

## Umstellung der App-Registrierung

Die [App-Einstellungen beim Editorbetreiber](https://github.com/organizations/ontologie8/settings/apps/ontologie8-editor) verwenden. Unter **Advanced → Danger zone** die öffentliche Sichtbarkeit kontrollieren; die bereits erfolgte Umstellung nicht erneut ausführen. Callback, App-Geheimnisse und Repository-Auswahl bleiben eigenständige Einstellungen. Die [öffentliche App-Seite](https://github.com/apps/ontologie8-editor) und einen neuen Anmeldeversuch über `https://www.ontologie8.de/login` prüfen. Alte Anmeldeverknüpfungen nicht weiterreichen oder wiederverwenden. Beim erneuten Umbenennen die tatsächlich von GitHub gemeldete Kennung und diese Links aktualisieren.

Bei der Diagnose am 06.10.2026 war die App privat. `jjwarzecha` war externer Mitarbeiter mit Schreiben auf `notariat8/ontology` und Lesen auf `ontologie8/editor8`; Editor-Zulassung und Notarrolle fehlten zusätzlich. Nach der vom Betreiber bestätigten Umstellung zeigte die öffentliche App-Seite die Anwendung und keinen Hinweis auf eine private App mehr. Diese Korrektur ergänzt die beiden Editor-Freigaben. Eine erfolgreiche reale Anmeldung und Prüfung werden daraus nicht abgeleitet.

## Nachweise vor Abschluss

- GitHub-Rechte am konkreten Datenziel und Benutzername prüfen; angenommene Einladung von ausstehender Einladung unterscheiden.
- Azure-Nutzerzulassung und repositorybezogene Rollen prüfen, ohne Geheimnisse auszulesen oder weiterzugeben.
- Nach Rollenänderung eine neue Anmeldung beginnen; bestehende In-Memory-Sitzungen können bei einer neuen Azure-Revision enden.
- In der tatsächlichen Sitzung den sichtbaren Benutzer, gewählten Bestand und angebotene Tätigkeiten prüfen. Synthetische Tests prüfen die Rollenlogik, bestätigen keine reale notarielle Identität oder Fachfreigabe.

Quellen: [GitHub-App-Sichtbarkeit](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/making-a-github-app-public-or-private), [Registrierung ändern](https://docs.github.com/en/apps/maintaining-github-apps/modifying-a-github-app-registration#changing-the-visibility-of-a-github-app), [Autorisierung und Installation](https://docs.github.com/en/apps/using-github-apps/authorizing-github-apps).

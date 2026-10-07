# Benutzerverwaltung ohne Softwareauslieferung

Stand: 07.10.2026. Status: Nutzer bestätigt die getrennten Verantwortungen und Entra-Gruppen für den App-Zugang; externe Identitäten werden unten konkretisiert. Noch keine Umstellung des produktiven Identitätsanbieters. Neue Nutzer und geänderte Rollen dürfen weder einen Image-Build noch eine neue Container-Revision benötigen.

## Bestätigte Verantwortungen

| Freigabe | Führendes System | Verantwortlich |
| --- | --- | --- |
| Editor entwickeln | Schreib- und Verwaltungsrechte an `ontologie8/editor8` | Betreiber als Entwickler |
| Gehostete App nutzen | Ausdrückliche Zuweisung zur Entra-Unternehmensanwendung, beispielsweise über `editor8-nutzer` | Betreiber |
| Daten lesen oder bearbeiten | Rechte am jeweiligen GitHub-Datenrepository | Jeweiliger Repository-Verantwortlicher |
| Fachlich freigeben | Zusätzliche Fachprüferrolle für den jeweiligen Datenbestand | Fachlich Verantwortlicher |

Das öffentliche Software-Repository vermittelt keine Zulassung zur bezahlten Instanz. Fachanwender benötigen keine Azure-Verwaltungsrechte und keine Mitgliedschaft im Softwareprojekt. `notariat8/ontology` wurde am 07.10.2026 auf ausdrücklichen Nutzerauftrag öffentlich gestellt; GitHub aktiviert damit Forks. Das ändert keine App-Zulassung und keine Schreibrechte. Die Hauptzweig-Sperre bleibt auf Nutzerwunsch bis zur Wiedervorlage am 09.10.2026 unverändert. Der frühere Tarifblocker für Branch Protection im privaten Repository gilt für den jetzt öffentlichen Bestand nicht mehr.

## Externe Identitäten ohne internes funktion8-Konto

Im vorhandenen Mandanten mit Anzeigename `f8` und ID `870c862b-56f7-4c9b-b0d9-f1f7d32c835c` sind `funktion8.de` und `ontologie8.de` bestätigt und Entra P1 aktiv. Der Name steht unter Entra ID → Übersicht → Eigenschaften. `kontakt@ontologie8.de` ist für App-Kontakt und Nutzungsbericht beauftragt, `admin@ontologie8.de` für die Administration vorgesehen. Beide Adressen sind aktuell Aliasse desselben bestehenden Benutzerobjekts; Details und verbleibende Verwendungen der bisherigen Adresse stehen unter [Betreiberidentitäten](operator-identities.md). Die Zuweisung von Gruppen zu Unternehmensanwendungen ist grundsätzlich verfügbar; anwendbare Benutzer- und Gastlizenzen bei Einrichtung prüfen. Der Vorschlag braucht keine internen Mitarbeiterkonten für Notare:

- Eigenes Entra-Konto: als B2B-Gast einladen. Die Person authentifiziert sich beim eigenen Identitätsanbieter; das Gastobjekt im Ressourcenmandanten ermöglicht die ausdrückliche App- und Gruppenzuweisung.
- Kein Entra-Konto, aber GitHub-Konto: Gast über eine bestätigte Kontakt-E-Mail mit E-Mail-Einmalcode zulassen und das GitHub-Konto durch eine separate bestätigte Anmeldung für die Datenrechte verknüpfen. Ein neu angelegtes Microsoft-Konto ist dafür nicht erforderlich.
- `Guest` ist ein Kontotyp, keine Schreib- oder Fachprüferrolle. Ein vorhandenes Gastobjekt allein erhält keinen App-Zugang. `editor8-nutzer` erlaubt nur die App; GitHub-Rechte und bestandsbezogene Fachrollen werden separat geprüft.

GitHub ist kein direkt aufgeführter B2B-Identitätsanbieter des bestehenden Workforce-Mandanten. Eine ausschließlich auf GitHub-Anmeldung beruhende Zulassung wäre ein eigener GitHub-Weg mit separat verwalteter Zugangsliste; sie darf nicht als bereits vorhandene Entra-Gruppenfreigabe dargestellt werden. Die endgültige externe Anmeldeerfahrung bleibt zu bestätigen; diese Dokumentation richtet noch keine Unternehmensanwendung, Gruppe oder Einladung ein.

Quellen: [B2B-Identitätsanbieter](https://learn.microsoft.com/en-us/entra/external-id/identity-providers), [E-Mail-Einmalcode](https://learn.microsoft.com/en-us/entra/external-id/one-time-passcode), [Gruppenzuweisung](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/assign-user-or-group-access-portal).

## Aktueller Befund

GitHub identifiziert den Nutzer. `EDITOR_USERS` schränkt die Anmeldung zusätzlich ein; die Azure-Einstellung wird beim Start gelesen. Ihre Änderung erzeugt eine Container-Revision mit demselben Image, keinen Image-Build. Weil die Sitzungen nur im Prozess liegen, können sie bei einer neuen Revision enden. Microsoft beschreibt die revisionsgebundene Änderung von [Umgebungsvariablen](https://learn.microsoft.com/en-us/azure/container-apps/environment-variables).

Die fachlichen Listen `notary_reviewers` und `ontology_maintainers` stehen derzeit in `config/data-repositories.json`. Der Dockerbuild kopiert diese Datei in das Image. Änderungen dieser Listen benötigen daher eine Softwareauslieferung. GitHub-Datenrechte werden bereits mit dem Benutzertoken geprüft. Die zusätzlichen statischen Listen sind eine Pilotlösung und kein geeignetes Ziel für die laufende Benutzerverwaltung.

## Aufgaben trennen

- **Identität:** Wer meldet sich an? Stabile Anbieterkennung verwenden, beispielsweise GitHub-Benutzer-ID oder Entra-Mandant und Objekt-ID. Anzeigenamen sind keine unveränderlichen Identitäten.
- **Zugang und fachliche Rollen:** Wer darf den Editor nutzen, einen bestimmten Bestand bearbeiten, fachlich prüfen oder gemeinsame Begriffe pflegen? Rollen und Bestandszuordnung außerhalb des Images verwalten. Schreibzugriff allein begründet keine Notarrolle.
- **Datenzugriff:** GitHub bleibt die versionierte Datenquelle. Datenrechte bleiben wirksam und werden durch eine Anmeldung bei Entra nicht automatisch erteilt.
- **Betrieb:** Ein neues Software-Release ändert Software. Das Einladen, Sperren oder Umstufen einer Person ist Benutzerverwaltung.

## Zwei umsetzbare Wege

| Weg | Benutzerverwaltung | Folge für den Editor |
| --- | --- | --- |
| GitHub weiter nutzen | Anmeldung und Datenrechte über GitHub; fachliche Gruppen über GitHub-Teams, wenn die Personen Organisationsmitglieder sind. Externe Repository-Mitarbeiter können nicht in Teams aufgenommen werden; sie benötigen eine gesonderte zentrale Rollenzuordnung. | Bestehenden GitHub-OAuth-Weg erhalten, statische Personenlisten durch zur Laufzeit ausgewertete Berechtigungen ersetzen. Vor einer Aufnahme in die Organisation deren Basisrechte prüfen. |
| Entra ID nutzen | Zugang und fachliche Rollen über die Unternehmensanwendung; externe Notare als B2B-Gäste oder bei einem späteren Kundenprodukt über einen dafür vorgesehenen External-ID-Mandanten. | OpenID-Connect-Anmeldung und Rollenprüfung ergänzen. GitHub-Datenzugriff und die Zuordnung von Änderungsautor und Fachprüfer ausdrücklich weiterführen. |

GitHub dokumentiert die [Teamgrenze für externe Mitarbeiter](https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-outside-collaborators/adding-outside-collaborators-to-repositories-in-your-organization). Ein GitHub-App-Benutzertoken erhält nur die Schnittmenge aus [App- und Benutzerrechten](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app).

Entra unterstützt [B2B-Gäste](https://learn.microsoft.com/en-us/entra/external-id/add-users-administrator) und [Anwendungsrollen in Anmeldetokens](https://learn.microsoft.com/en-us/entra/identity-platform/howto-add-app-roles-in-apps). Stabile Tätigkeitsrollen werden einmal definiert; konkrete Nutzerzuweisungen werden zentral gepflegt. Bestandsbezogene Berechtigungen brauchen zusätzlich eine eindeutige Zuordnung. Rollen sind beim nächsten Token beziehungsweise der nächsten Berechtigungsprüfung wirksam; ein Entzug muss für bestehende Sitzungen ausdrücklich umgesetzt und geprüft werden.

## Empfehlung und Migration

Für einen Fachanwenderkreis mit externen Notaren ist Entra ID als zentrale Benutzer- und Rollenverwaltung das empfohlene Ziel. GitHub bleibt dabei die Datenquelle. Ein reiner GitHub-Weg ist eine kleinere Alternative, wenn alle Nutzer dauerhaft GitHub-Konten verwenden sollen und die fachliche Rollenverwaltung verbindlich geklärt ist.

1. Identitätsanbieter, verantwortlichen Mandanten und Bestandsgrenzen entscheiden. Bei Entra den vorhandenen geeigneten Mandanten, die erforderlichen Verwaltungsrechte und die anwendbaren Lizenzen prüfen; aus Azure-Hosting allein folgt keine Entra-Verwaltungsberechtigung.
2. Die Rollen Leser, Ontologiepfleger, notarieller Fachprüfer und Pflege gemeinsamer Begriffe zentral definieren. Repository- oder Bestandszuordnung getrennt abbilden. Keine automatischen Notarrechte aus GitHub `Write` ableiten.
3. Zunächst Entra-Zugang mit einem ausdrücklich verknüpften GitHub-Konto kombinieren. Damit bleiben die bestehenden Benutzerrechte für GitHub-Schreibvorgänge erhalten. Konten nur nach nachgewiesener Anmeldung bei beiden Anbietern verknüpfen, nicht anhand gleicher E-Mail-Adressen.
4. Wenn Fachanwender später kein GitHub-Konto benötigen sollen, GitHub-Zugriffe über die eng begrenzte App-Installation ausführen. Das ist ein eigener Umbau: Autorenzuordnung, Prüfidentität, Verbot der eigenen Fachfreigabe und nachvollziehbare Reviews müssen auch bei einem gemeinsamen technischen GitHub-Absender erhalten bleiben.
5. Statische Personenlisten aus Azure und dem Image entfernen, sobald die zentrale Berechtigungsprüfung aktiv und geprüft ist. Berechtigungen bei Anmeldung und geschützten Aktionen prüfen; Änderungen mit begrenzter Zwischenspeicherung übernehmen. Ausfall oder unklare Zuordnung dürfen keine zusätzlichen Rechte eröffnen.

## Abnahme

Eine neue künstliche Testperson wird zentral eingeladen und erhält einen Bestand sowie eine Rolle. Sie kann sich ohne neuen Build und ohne neue Azure-Revision anmelden. Eine Rollenänderung und ein Entzug wirken innerhalb des dokumentierten Zeitfensters auch auf bestehende Sitzungen. Unberechtigte Bestände bleiben gesperrt. Dieselbe natürliche Person darf unter unterschiedlichen Konten keine eigene Änderung fachlich freigeben. Erst anschließend den Weg mit einem tatsächlich eingeladenen Fachanwender bestätigen.

Die Zulassung von `jjwarzecha` mit der bisherigen Konfiguration behebt den aktuellen Zugang; sie ist kein Nachweis dieser noch ausstehenden IAM-Migration.

# Entra-Zulassung und persönliche GitHub-Datenrechte

Stand: 07.10.2026. Die Software ist implementiert; Einrichtung und Aktivierung in der Cloud sind getrennte Schritte. Der geprüfte Einrichtungsumfang steht in [infra/iam-plan.json](../infra/iam-plan.json). Dieser Plan enthält keine externen Einladungen und aktiviert den neuen Zugang noch nicht. Eine automatische Freigabeprüfung hat den ersten gebündelten Einrichtungsversuch vor Ausführung abgewiesen. Das ist kein Nachweis fehlender Entra-Verwaltungsrechte.

## Vier Verantwortungen

| Aufgabe | Maßgebliche Freigabe |
| --- | --- |
| Editor entwickeln | GitHub-Rechte an `ontologie8/editor8` |
| Bezahlte App nutzen | Entra-Unternehmensanwendung mit Zuweisung erforderlich, Rolle `App.Use`, Gruppe `editor8-nutzer` |
| Bestand bearbeiten | Bestandsbezogene Entra-Pflegergruppe und persönliche GitHub-Schreibrechte am Datenrepository |
| Fachlich freigeben | Bestandsbezogene Entra-Fachprüfergruppe, GitHub-Schreibrechte und eine andere verknüpfte Autorenidentität |

Die Übernahme geprüfter Änderungen ist eine weitere Tätigkeit innerhalb des Datenbestands. Sie vermittelt keine Azure-Verwaltungsrechte. Der Betreiber erhält beim Bootstrap App-Zugang, Lesen, Pflegen, Pflege gemeinsamer Begriffe und Übernehmen. Er wird dadurch nicht zum notariellen Fachprüfer.

## Anmeldung für Fachanwender

1. Anmeldung im Editor beginnen. Entra prüft das ausdrücklich zugewiesene interne oder eingeladene Gastkonto im Ressourcenmandanten `f8` (`870c862b-56f7-4c9b-b0d9-f1f7d32c835c`). Ein Gastobjekt allein genügt nicht.
2. Persönliches GitHub-Konto bestätigen. Die Editor-App muss auf den vorgesehenen Datenrepositories installiert sein. Der Benutzertoken hat die Schnittmenge aus App- und Benutzerrechten.
3. Nach erfolgreicher Anmeldung bei beiden Anbietern wird Entra-Mandant/Objekt-ID atomar und eindeutig mit der unveränderlichen GitHub-Benutzer-ID verknüpft. Gleiche E-Mail-Adressen oder Anzeigenamen begründen keine Verknüpfung. Das Ändern einer vorhandenen Zuordnung ist eine gesonderte Betreiberaufgabe.
4. Lesen, Bearbeiten, Speichern, Einreichen, Prüfen und Übernehmen erfolgen im Editor. GitHub speichert die versionierten Änderungen und Prüfentscheidungen im Hintergrund. Die Nutzer benötigen weder Software-Rechte noch Azure-Zugriff.

Externe Personen mit eigener Entra-Identität können als B2B-Gäste arbeiten. Für Personen ohne Entra-Konto ist ein Gastzugang über eine bestätigte Kontaktadresse und den im Mandanten zugelassenen Anmeldeweg vorgesehen, beispielsweise E-Mail-Einmalcode. Der tatsächliche Gastanmeldeweg und dessen Tenant-Richtlinien sind vor produktiver Aktivierung zu prüfen. Die Kontaktadressen für `hheise-ch` und `jjwarzecha` müssen vom Betreiber bestätigt werden. Keine Einladung und keine Identitätsverknüpfung wird aus einem GitHub-Namen abgeleitet.

## Bestände und Tätigkeiten zur Laufzeit

Die Azure-Tabelle `editor8access` enthält ausschließlich administrative Richtlinien, verifizierte Kontoverknüpfungen und Nachweise zu Prüfentscheidungen. Fachmodelle, Zugangstoken und Akteninhalte bleiben außerhalb dieser Tabelle. Die App greift mit ihrer Managed Identity zu; gemeinsame Storage-Schlüssel sind deaktiviert.

| Partition | Einträge |
| --- | --- |
| `policy` | `app`: Schema-Version 1 und Entra-Gruppe für App-Zulassung |
| `repositories` | Repository, fachlicher Anzeigename und Zuordnung Tätigkeit → Gruppen-Objekt-ID |
| `links` | Eindeutige Zuordnung Entra-Identität ↔ GitHub-Benutzer-ID |
| `reviews_<Bestandskennung>` | Prüfentscheidung, geprüfter Commit, verknüpfte Autor- und Prüferidentität |

Der erste Bestand verwendet diese Gruppen:

| Tätigkeit | Gruppe |
| --- | --- |
| Lesen | `editor8-notariat-lesen` |
| Bearbeiten und Einreichen | `editor8-notariat-pflegen` |
| Fachprüfung | `editor8-notariat-pruefen` |
| Gemeinsame Begriffe pflegen | `editor8-notariat-begriffe` |
| Geprüfte Änderungen übernehmen | `editor8-notariat-uebernehmen` |

Jede zugewiesene Tätigkeit erlaubt das Lesen dieses Bestands. Gemeinsame Begriffe pflegen benötigt zusätzlich die Pflegerrolle. Eine Fachprüferrolle enthält keine automatische Pfleger- oder Übernahmerolle. Ein anderer Bestand erhält eigene Gruppen und einen eigenen Tabelleneintrag. Der Server bildet keine Kombination aus einer globalen Schreibrolle und allen sichtbaren Repositories. Öffentlich lesbare GitHub-Repositories werden ohne Entra-Bestandsfreigabe nicht angeboten.

Die Berechtigungsprüfung hat höchstens 60 Sekunden Anwendungscache für Lesen. Vor jeder geschützten Änderung werden Gruppen und App-Installationsumfang erneut abgefragt; GitHub-Schreibrechte werden ebenfalls geprüft. Die tatsächliche Wirksamkeit hängt zusätzlich von der Weitergabe einer Änderung bei Entra/GitHub ab. Bei nicht prüfbaren Richtlinien oder Anbietern wird die Aktion abgewiesen. Ein App-Entzug führt zu 403; eine erneute Anmeldung erteilt keine zusätzlichen Rechte. Abmelden bleibt möglich. Ein entzogener Bestand kann abgelegt und ein anderer erlaubter Bestand gewählt werden.

## Fachprüfung und Übernahme

Die fachliche Freigabe ist an den angezeigten Commit gebunden. Der Server verhindert die Freigabe der eigenen verknüpften Identität und speichert einen Nachweis erst nach der erfolgreichen GitHub-Prüfentscheidung. Kontoverknüpfungen verhindern das Teilen eines GitHub-Kontos zwischen zwei Entra-Konten; sie ersetzen keine organisatorische Feststellung der natürlichen Person.

Übernehmen verlangt eine gesonderte Rolle, aktuelle GitHub-Schreibrechte, den unveränderten Commit, eine unabhängige über den Editor dokumentierte Freigabe und erfolgreiche technische Prüfungen. Offene Änderungswünsche, unvollständige Prüfergebnisse, neue Änderungen oder ein unpassender Datenumfang sperren die Aktion. GitHub erhält den erwarteten Commit beim Merge und prüft seinen eigenen Branchschutz. Die Freigabe dokumentiert die Fachprüferberechtigung zum Zeitpunkt der Entscheidung; ein späterer Rollenentzug löscht die historische Entscheidung nicht. Für private Datenziele muss die GitHub-App zusätzlich `Checks: read` und `Commit statuses: read` besitzen; bei fehlendem Zugriff auf Prüfergebnisse wird nicht übernommen.

Das Datenrepository bleibt Eigentümer seiner Schutzregeln. Direkte GitHub-Schreibmöglichkeiten außerhalb des Editors werden durch die Entra-Rollen nicht eingeschränkt. Die Hauptzweig-Sperre ist auf Nutzerwunsch bis 09.10.2026 zurückgestellt. Auch die reale Prüfung mit zwei Fachkonten bleibt bis 01.12.2026 zurückgestellt. Der bestehende Prüfvergleich unterstützt die vereinbarten Fall- und Vokabularänderungen; beliebige repositoryweite Änderungen benötigen weiterhin eine passende Datenadapter- und Vergleichsfunktion.

## Einrichtung und kontrollierte Aktivierung

`scripts/deploy_iam.py` zeigt ohne Optionen nur den Plan. `--apply` richtet den beschriebenen Umfang mit dem bestehenden Verwaltungsaccount ein; der Helper prüft Mandant und Subscription. Er schreibt ein auf 180 Tage begrenztes Clientgeheimnis direkt nach Key Vault, ohne Klartextausgabe. Die Erneuerung vor Ablauf ist eine Betriebsaufgabe. Der Helper gewährt der Editor-Anwendung nur delegiertes `User.Read`, keine Graph-Schreibrechte und keinen Zugriff auf fremde Benutzerprofile.

`--invite GITHUB=EMAIL` benötigt bestätigte Kontaktadressen und einen gesondert geprüften Einladungsumfang. Für weitere Bestände lassen sich `--repository`, `--label` und `--group-prefix` angeben. Der Bestand muss den Datenvertrag erfüllen, die App muss darauf installiert sein und die persönlichen GitHub-Rechte bleiben erforderlich.

Die produktive Umstellung erfolgt erst mit `--apply --activate --expected-commit <vollständiger editor8-Commit>`, nachdem das neue Image aktiv und gesund sowie dessen Release geprüft ist. Die vier erforderlichen Einstellungen sind `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET` als Key-Vault-Verweis und `IAM_TABLE_ENDPOINT`; dazu `AUTH_PROVIDER=entra`. Bei Aktivierung entfernt der Helper die bisherigen Hostlisten. Im Entra-Betrieb werden auch die personenbezogenen Listen der alten Image-Registry nicht mehr ausgewertet. Für die kontrollierte Migration bleibt `AUTH_PROVIDER=github` verfügbar, bis Betreiber- und Gastzugang tatsächlich geprüft sind. Ein Benutzerwechsel in Entra oder der Laufzeittabelle braucht anschließend keinen Image-Build und keine neue Container-Revision.

## Technische Nachweise und offene Abnahme

Synthetische Tests prüfen signierte Tokens, Mandant, Audience, Nonce, Browserbindung beider Anmeldungen, eindeutige Verknüpfung, Bestandsgrenzen, Rechteentzug während einer Sitzung, fehlende GitHub-Schreibrechte und die Bindung von Übernahmen an Freigabe und Commit. Browserprüfungen verwenden ausschließlich künstliche Daten und Konten. Diese Nachweise ersetzen weder eine tatsächlich eingerichtete Unternehmensanwendung noch eine reale Betreiber-/Gastanmeldung.

Quellen: [Entra-Gruppenzuweisung](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/assign-user-or-group-access-portal), [eigene Gruppenmitgliedschaften mit User.Read prüfen](https://learn.microsoft.com/en-us/graph/api/directoryobject-checkmembergroups?view=graph-rest-1.0), [GitHub-App-Benutzertoken](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app), [Check Runs lesen](https://docs.github.com/en/rest/checks/runs#list-check-runs-for-a-git-reference).

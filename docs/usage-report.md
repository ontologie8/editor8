# Nutzungsbericht der gehosteten App

Betreiberdokumentation, Stand 07.10.2026. Auftrag: wöchentlicher Bericht an `kontakt@ontologie8.de`. Dieselbe Adresse steht in der App unter Hilfe → Kontakt. Das Betreiberkonto wird als `admin@ontologie8.de` angezeigt; die bestätigte Entscheidung verwendet vorerst die vorhandenen E-Mail-Aliasse. Kontaktadresse, Absenderverbindung und Administratorrechte sind getrennte Einstellungen. Den aktuellen Konto- und Aliasbestand beschreibt [Betreiberidentitäten](operator-identities.md). App-Nutzung, GitHub-Datenrechte und Fachfreigaben bleiben getrennt. Dieser Bericht ist kein Freigabenachweis und misst keine Arbeitsdauer.

## Aufzeichnung

Der gehostete Server schreibt einzeilige JSON-Ereignisse mit dem Präfix `editor8_audit `. Zulässige Felder sind Schema, UTC-Zeitpunkt, Aktion, Ergebnisstatus, bestätigte GitHub-Benutzer-ID, geprüfter Anzeigename, ausgewähltes Repository, Release und gegebenenfalls `changed`. Sitzungsobjekte, Tokens, Cookies, OAuth-Codes, Anfragekörper, Quellenangaben und Akteninhalte werden nicht übernommen.

Erfasst werden Dienststart, abgeschlossene Anmeldung, abgewiesene Anmeldung, erfolgreicher Abruf eines Modellbestands oder Modells, Bestandswechsel, Speichern, Einreichen und Prüfentscheidung. Statusabfragen, Vorschau und Hintergrundindizes werden nicht als eigene Nutzungstätigkeiten gezählt. Gespeicherte Änderungen zählen nur, wenn der Speicherweg `changed: true` meldet. Unbekannte Identitäten bleiben ausdrücklich nicht zugeordnet; Benutzeranzahlen verwenden bestätigte GitHub-IDs.

Azure sammelt diese Ereignisse im vorhandenen Log-Analytics-Workspace `law-nac-ontology-editor`. Seine geprüfte Aufbewahrung beträgt 30 Tage. Die erste Aufzeichnung beginnt mit dem Release dieser Funktion. Ältere Nutzung ist nicht nachträglich rekonstruierbar. Die im Bericht angegebene erste Aufzeichnung bezieht sich auf noch vorhandene Protokolle.

## Wochenablauf

Die Consumption Logic App `editor8-weekly-usage` läuft montags um 08:00 Uhr in der Zeitzone Berlin, einschließlich Sommerzeit. Sie fragt die vergangenen sieben Tage ab und erzeugt:

- Übersicht mit aktiven, bestätigten Konten, Anmeldungen, Ereignissen und abgewiesenen Zugriffen;
- Tabelle je Konto und Datenbestand mit letzter Aktivität, Öffnungen, tatsächlichen Speicheränderungen, eingereichten Änderungen und Prüfentscheidungen;
- Hinweis auf Aufzeichnungsbeginn und zuletzt protokolliertes Editor-Release.

Die verwaltete Identität der Logic App erhält `Log Analytics Reader` ausschließlich am vorhandenen Workspace. Sie bekommt keine Ontologie-Schreibrechte und keine mandantenweiten E-Mail-Anwendungsrechte. Berichtsinhalte liegen auch im Azure-Ausführungsverlauf; dessen Zugriff gehört zum Betrieb.

## Einrichtung und Versand

`scripts/deploy_usage_report.py` verwendet die vorhandene Azure-CLI-Sitzung und prüft den `f8`-Mandanten. Der Standardlauf legt den Ablauf, eine eigene Outlook-Verbindung und die begrenzte Leserolle an. Er erzeugt Berichte, schaltet den E-Mail-Versand aber erst nach einer bestätigten Verbindung frei. Wiederholte Auslieferungen erhalten eine vorhandene Outlook-Verbindung und deren Autorisierung.

1. In Azure die API-Verbindung `editor8-report-outlook` öffnen, unter **Edit API connection** das vorgesehene Absenderkonto autorisieren und speichern. Das Konto muss zum vorgesehenen Betreiber gehören; keine fremde Unternehmens-Mailverbindung verwenden.
2. Den tatsächlichen angemeldeten Absender und den Status `Connected` prüfen.
3. Den Betriebshelfer mit `--send-mail` ausführen. Ohne verbundene API-Verbindung verweigert er die Versandaktivierung.
4. Den Wochenablauf manuell ausführen und den Eingang bei `kontakt@ontologie8.de` nachweisen. Erst dann ist die E-Mail-Auslieferung abgeschlossen.

Vorher kann der Ablauf manuell mit deaktiviertem Versand geprüft werden. Er muss Logabfragen, Tabellen und Bericht erfolgreich erzeugen; das Ergebnis lautet ausdrücklich, dass die Mailfreigabe noch fehlt. Eine erfolgreiche Azure-Ressourcenbereitstellung allein beweist keinen E-Mail-Versand.

Die Quellen der Abfragen liegen in `infra/usage-*.kql`; der Betriebshelfer erzeugt eine exportierbare ARM-Vorlage. Die Vorlage enthält keine Zugangsdaten. Nutzern erklären die Fachhilfe und das Training nur die nachvollziehbare Aufzeichnung ihrer Arbeit; Einrichtung und Azure-Befehle bleiben in dieser Betreiberdokumentation.

Quellen: [Container-App-Protokolle](https://learn.microsoft.com/en-us/azure/container-apps/log-monitoring), [Logs-API](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/api/access-api), [verwaltete Identität](https://learn.microsoft.com/en-us/azure/logic-apps/authenticate-with-managed-identity), [Logdaten per E-Mail](https://learn.microsoft.com/en-us/azure/connectors/connectors-azure-monitor-logs).

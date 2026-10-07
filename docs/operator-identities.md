# Kontakt und Administratoridentität

Stand: 07.10.2026. Diese Betreiberdokumentation trennt Adressen, Anmeldung und Berechtigungen. Die fachliche Hilfe enthält keine Verwaltungsanweisungen.

## Beauftragte Adressen

| Zweck | Adresse |
| --- | --- |
| Wochenbericht über die App-Nutzung | `kontakt@ontologie8.de` |
| Hilfe → Kontakt, Bedienfragen und technische Störungen | `kontakt@ontologie8.de` |
| Anzeige des Betreiberkontos in der App und im Bericht | `admin@ontologie8.de` |

Die Kontaktadresse wird weder in eine App-Benutzerliste noch als Fachprüfer eingetragen. Der Bericht liest Logdaten mit seiner verwalteten Azure-Identität. Seine Empfängeradresse erteilt keine Azure-, GitHub- oder Fachprüferrechte. Die Outlook-Absenderverbindung wird separat autorisiert; eine Änderung des Empfängers autorisiert keinen Absender.

## Aktuell bestätigter Verzeichnisbestand

Die Microsoft-Graph-Abfrage bestätigt `admin@ontologie8.de` und `kontakt@ontologie8.de` als SMTP-Aliasse des bestehenden Benutzerobjekts `94f4a71c-ff52-4074-b215-8cc138be329b`. Dessen Anmeldename und primäre E-Mail-Adresse lauten weiterhin `ofunk@funktion8.de`. Die Aliasse sind keine separaten Benutzerkonten und haben keine eigenen Rechte. Ein eigenständiges Administratorkonto und eine Umbenennung des vorhandenen Kontos sind unterschiedliche Maßnahmen; die zweite würde auch bestehende funktion8-Anmeldungen betreffen.

Der Nutzer hat bestätigt, dass aktuell die E-Mail-Aliasse und eine Anzeige ohne persönlichen Namen genügen. Ein separates Administratorkonto und eine Umbenennung des bestehenden Kontos sind nicht beauftragt. Die vorhandene Azure-CLI-Sitzung und die Owner-Zuweisung der Azure-Subscription verwenden weiterhin dieses bestehende Benutzerobjekt.

Die App zeigt für das bestätigte Betreiber-GitHub-Konto `ofunk` den Namen `admin@ontologie8.de` in der Kopfzeile sowie in Verlauf und Prüfansichten. Der Nutzungsbericht verwendet dieselbe Anzeige für die bestätigte GitHub-ID `30691509`. Das ist eine Anzeigezuordnung; kanonische GitHub-Namen, IDs, Benutzerzulassung, Entwurfszuordnung, Wiederherstellung und Prüfberechtigungen bleiben erhalten. Herkunft und Autoren bleiben in NOTICE und den Lizenzhinweisen dokumentiert.

## Fundstellen der bisherigen Adresse

| Fundstelle | Bedeutung und Behandlung |
| --- | --- |
| Berichtsvorlage und aktiver Azure-Wochenablauf | Empfänger ist `kontakt@ontologie8.de`. |
| Betreiberdokumentation zum Wochenbericht | Neue Empfängeradresse ist maßgeblich. |
| Entra-Benutzerobjekt und Aliaszuordnung | Bisheriger Anmeldename, primäre E-Mail und Eigentümer beider neuen Aliasse. Bleibt gemäß Nutzerentscheidung bestehen. |
| Azure-CLI-Sitzung und Azure-Owner-Zuweisung | Bestehende Verwaltungsidentität. Außenanzeige und E-Mail-Alias ändern keine Rechte. |
| Bereits veröffentlichte Git-Commits | Historische Autorenadresse. Keine nachträgliche Umschreibung der Git-Historie. Die aktuelle lokale Git-Autorenadresse ist die GitHub-Noreply-Adresse des Entwicklers. |
| Diese Bestandsaufnahme | Dokumentiert den tatsächlichen internen Bestand; keine App-Kontaktadresse. |

Der Editor identifiziert Nutzer derzeit über GitHub-IDs und GitHub-Anmeldenamen. `ofunk` ist dabei ein GitHub-Konto, keine Microsoft-E-Mail-Adresse. Die CI-Auslieferung verwendet eine Azure-Anwendungsidentität, der Bericht seine eigene verwaltete Identität. Die Anzeigezuordnung ersetzt daher ausschließlich sichtbare Beschriftungen, keine führenden Identitäten.

## Wo `f8` zu finden ist

`f8` ist der Anzeigename des vorhandenen Entra-Mandanten, kein Benutzer, keine App und keine Gruppe:

- Mandanten-ID: `870c862b-56f7-4c9b-b0d9-f1f7d32c835c`.
- Ursprüngliche Domain: `funktion8.onmicrosoft.com`.
- Aktuelle Standarddomain: `funktion8.de`.
- `ontologie8.de` ist bereits eine bestätigte weitere Domain dieses Mandanten.

Im [Entra Admin Center](https://entra.microsoft.com) den Mandanten mit dieser ID auswählen und **Entra ID → Übersicht → Eigenschaften** öffnen. Dort stehen Name und Mandanten-ID. Eine Änderung des Anzeigenamens verschiebt weder Ressourcen noch Konten in einen anderen Mandanten. Der Anzeigename ist daher keine technische Abhängigkeit des Editors.

Quellen: [Benutzerattribute und SMTP-Aliasse](https://learn.microsoft.com/troubleshoot/azure/active-directory/proxyaddresses-attribute-populate), [Benutzerprofile verwalten](https://learn.microsoft.com/en-us/entra/fundamentals/how-to-manage-user-profile-info), [Mandantenübersicht und Eigenschaften](https://learn.microsoft.com/en-au/entra/identity-platform/quickstart-create-new-tenant).

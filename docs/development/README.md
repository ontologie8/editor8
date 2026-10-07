# Editorentwicklung und Betrieb

Diese Dokumentation richtet sich an den Verantwortlichen für Entwicklung und Betrieb von editor8. Das Software-Repository `ontologie8/editor8` wird von ihm gepflegt. Ontologiepfleger und Notare sind Anwender des Editors und arbeiten an Fachmodellen in getrennten Datenrepositories, beispielsweise `notariat8/ontology`.

Die fachliche Nutzung erklärt das [Produkthandbuch](../product/README.md); der [Grundkurs](../../training/README.md) übt sie mit künstlichen Beispielen. Beide werden im Editor unter Hilfe angeboten. Diese Entwickler- und Betriebsdokumentation wird dort nicht als Bedienhilfe eingebunden. Modellpflege erfordert keinen Zugriff auf den Editor-Quellcode.

## Technische Dokumentation

- [Kontakt und Administratoridentität](../operator-identities.md): Kontaktadresse, Statistikempfänger, tatsächliche Aliaszuordnung und Entra-Mandant.
- [Lokaler Start und Softwaretests](../../README.md): ausdrücklich separater Datencheckout, Python, JavaScript und Browserprüfungen.
- [Hosting und GitHub-Anmeldung](../editor-hosting.md): Server, Azure und Zugangskonfiguration.
- [App-Eigentum und Dateninstallation](../github-app-ownership.md): Registrierung bei `ontologie8`, getrennte Installation beim Datenbetreiber und Identitätsprüfung der Betriebshelfer.
- [Datenrepositories und Benutzer](../data-repositories-and-users.md): Registry, App-Installation, Zulassung und fachliche Rollen.
- [Nutzer und Notare zulassen](../editor-user-onboarding.md): externe Konten, GitHub-404 bei der Anmeldung und getrennte Freigaben.
- [IAM-Zielbild](../iam-zielbild.md): zentrale Benutzerverwaltung ohne Image-Build oder neue Container-Revision; recherchierte Alternativen und ausstehende Migration.
- [IAM-Implementierung](../iam-implementation.md): Entra/GitHub-Anmeldung, bestandsbezogene Gruppen, Laufzeittabelle, kontrollierte Aktivierung und konkrete Abnahme.
- [Nutzungsbericht](../usage-report.md): erlaubte Ereignisse, Wochenbericht in Azure und getrennte Freigabe des E-Mail-Versands.
- [Datenvertrag](../data-contract.md): Adapter und Schnittstelle zu den Fachmodellen.
- [Datenintegration in CI](../editor-integration-ci.md): getrennte Software- und Datenstände prüfen.
- [HTTPS und Domainbetrieb](../custom-domain.md): Zertifikat, öffentliche Adresse und technische Anmeldeprüfung.
- [Migration](../migration.md), [Produktstand](../editor-produktstand.md) und [Roadmap](../editor-roadmap.md): Entwicklungsplanung und noch offene Abnahmen.

Softwareänderungen bleiben in editor8; Fachmodelländerungen bleiben im jeweiligen Datenprojekt. Benutzerzulassung, Modellrollen und Repository-Rechte werden durch den zuständigen Verantwortlichen verwaltet. Anweisungen zu Hosteinstellungen, Tokens, Adaptercode oder Deployments gehören nicht in die fachliche Hilfe.

## Produkthilfe und Training pflegen

Bei geänderten Befehlen, Feldern, Rollen oder Speicherabläufen im selben Änderungsvorschlag die fachlichen Erklärungen aktualisieren:

- Handbuchquelle: [handbook.json](../product/handbook.json).
- Trainingsquelle: [course.json](../../training/course.json).
- Rein künstliches Übungsmodell: [workshop.json](../../training/examples/workshop.json).
- Kurzanleitung, Begriffe und Kontexthilfe: [app.js](../../editor/app.js).
- Hinweise und Kontextmenüs: [interaction.js](../../editor/interaction.js). Die Interaktionsschicht ruft die bestehenden Entwurfs-, Speicher- und Hilfeabläufe auf. Zielobjekt, laufende Speicherung und fachliche Berechtigungen beim Ausführen erneut prüfen; Eingabefelder behalten ihre Textbefehle. Interne Scrollvorgänge von Textfeldern beim Fokuswechsel dürfen ein gerade geöffnetes Objektmenü nicht schließen.
- Anordnung und Zielgruppe: [DESIGN.md](../../DESIGN.md).

```powershell
python scripts/build_learning.py
python scripts/build_learning.py --check
```

Der Generator erzeugt die Browserinhalte und Markdownfassungen gemeinsam. Generierte Dateien nicht getrennt bearbeiten. Die Softwareprüfung kontrolliert ihren Gleichstand. Betroffene Kapitel, Folien, Lernfragen und die Speicherübung im Browser prüfen; alle Beispiele bleiben künstlich. Entwicklungs- und Betriebsschritte nicht in die Inhalte für Ontologiepfleger oder Notare aufnehmen.

Die [Trainingsrecherche](../research/2026-10-03-ontology-training.md) dokumentiert die verwendeten Lehrmuster. Für spätere Erklärvideos: Problem zeigen, eine Handlung vorführen, Ergebnis erklären, Lernfrage beantworten. Eine Aufnahme pro Lektion erleichtert spätere Pflege. Inhalte eigenständig formulieren und keine fremden Produktbilder oder Videos übernehmen.

## Software ausliefern

Ein Build ist erst abgeschlossen, wenn das erwartete Image auf Azure bereitgestellt ist, die aktive Revision gesund ist und die laufende App den erwarteten Editor-Commit als Release ausliefert. Das ist ein Abschlusskriterium für die Softwareentwicklung. Für fachliche Nutzer zählt ihre begründete, gespeicherte, geprüfte und übernommene Modelländerung.

Inhalt: CC-BY-4.0. Herkunft und Lizenzzuordnung bleiben in [NOTICE](../../NOTICE) erhalten.

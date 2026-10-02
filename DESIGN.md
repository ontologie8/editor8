# Desktop-Arbeitsoberfläche

Status: verbindliche Nutzeranforderungen vom 02.10.2026. Der erste klickbare Entwurf wurde visuell abgelehnt; Maße und Proportionen müssen gemäß [Microsoft-Referenzprüfung](docs/design/microsoft-reference-audit.md) korrigiert werden. Keine Designabnahme.

## Aufgabe und Reihenfolge

Verstehen → Bearbeiten → Prüfen. Beim Öffnen steht das Verständnis der Fachvorlage im Mittelpunkt. Kontextbezogene Hilfe, eine kurze Dokumentation und geführte Beispiele unterstützen die Orientierung. Fachliche Inhalte bleiben im gewählten Datenrepository; Beispiele im Softwareprojekt sind vollständig künstlich.

## Arbeitsfläche

- Primär: 27–34-Zoll-Monitore, 2K–4K. Auch bei Windows-Skalierung muss die Oberfläche ausreichend Platz und lesbare Schrift bieten. Deshalb CSS-Viewports zusätzlich bei 1440×900 und 1920×1080 prüfen, nicht nur physische Pixel zählen.
- Die Anwendung füllt das Browserfenster. Kein Seitenscrollen, um Menüs, Hauptaktionen, Datenrepository- oder Vorgangsauswahl zu finden.
- Titelbereich, Hauptmenü, kontextbezogene Befehle und Statusleiste bleiben sichtbar. Arbeitsfläche und einzelne Inhalte dürfen intern scrollen. Keine unbegrenzt wachsende Seite.
- Ganz links: feste Bereichsnavigation (Verstehen, Bearbeiten, Prüfen, Hilfe). Daneben: ausgewähltes Datenziel, Suche und aufklappbarer Baum Datenziel → Vorgang → Baustein. Mitte: Fachgraph oder Arbeitsdokument. Rechts: Details, Bearbeitung, Prüfvergleich oder Hilfe. Die Auswahlposition bleibt beim Aufgabenwechsel erhalten.
- Microsoft-Office-Menüführung: Datei, Startseite, Bearbeiten, Überprüfen, Ansicht, Hilfe. Standardbefehle heißen durchgängig Öffnen, Speichern, Drucken; keine eigenen Ersatznamen. Die Arbeitsfolge Verstehen → Bearbeiten → Prüfen wird durch Inhalt und Hilfe unterstützt, nicht als erfundene Standardmenüs ausgegeben. Befehle werden nach Aufgabe gruppiert; ein aktiver Menübereich zeigt die passenden Aktionen. Keine Ansammlung gleichgewichtiger Schaltflächen in der Kopfzeile.
- Vollbild, Fensteransicht und einblendbare Details ändern die verfügbare Arbeitsfläche, nicht den Ort der Menüs.
- Mobile ist sekundär. Kleinere Ansichten dürfen kompakter werden, ohne die Desktop-Arbeitsfläche als lange Webseite abzubilden.

## Visuelle Richtung

Microsoft Office / Outlook ist die primäre Referenz für Benennung, Menüband und räumliche Anordnung gemäß Nutzerkorrektur vom 02.10.2026. Die vom Nutzer gezeigte Outlook-Abbildung wird nur als visuelle Referenz verwendet; keine darin enthaltenen Konto- oder Nachrichtenwerte werden übernommen.

Palantir Ontology Manager ist ergänzende Referenz für ruhige Navigation, Lesbarkeit, Detailanordnung und Beziehungen. Seine dauerhafte Kopf- und Seitenleiste dienen als Orientierung. Es werden keine Logos, Screenshots oder Produktassets übernommen.

Quellen: [Übersicht](https://www.palantir.com/docs/foundry/ontology-manager/overview), [Navigation](https://www.palantir.com/docs/foundry/ontology-manager/navigation), gelesen am 02.10.2026.

Zur Prüfung vorgeschlagene Gestaltungswerte: Segoe UI als Windows-Systemschrift, Grundgröße 14px, heller Titel- und Menübereich wie in der Outlook-Vorlage, helle Arbeitsfläche, dezentes Blau für Auswahl und Hauptaktion, dünne Trennlinien, geringe Rundung. Keine dekorativen Farbverläufe, Schatten oder ineinander geschachtelten Karten.

## Hilfe und Zustände

Hilfe muss direkt im Arbeitsbereich erreichbar sein. Ein Beispiel erklärt Auswahl, Baustein, Beziehung und den Übergang zur Bearbeitung. Beispiele geben keine notarielle Rechtsauskunft.

Lesemodus, ungespeicherte Eingaben, gespeicherter Entwurf und eingereichte Änderung müssen eindeutig unterscheidbar sein. Eine simulierte Freigabe im Entwurf darf nicht wie eine tatsächliche notarielle Freigabe erscheinen. Release und Datenziel bleiben sichtbar.

## Erster Entwurf

`docs/design/desktop-workbench.html` ist eine eigenständige Vorschau mit künstlichen Daten. Menüs, Vorgangsauswahl, Graphauswahl, Beispielbearbeitung, Prüfvergleich, Hilfe und Vollbild sind lokal bedienbar. Die Vorschau hat keine GitHub- oder Azure-Schreibfunktion. Nach der Designentscheidung werden die produktiven Abläufe in diese Arbeitsstruktur überführt und bis Azure geprüft.

## Microsoft-Referenzen

Geprüft am 02.10.2026:

- [Office: Registerkarte Datei / Backstage](https://support.microsoft.com/de-de/office/collab-files/start-backstage-with-the-file-tab): Standardbefehle Öffnen, Speichern, Drucken und Trennung von Dateiaktionen und Inhaltsaktionen.
- [Microsoft NavigationView](https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/navigationview): dauerhaft erreichbare Bereichsnavigation am linken Rand.
- [Microsoft TreeView](https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/tree-view): aufklappbare Hierarchie neben dem Arbeitsbereich.

NavigationView und TreeView beschreiben Windows-Steuerelemente; im Browser wird ihre Anordnung und Bedienlogik übernommen. Der Entwurf ist keine Microsoft-Anwendung. Öffnen führt zur Auswahl im Beispieldatenbaum; Speichern speichert nur den flüchtigen Beispielzustand; Drucken öffnet den Browserdruck für eine Lesefassung. Produktiv muss Speichern den tatsächlichen Speicherstatus anzeigen und darf eine notarielle Freigabe nicht vorwegnehmen.

## Verbindliche Gesamtanordnung

Die gesamte Oberfläche folgt dem vom Nutzer vorgegebenen Office-/Outlook-Muster, nicht nur einzelne Schaltflächen: heller Titelbereich mit Suche, oben links Hamburger-Schaltfläche zum Ein-/Ausblenden des inneren Navigationsbereichs, Registerkarten und Befehlsgruppen im Menüband, äußere feste Bereichsleiste, innere Baum-/Auswahlnavigation, mittlere Arbeitsfläche, rechter Detail-/Hilfebereich und Statusleiste. Die äußere Bereichsleiste bleibt beim Einklappen des Baums erreichbar. Der Bereich Verstehen zeigt die Modellhierarchie, Bearbeiten die Modellhierarchie mit bearbeitbarer Auswahl, Prüfen die gespeicherten Änderungen, Hilfe die Dokumentationsauswahl. Keine funktionslosen Outlook-Bereiche wie E-Mail oder Kalender übernehmen.

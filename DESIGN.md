# Desktop-Arbeitsoberfläche

Status: Die korrigierte Office-Vorschau wurde am 02.10.2026 vom Nutzer zur produktiven Umsetzung beauftragt („das sieht deutlich besser aus – bau das mal“). Die Maßvorgaben und eindeutigen Befehlsorte gelten für die produktive Oberfläche. Die erste verworfene Fassung ist in der [Referenzprüfung](docs/design/microsoft-reference-audit.md) dokumentiert.

## Aufgabe und Reihenfolge

Verstehen → Bearbeiten → Prüfen. Beim Öffnen steht das Verständnis der Fachvorlage im Mittelpunkt. Kontextbezogene Hilfe, eine kurze Dokumentation und geführte Beispiele unterstützen die Orientierung. Fachliche Inhalte bleiben im gewählten Datenrepository; Beispiele im Softwareprojekt sind vollständig künstlich.

## Arbeitsfläche

- Primär: 27–34-Zoll-Monitore, 2K–4K. Auch bei Windows-Skalierung muss die Oberfläche ausreichend Platz und lesbare Schrift bieten. Deshalb CSS-Viewports zusätzlich bei 1440×900 und 1920×1080 prüfen, nicht nur physische Pixel zählen.
- Die Anwendung füllt das Browserfenster. Kein Seitenscrollen, um Menüs, Hauptaktionen, Datenrepository- oder Vorgangsauswahl zu finden.
- Titelbereich, Hauptmenü, kontextbezogene Befehle und Statusleiste bleiben sichtbar. Arbeitsfläche und einzelne Inhalte dürfen intern scrollen. Keine unbegrenzt wachsende Seite.
- Ganz links: feste Bereichsnavigation (Verstehen, Bearbeiten, Prüfen). Daneben: ausgewähltes Datenziel und aufklappbarer Baum Datenziel → Vorgang → Baustein. Mitte: Fachgraph oder Arbeitsdokument. Rechts: Details, Bearbeitung, Prüfvergleich oder Hilfe. Die Auswahlposition bleibt beim Aufgabenwechsel erhalten.
- Microsoft-Office-Menüführung: Datei, Startseite, Ansicht, Hilfe. Standardbefehle heißen durchgängig Öffnen, Speichern, Drucken; keine eigenen Ersatznamen. Die Arbeitsfolge Verstehen → Bearbeiten → Prüfen wird durch Inhalt und Hilfe unterstützt, nicht als erfundene Standardmenüs ausgegeben. Befehle werden nach Aufgabe gruppiert; ein aktiver Menübereich zeigt die passenden Aktionen. Keine Ansammlung gleichgewichtiger Schaltflächen in der Kopfzeile.
- Vollbild, Fensteransicht und einblendbare Details ändern die verfügbare Arbeitsfläche, nicht den Ort der Menüs.
- Mobile ist sekundär. Kleinere Ansichten dürfen kompakter werden, ohne die Desktop-Arbeitsfläche als lange Webseite abzubilden.

## Visuelle Richtung

Die vom Nutzer vorgegebenen Markenlogos stammen aus `software8-de/icons`, Revision `31766769bcb1c73417894859b02955140bd0d495`: e8 für Editor-Titelleiste und Browser-Symbol, n8 für das NaC-Datenziel `notariat8/ontology`. Original-PNGs in 32, 192 und 526 Pixeln werden unverändert eingebunden; responsive Bildquellen berücksichtigen die Geräteskalierung. Andere Datenziele erhalten kein NaC-Logo. Herkunft und Lizenzzuordnung stehen in NOTICE und LICENSES/README.md.

Microsoft Office / Outlook ist die primäre Referenz für Benennung, Menüband und räumliche Anordnung gemäß Nutzerkorrektur vom 02.10.2026. Die vom Nutzer gezeigte Outlook-Abbildung wird nur als visuelle Referenz verwendet; keine darin enthaltenen Konto- oder Nachrichtenwerte werden übernommen.

Palantir Ontology Manager ist ergänzende Referenz für ruhige Navigation, Lesbarkeit, Detailanordnung und Beziehungen. Seine dauerhafte Kopf- und Seitenleiste dienen als Orientierung. Es werden keine Logos, Screenshots oder Produktassets übernommen.

Quellen: [Übersicht](https://www.palantir.com/docs/foundry/ontology-manager/overview), [Navigation](https://www.palantir.com/docs/foundry/ontology-manager/navigation), gelesen am 02.10.2026.

Zur Prüfung vorgeschlagene Gestaltungswerte: Segoe UI als Windows-Systemschrift, Grundgröße 14px, heller Titel- und Menübereich wie in der Outlook-Vorlage, helle Arbeitsfläche, dezentes Blau für Auswahl und Hauptaktion, dünne Trennlinien, geringe Rundung. Keine dekorativen Farbverläufe, Schatten oder ineinander geschachtelten Karten.

## Hilfe und Zustände

Offene Eingaben werden im selben Browserfenster vorübergehend ohne Zugangsdaten gesichert. Nach Neuladen oder erneuter Anmeldung bietet die App Wiederherstellen für dasselbe Konto und denselben Modellbestand an. Sie prüft den eigenen Entwurf, führt unabhängige Änderungen zusammen und hält widersprüchliche Änderungen sichtbar an. Diese Sicherung ersetzt Speichern nicht; Abmelden und Verwerfen löschen sie.

Der Speicherdialog und die Fachprüfung zeigen Vorher/Nachher aus dem tatsächlichen RDF-Vergleich. Farben und deutsche Statuswörter kennzeichnen Hinzugefügt, Entfernt, Geändert und Unverändert. Beide Seiten verwenden dieselben Positionen; das direkte Umfeld bleibt erkennbar. Auswahl und Tastatur öffnen den Feldvergleich. Beschreibung und Quellen ohne Bausteinänderung bleiben im Textvergleich. Scrollen erfolgt innerhalb der Graphbereiche; Befehle zum Weiterarbeiten und Speichern bleiben im Dialog erreichbar.

Hilfe muss direkt im Arbeitsbereich erreichbar sein. Ein Beispiel erklärt Auswahl, Baustein, Beziehung und den Übergang zur Bearbeitung. Beispiele geben keine notarielle Rechtsauskunft.

Die gesamte sichtbare Hilfe richtet sich an Ontologiepfleger und Notare. Kurzanleitung, Begriffe, Kontexthilfe, Produkthandbuch und Training erklären die fachliche Nutzung des ausgewählten Modellbestands. Editorentwicklung, Programmierung, Hosting, Konfiguration und Softwarebuilds gehören ausschließlich in die getrennte [Entwickler- und Betriebsdokumentation](docs/development/README.md). Fachliche Nutzer pflegen Modelle in den Datenrepositories; die Pflege dieses Software-Repositories liegt beim Editorverantwortlichen. GitHub wird in der Nutzungshilfe nur erklärt, soweit Anmeldung oder ein verlinkter fachlicher Änderungsvorschlag es erfordern.

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

## Tatsächlicher Desktop des Nutzers

3840×2160, Windows-Skalierung 250 %, Browserzoom 100 % wurden am 02.10.2026 bestätigt. Für Layoutprüfung höchstens 1536×864 CSS-Pixel und zusätzlich eine kleinere Browser-Innenhöhe verwenden; Gerätepixelverhältnis 2,5 prüfen. Physische 4K-Auflösung nicht mit einem 4K-CSS-Viewport gleichsetzen. Näherungswerte für die nächste Office-Hülle: außen 68 px, innerer Baum 236 px, Menüzeile 36 px, kompakte Befehlsleiste 44 px; Herleitung und Grenzen stehen in der Referenzprüfung.

## Menüband und Symbole

Office-Verhalten: [Menüband ein-/ausblenden](https://support.microsoft.com/de-DE/Office/foundations-experiences/show-or-hide-the-ribbon-in-office). Nur Registerkarten anzeigen, bei Klick Befehle vorübergehend öffnen, dauerhaftes Anzeigen über Anheften; Strg+F1 und Doppelklick wechseln den Zustand. Escape bzw. Klick auf den Arbeitsbereich schließen die vorübergehende Befehlsleiste. Die Baum-Navigation wird unabhängig davon mit dem Hamburger-Schalter gesteuert.

Die Vorschau verwendet originale Fluent-System-SVGs aus einem festgehaltenen Microsoft-Commit; MIT-Lizenz und Herkunft liegen bei den Assets und in NOTICE. Kompakte Befehlsleiste jetzt 44 px, äußere Leiste 68 px, innerer Baum 236 px. Die korrigierte Struktur ist zur produktiven Umsetzung beauftragt.

## Eindeutige Befehlsorte

- Oben Hilfe: allgemeine Dokumentation, Kurzanleitung, Begriffe und Beispiele im mittleren Arbeitsbereich.
- Am Objekt ein Fragezeichen: Kontexthilfe zur aktuellen Auswahl im rechten Bereich, kein zweites Hauptmenü Hilfe.
- Links außen ausschließlich Verstehen, Bearbeiten, Prüfen. Eine einzige Suche im Titelbereich filtert den Baum. Keine doppelte Hilfe oder zusätzliche Bearbeiten-/Prüfen-Registerkarte oben.
- Darstellungswahl ausschließlich unter Ansicht, keine wiederholte Ansichtsregisterleiste im Dokument.
- Fluent-Komponentenregeln: [Toolbar](https://fluent2.microsoft.design/components/web/react/core/toolbar/usage), [Info label](https://fluent2.microsoft.design/components/web/react/core/info-label/usage), [Tooltip](https://fluent2.microsoft.design/components/web/react/core/tooltip/usage), [Tree](https://fluent2.microsoft.design/components/web/react/core/tree/usage). Komponentenregeln bilden die Gestaltung ab; die Zuordnung auf Editor-Aufgaben ist eine dokumentierte Implementierungsentscheidung.

## Hinweise und Kontextmenüs

Microsoft-Referenzen erneut geprüft am 04.10.2026: [Fluent Tooltip](https://fluent2.microsoft.design/components/web/react/core/tooltip/usage) und [Menus and context menus](https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/menus-and-context-menus). Kurze, ergänzende Hinweise erscheinen beim Überfahren und bei Tastaturfokus, mit 4 px Abstand zum Bedienelement. Sie bleiben beim Überfahren des Hinweises lesbar, verschwinden mit Escape und erklären bei deaktivierten Befehlen den erforderlichen Zustand. Fachlich notwendige Erläuterungen bleiben zusätzlich in sichtbaren Feldern, Hilfe zur Auswahl und Handbuch verfügbar.

Rechtsklick beziehungsweise Umschalt+F10 und die Kontextmenü-Taste öffnen die Befehle für das angeklickte Objekt. Bausteine bieten Öffnen, Bearbeiten, Verbindungen, Hilfe zur Auswahl und den Speicherbefehl des aktuellen Arbeitsentwurfs; zusätzlich angelegte Bausteine zusätzlich Entfernen. Vorgangsarten bieten Öffnen, Informationen und Drucken. Gemeinsame Begriffe bieten Öffnen, Bearbeiten entsprechend der fachlichen Berechtigung und Hilfe zur Auswahl. Das Öffnen eines Menüs verändert weder Modell noch Entwurf. Pfeiltasten, Pos1, Ende, Eingabetaste, Tab und Escape bedienen das Menü. Escape kehrt zum ursprünglichen Objekt zurück, ohne gleichzeitig dessen Detailansicht zu schließen. Menüs werden an den Bildschirmrändern eingepasst. Eingabefelder behalten die üblichen Textbefehle Ausschneiden, Kopieren und Einfügen.

Die Interaktionsschicht verwendet bestehende Speicher-, Entwurfs- und Prüfabläufe; sie erteilt keine zusätzlichen Rechte. Entwicklungsdetails bleiben in der Entwicklerdokumentation.

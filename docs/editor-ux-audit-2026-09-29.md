> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# UI-Prüfung des NaC-Fall-Editors

Stand: 29.09.2026. Diese Prüfung bewertet die **Lesbarkeit und Aufgabenführung** der Editoroberfläche, keine notarielle Richtigkeit der Falldaten.

#> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# Warum die erste Oberfläche von der Palantir-Referenz abwich

Der Aufbau stammt aus dem ersten lokalen Browser-Editor (Commit `d421489`) und wurde mit weiteren Funktionen schrittweise erweitert. Er verwendet selbst geschriebenes HTML, JavaScript und CSS, kein übernommenes Designsystem und keine Palantir-Komponenten. Die Palantir-Dokumentation wurde für Funktionen verglichen, aber nicht als prüfbare Vorgabe für Seitenhierarchie, Blickführung und Arbeitsaufgaben umgesetzt. Es gab vor dem Hosting weder einen moderierten Nutzertest mit Notariatsfachkräften noch eine Abnahme anhand gerenderter Desktop- und Mobilansichten. Technische Tests belegten Datenverarbeitung und Zugriff, nicht Bedienbarkeit.

Die [Palantir-Dokumentation zum Ontology Manager](https://www.palantir.com/docs/foundry/ontology-manager/overview) beschreibt eine dauerhafte Kopf- und Seitenleiste sowie eine Objektübersicht, aus der Eigenschaften und Beziehungen gezielt geöffnet werden. Im ersten NaC-Layout lagen dagegen Quellenlinks und Erläuterungstext im Zentrum; das Diagramm war in einem eingeklappten Bereich einer anderen Registerkarte verborgen. Damit verlangte die Oberfläche, Zusammenhänge über Navigation und Repository-Links selbst zu rekonstruieren.

#> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# Korrigierte Informationshierarchie

| Platz | Aufgabe |
| --- | --- |
| Kopfbereich | Arbeitsstand, Suche über alle Fälle, Änderung beginnen und speichern. |
| Linke Seitenleiste | Eine der 20 Vorgangsarten wählen. |
| Fallübersicht | **Direkt sichtbarer, interaktiver Graph** der verknüpften Bausteine; unverknüpfte Bausteine stehen darunter und der ganze Fall ist zuschaltbar. Ein Klick auf einen Baustein markiert ihn und erklärt seine direkten Verbindungen in Textform. Die Fallbeschreibung ist über „Info zum Fall“ erreichbar. |
| Fallübersicht bei Bedarf | Auf einen Baustein und seine Nachbarn fokussieren; die Gesamtansicht bleibt umschaltbar. |
| Kontextdialog | Rechtsquellen, NaC-Herkunft und Prozessablauf nur bei Rückfragen öffnen. |
| Weitere Arbeitsbereiche | Fachliche Bausteine und Beziehungen ändern, Änderungen einreichen oder prüfen, gemeinsame Begriffe pflegen. |

Die Oberfläche zeigt keine Turtle-Rohansicht mehr. Turtle und die daraus erzeugten Mermaid-Seiten bleiben im Git-Repository die maschinenlesbare Pflegequelle; die App stellt die daraus abgeleiteten fachlichen Inhalte dar. Der Graph zeigt nur erfasste Beziehungen. Bei Erbausschlagung sind derzeit 19 Bausteine und 6 Beziehungen vorhanden; 9 Bausteine haben keine erfasste Verbindung. Die App benennt diese Lücke, statt fachliche Verbindungen zu erfinden.

#> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# Korrektur vom 30.09.2026: UI-Entwicklung und Fachprüfung trennen

Die Verantwortung für eine gut benutzbare Oberfläche liegt beim Editor-Team. Notarinnen und Notare sollen keine unausgereifte UI durch Ausprobieren retten. Die UI wird daher als eigenständige Produktaufgabe umgesetzt und geprüft:

1. Ein klarer Hauptbereich pro Ansicht; Fallnavigation, Bearbeitung und Fachprüfung bleiben unterscheidbar.
2. Der Fachgraph ist auf breiten Bildschirmen direkt sichtbar. Ein Klick auf einen Baustein öffnet dessen Erklärung und Beziehungen unmittelbar in einer Seitenansicht. Auf schmalen Bildschirmen ersetzt eine gruppierte, vollständig lesbare Karte die abgeschnittene Grafik.
3. Quellen, Historie und technische Metadaten erscheinen erst bei Bedarf. Rohes Turtle bleibt aus der Oberfläche heraus.
4. Sichtbare Zustände für Lesemodus, Entwurf und ungespeicherte Änderung; Tastaturbedienung und mobile Ansicht werden im Browser geprüft.
5. Die technische UI-Abnahme erfolgt mit gerenderten Desktop- und Mobilansichten sowie durchgeklickten Wegen: Fall wählen, Zusammenhang erkennen, Details öffnen, Inhalt bearbeiten, Änderung speichern und einreichen. Eine fachliche Freigabe der Ontologie ist eine gesonderte Aufgabe für Notarinnen oder Notare.

Die lokale Chrome-Prüfung am 29.09.2026 zeigte den ganzen Erbausschlagungsgraphen in der Fallübersicht und die Quellen außerhalb des Hauptbereichs. Ein anschließender Browser-Test bestätigte 19 sichtbare Knoten, die Auswahl eines Knotens, den Wechsel zur Detailansicht sowie das Öffnen von Quellen- und Suchdialog. Die gehostete Revision `ca-nac-ontology-editor--0000005` lieferte das damalige HTML mit Graph und Quellendialog aus. Diese Prüfung belegte die Funktion, aber noch keine gelungene Gesamtgestaltung. Zusätzliche Palantir-Screenshots waren für den nächsten technischen Schritt nicht erforderlich.

Der letzte Absatz beschreibt die Prüfung des Standes vom 29.09.2026. Für die neue UI ist ein Notarkonto keine technische Abnahmevoraussetzung. Eine spätere Rückmeldung aus der Praxis ist willkommen, aber die Oberfläche muss bereits davor kohärent und verständlich sein.

Am 30.09.2026 wurden die Desktop- und Mobilansicht des UI-Standes `45b31ae` erneut gerendert. Ein lokaler Browserdurchlauf bestätigte für Erbausschlagung 19 Bausteine in beiden Darstellungen, einen direkt geöffneten Detaildialog nach Bausteinwahl, Quellen- und Suchdialog, `Ctrl+K`, sechs sofort sichtbare Verbindungen, eine ausgefüllte Bausteindetailansicht und keine horizontale Seitenüberläufe bei 500 Pixeln Breite. Das aktuelle Pilot-Image dieses Stands läuft in Azure-Revision `ca-nac-ontology-editor--0000006`.

#> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# Korrektur nach Rückmeldung zur Immobilienansicht

Der Screenshot des Immobilienkaufvertrags zeigte einen nativen Auswahlkasten mit 22 Einträgen, der den Graphen verdeckte. Die doppelte Überschrift und der Erklärungssatz nahmen weiteren Platz ein. Die Browserprüfung des vorherigen Stands hatte diesen Bedienfehler nicht erfasst; die dortige Bewertung der UI war zu positiv.

Die Fallbeschreibung „Kauf oder Verkauf …“ ist fachlicher Inhalt aus `dcterms:description` in `cases/immobilienkaufvertrag/ontology.ttl`. Überschriften, Zähler, Platzhalter und Bedienhinweise kommen aus `editor/index.html` und `editor/app.js`. Bei der Korrektur wurde kein Hilfetext in Turtle geschrieben und kein fachlicher Fallinhalt geändert. Die Beschreibung bleibt im Dialog „Info zum Fall“ erreichbar. Die lange native Auswahlliste entfällt; eine fallbezogene Suche öffnet Treffer in einem eigenen Dialog und anschließend ihre Beziehungen. Der Graph wird auf mittleren Desktopbreiten vollständig ohne horizontales Abschneiden angezeigt. Bereits in Turtle enthaltene Präfixe wie „Dokument:“ werden in der jeweiligen, eindeutig beschrifteten UI-Kategorie nur für die Anzeige entfernt; die gespeicherten Bezeichnungen bleiben unverändert.

Der lokale Chrome-Durchlauf für Commit `6006268` prüfte am Immobilienkaufvertrag 22 sichtbare Graph-Bausteine, die Suche nach „Grundbuch“ mit öffnendem Detail, acht Verbindungen, die Infoansicht, Tastatursuche, den Arbeitsbereich für Bausteine und die Mobilansicht. Bei 1100 Pixeln Breite bleibt der Graph sichtbar; die Fallwahl wandert oberhalb der Arbeit. Bei 500 Pixeln erscheinen gruppierte Bausteinkarten ohne horizontales Seitenüberlaufen. Diese Browserprüfung bestätigt die technischen Interaktionen und die betrachteten Größen, keine fachliche oder notarielle Freigabe der Inhalte.

#> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# Zusammenhängende Überarbeitung vom 30.09.2026

Die vorige Korrektur entfernte die lange Auswahlliste aus der Graphübersicht, ließ aber einen modalen Detaildialog über der Karte stehen. Die aktuelle Arbeitsfläche öffnet ausgewählte Bausteine und ihre direkten Beziehungen neben dem Graphen; bei geringerer Breite erscheint eine kompakte Detailfläche am unteren Rand. Die Karte bleibt auf breiten Bildschirmen bedienbar. „Verknüpft“ zeigt zunächst nur Bausteine mit erfassten Beziehungen, während unverknüpfte Bausteine direkt darunter einzeln erreichbar sind; „Alle“ zeigt die vollständige Fallvorlage. Beim Immobilienkaufvertrag sind das 14 verknüpfte und 8 noch unverknüpfte Bausteine. Dieser Unterschied ist eine Eigenschaft der vorliegenden Ontologie, keine fachliche Bewertung fehlender Verbindungen.

Fallbeschreibung, Rechtsquellen und Änderungsverlauf liegen im Dialog „Info zum Fall“. Die Bausteinliste hat eine Suche und einen Artfilter in einer Zeile. Die Verbindungsansicht führt im Lesemodus zurück zum Graphen; im Entwurf werden Ausgang und Ziel über eine gezielte Suche gewählt. Dadurch erscheint an keiner dieser Stellen eine lange native Auswahlliste mit allen Bausteinen. Die Oberfläche hält Turtle und technische Metadaten aus der Hauptaufgabe heraus. An fachlichen TTL-Dateien wurde für diese UI-Änderung nichts geändert.

Die Orientierung an der [Palantir-Navigation](https://www.palantir.com/docs/foundry/ontology-manager/navigation) betrifft dauerhafte Navigation und Suche; die [Objektbeziehungen in Vertex](https://www.palantir.com/docs/foundry/vertex/explore-object-relationships) zeigen das Prinzip einer Auswahl mit eigenem Detailbereich. Der NaC-Editor übernimmt keine Foundry-Komponenten und beansprucht keine Funktionsgleichheit. Die Gestaltung und Implementierung sind für diesen abgegrenzten Katalog entstanden.

Ein lokaler Chrome-Durchlauf prüfte die 20 Fallansichten und die Zahl der sichtbaren Bausteine gegen die Falldaten. Für den Immobilienfall wurden Graphansichten, einzelne unverknüpfte Bausteine, Auswahl und Schließen der Detailfläche, Zoom, Suche mit Pfeiltasten und Eingabetaste, Dialog „Info zum Fall“, Rücksprung aus einer Verbindung sowie die geöffneten Bearbeitungsfelder geprüft. Gerenderte Ansichten mit 1438, 1100 und 500 Pixeln Breite wurden visuell kontrolliert; in den geprüften Wegen gab es keine horizontalen Seitenüberläufe. Dies ist eine technische und visuelle UI-Prüfung. Ein echter angemeldeter Speichern-/Pull-Request-Durchlauf und eine Nutzungserprobung mit Editorinnen oder Editoren stehen für eine Produktabnahme noch aus.

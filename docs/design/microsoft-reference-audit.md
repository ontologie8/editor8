# Office-/Outlook-Referenz: Messung und Korrekturbedarf

Stand: 02.10.2026. Der bisherige Entwurf ist funktional geprüft, aber vom Nutzer visuell abgelehnt. Er ist keine Designabnahme und keine produktive Azure-Lieferung.

## Messgrundlage

Die beiden vom Nutzer bereitgestellten Original-PNGs wurden in Originalauflösung ausgelesen: Outlook 2527×1167, Editor 2705×1230. Gemessen wurden Grenzen homogener Hintergrundflächen mit System.Drawing und visuell kontrollierte Trennlinien. Keine Konto- oder Nachrichteninhalte werden übernommen; die Screenshots bleiben außerhalb des Repositorys.

Alle folgenden Angaben sind ungefähr und in **Bildpixeln**, nicht CSS-Pixeln. Der Nutzer hat anschließend Windows-Skalierung 250 %, Bildschirmauflösung 3840×2160 und Browserzoom 100 % bestätigt. Ob beide früheren Ausschnitte unter exakt diesen Einstellungen aufgenommen wurden, ist nicht gesondert bestätigt. Der Editor-Ausschnitt zeigt die Titelzeile nur teilweise und den rechten Bereich nicht vollständig. Ganze Fensterhöhen, vollständige Spaltenanteile und exakte CSS-Schriftgrößen sind daraus nicht belastbar vergleichbar. Verhältnisse benachbarter Elemente innerhalb eines Bildes sind trotzdem brauchbar.

| Element | Outlook-Referenz | Abgelehnter Editor-Ausschnitt | Befund |
|---|---:|---:|---|
| Menüzeile | y≈120–204: 84 px | y≈28–118: 90 px | vergleichbare dargestellte Höhe |
| Befehlsleiste darunter | y≈204–310: 106 px | y≈118–344: 226 px | Editor deutlich zu hoch |
| Befehlsleiste / Menüzeile | ≈1,26 | ≈2,51 | relativ zur Menüzeile etwa doppelt so hoch |
| Äußere Bereichsleiste | x≈0–170: 170 px | x≈17–234: 217 px | sichtbar breiter; CSS-Vergleich braucht Skalierung |
| Innerer Navigationsbereich | x≈170–758: 588 px | x≈234–882: 648 px | sichtbar breiter; genaue Zielbreite noch kalibrieren |

Dies sind beobachtete Maße der konkreten Referenz, keine von Microsoft vorgeschriebenen Outlook-Pixelmaße.

## Konkrete Abweichungen

- Das vereinfachte Outlook-Menüband ist eine kompakte Befehlszeile. Der Entwurf verwendet hohe gerahmte Textbuttons mit zusätzlicher Gruppenbeschriftung und viel leerem Raum; er vermischt damit verschiedene Office-Menübandvarianten.
- Außenleiste, Menüband, Dokumenttitel, Untertitel, Ansichtsregister und Graphhinweis beanspruchen zusammen zu viel Fläche. Die zusätzliche Innenkopfstruktur ist durch die konkrete Outlook-Referenz nicht belegt.
- Zusammenhänge und Lesefassung werden sowohl im Menüband als auch unmittelbar darunter angeboten. Die Suche erscheint oben und im Baum mit identischer Benennung. Die Oberfläche benötigt klare Zuständigkeiten statt mehrfacher gleicher Auswahl.
- Die Navigation benutzt selbst gezeichnete Symbole. Microsoft stellt einen eigenen Fluent-System-Icons-Satz bereit. Strichstärke, Symbolgröße, aktiver/normaler Zustand und optische Ausrichtung müssen daraus konsistent übernommen werden.
- Hauptoberfläche und SVG-Graph skalieren unterschiedlich. Die Graphtexte werden mit der gesamten SVG-Geometrie skaliert und wirken im Nutzerbild deutlich kleiner als die Menü-/Baumtexte. Mindestlesbarkeit muss unabhängig von der Graph-Einpassung bleiben.
- Der innere Baum ist im Nutzerbild bereits vertikal scrollbar. Die bisherigen Prüfungen ohne Seitenscrollen bei festen CSS-Viewports beweisen kein passendes Layout auf dem tatsächlichen Nutzergerät mit dessen Zoom und Skalierung.
- Funktionale Browserprüfungen belegen Bedienbarkeit, nicht visuelle Übereinstimmung mit Microsoft. Visuelle Abnahme und automatischer Funktionscheck bleiben getrennte Nachweise.

## Verifizierte Microsoft-Quellen

Gelesen am 02.10.2026:

- [Fluent Layout](https://fluent2.microsoft.design/layout): Grundraster 4 px, ergänzende Werte 2/6/10, definierte Abstände und bewusste Ausrichtung; keine universelle feste Outlook-Spaltenaufteilung.
- [Fluent Typography](https://fluent2.microsoft.design/typography): Webschrift Segoe UI, Body 1 14 px / 20 px Zeilenhöhe, Caption 1 12/16, Subtitle 2 16/22. Die reale Referenz muss zusätzlich auf Zoom/Anzeigeskalierung kalibriert werden.
- [Fluent Design Tokens](https://fluent2.microsoft.design/design-tokens): benannte Werte für Farbe, Schrift, Abstände, Ecken, Linien und Zustände.
- [Fluent Web-Komponenten](https://fluent2.microsoft.design/components/web/react): Bausteine wie Button, Toolbar, Searchbox, Tablist, Tree und Tooltip. Fluent bietet React und Web Components; nicht jede Plattform hat automatisch identischen Funktionsumfang.
- [Fluent Entwicklung](https://fluent2.microsoft.design/get-started/develop): React v9 und JavaScript-Web-Components mit Theme-/Token-Unterstützung. Für die bestehende JavaScript-App zuerst die Web-Components-Eignung prüfen, nicht ohne Prüfung auf ein neues Framework wechseln.
- [Microsoft Fluent System Icons](https://github.com/microsoft/fluentui-system-icons): offizielle Symbole statt selbst gezeichneter Ersatzsymbole.
- [Office Datei / Backstage](https://support.microsoft.com/de-de/office/collab-files/start-backstage-with-the-file-tab): einheitliche Standardbefehle Öffnen, Speichern, Drucken.

Fluent ist die Bauteil- und Gestaltungsgrundlage. Die konkrete Outlook-Anordnung wird an der Nutzerreferenz gemessen; die allgemeinen Fluent-Seiten liefern keinen kompletten pixelgenauen Outlook-Nachbau.

## Was umsetzbar ist

1. Referenzgrenzen, Abstände, Farben und Größenverhältnisse aus dem Bild messen; eigene DOM-/CSS-Maße und Gerätepixelverhältnis im Browser protokollieren.
2. Daraus eine feste Maßtabelle und zentrale Gestaltungsvorgaben erstellen; Standardkomponenten und Symbole von Microsoft verwenden, soweit sie zur bestehenden App passen.
3. Eine schmale Office-Hülle mit Datei/Startseite/Ansicht/Hilfe, äußerer Aufgabenleiste Verstehen/Bearbeiten/Prüfen und jeweils passendem innerem Baum entwickeln. Zusätzliche Register nur bei konkretem Bedarf.
4. Zunächst dieselbe Hülle für alle drei Aufgaben visuell kalibrieren. Keine weiteren Produktfunktionen hinzufügen, bevor Höhen, Breiten, Lesbarkeit und Zustände passen.
5. Bildschirmbilder bei kontrollierter Fenstergröße, 100-%-Browserzoom und bekanntem Gerätepixelverhältnis prüfen; anschließend die reale Nutzerskalierung testen. Funktionsprüfungen und Bildvergleich ergänzen sich.
6. Nach visueller Entscheidung produktiv integrieren; ein Buildabschluss erfordert weiterhin das gesunde Azure-Image und die erwartete Live-Release-Kennung.

## Fehlende Information und Grenzen

Für die proportionale Korrektur reichen die vorhandenen Bilder. Windows-Anzeigeskalierung und Browserzoom sind nun bekannt. Die exakte nutzbare Browser-Innenfläche hängt noch von Fenstergröße und Browserleisten ab und kann im Editor selbst gemessen werden. Dafür werden keine Geheimnisse, Kontozugänge oder Zugriff auf das alte Datenrepository benötigt. Ein zusätzlicher Screenshot oder Figma ist keine Voraussetzung für den nächsten Korrekturschritt.

Derzeit steht das Outlook-Original als Bild zur Verfügung, nicht sein DOM oder sein CSS. Ein Screenshot verrät keine exakten CSS-Werte, versteckten Zustände oder Interaktionen. Reale Outlook-Maße könnten bei ausdrücklich bereitgestellter Browsermessung ergänzt werden; auf private Nachrichten muss dafür nicht zugegriffen werden. Interaktionen wie Hover, Fokus, Auswahl, deaktiviert, Menü geöffnet und eingeklappter Baum werden aus den öffentlichen Microsoft-Komponenten spezifiziert und im Editor geprüft.

## Bestätigte Zielumgebung und abgeleitete Maßtabelle

Nutzerbestätigt: 3840×2160 physische Pixel, Windows 250 %, Browser 100 %. Rechnerische logische Bildschirmfläche: 1536×864; Browserleisten und Fensterrahmen verkleinern die tatsächliche Innenfläche. 3840×2160 als CSS-Testfenster bildet diesen Arbeitsplatz nicht ab. Zusätzlich zur bisherigen Matrix müssen 1536×864 und eine konservative Fenster-Innenfläche von 1536×760 bei Gerätepixelverhältnis 2,5 geprüft werden. 760 ist eine Testannahme, kein gemessener Wert des Nutzerfensters.

Wenn auch die beiden ursprünglichen Ausschnitte bei diesen Einstellungen aufgenommen wurden, ergeben sich durch Division der Bildpixel durch 2,5 folgende **Referenzschätzungen**:

| Maß | Outlook in CSS-Pixeln, ungefähr | Bisheriger Entwurf | Korrekturgrundlage |
|---|---:|---:|---|
| Äußere Bereichsleiste | 68 | 88 | 68 px |
| Innerer Baum-/Navigationsbereich | 235 | 260 | 236 px, verstellbar |
| Menüzeile | 34 | 36 | 36 px |
| Kompakte Befehlsleiste | 42 | 91 | 44 px ohne zusätzliche Gruppenunterzeile |

Die Zielwerte 68/236/36/44 sind aus Referenzschätzung und Fluent-Abstandsraster abgeleitet. Sie sind keine von Microsoft fest vorgeschriebenen Outlook-Werte. Der Screenshot erklärt die fast exakt zur aktuellen CSS-Höhe passende übergroße Befehlsleiste: 91×2,5≈228 Bildpixel gegenüber gemessenen 226.

Für die nächste Umsetzung genügt die vorliegende Evidenz. Die App kann ihre nutzbare Innenfläche und das Gerätepixelverhältnis selbst messen. Kein neuer Kontozugang, Figma-Zugang, Secret oder weiterer Screenshot ist dafür erforderlich.

## Korrigierte Vorschau nach Nutzerhinweisen

Die nächste Vorschaufassung setzt die abgeleiteten Breiten und die 44-px-Befehlsleiste um, verwendet offizielle MIT-lizenzierte Fluent-Symbole und unterstützt ein reduziertes, vorübergehend ausgeklapptes sowie dauerhaft sichtbares Menüband. Die allgemeine Hilfe ist nur oben erreichbar; Objekt-Kontexthilfe nutzt ein Fragezeichen am rechten Detailbereich. Die äußere Leiste enthält nur die drei Arbeitsbereiche; die Suche liegt ausschließlich im Titelbereich und die Darstellungswahl unter Ansicht. Der ursprüngliche visuell abgelehnte Entwurf gilt weiterhin nicht als abgenommen; auch die Korrektur braucht visuelle Beurteilung.

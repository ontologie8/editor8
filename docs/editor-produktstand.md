> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# Produktstand des NaC-Ontologie-Editors

Stand: 01.10.2026. Bezugsrahmen sind ausschließlich die 20 Vorgangsarten in [`catalog/nac-baseline.json`](../catalog/nac-baseline.json). Die Oberfläche bearbeitet fachliche **Vorlagen**; reale Akten und laufende Vorgänge gehören nicht in dieses Repository.

#> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# Was die Oberfläche bereits kann

| Aufgabe | Umgesetzter Weg |
| --- | --- |
| Einen Fall verstehen | Direkt sichtbarer Fachgraph mit den bereits verknüpften Bausteinen und ihren Beziehungen; bisher unverknüpfte Bausteine stehen unmittelbar darunter. „Alle“ zeigt auf Wunsch sämtliche Bausteine im Graphen. Eine Suche öffnet den gewünschten Baustein ohne lange Auswahlliste. Die Auswahl zeigt das direkte Umfeld und die Beziehungen neben dem Graphen; auf schmalen Bildschirmen erscheinen gruppierte Karten und eine Detailfläche am unteren Rand. Beschreibung, Quellen und NaC-Prozessablauf stehen im Dialog „Info zum Fall“. |
| Einen Baustein finden | Suche im Fall und über alle 20 Fälle; ein Treffer öffnet unmittelbar den betreffenden Baustein. Der gemeinsame Suchstand ist an einen Git-Commit gebunden. |
| Fachliche Inhalte pflegen | Strukturierte Felder für Fragen, Dokumenttypen, Entscheidungen, Prüfschritte, Nachweistypen und ihre Beziehungen. Vor dem Speichern erscheint eine fachliche Änderungsvorschau. Turtle bleibt Pflegequelle. |
| Gemeinsame Begriffe pflegen | Klassen und Eigenschaften bearbeiten; die technische Verwendung in den 20 Fällen sehen und zu betroffenen Fällen springen. |
| Änderungen prüfen | Getrennte Git-Branches und Pull Requests, Quellenstand und Begründung, fachlicher Prüfkorb, begründete Freigabe durch ein anderes eingetragenes Notarkonto auf dem geprüften Commit. |
| Arbeit fortsetzen und wechseln | Eigene Fall- oder Vokabularzweige ohne Pull Request nach erneuter Anmeldung wieder öffnen, auch wenn noch keine Änderung gespeichert wurde. Mit „Entwurf ablegen“ in den Lesemodus wechseln und einen anderen Zweig öffnen. Ein Fallentwurf kann nur seinen ausgewählten Fall ändern; andere Fälle sind lesbar. Ungespeicherte Browser-Eingaben sind davon nicht umfasst. |
| Frühere Fassung prüfen | Die letzten 20 GitHub-Änderungen eines Falls ansehen. Eine frühere Fassung kann nach einer fachlichen Differenzvorschau als neuer Branch und Pull Request vorgeschlagen werden. Der Editor akzeptiert nur eine vollständig darstellbare RDF-Fassung; die notarielle Prüfung bleibt erforderlich. |

Die [Palantir-Dokumentation zum Ontology Manager](https://www.palantir.com/docs/foundry/ontology-manager/overview) beschreibt darüber hinaus die Pflege von Objekttypen, Eigenschaften, Aktionen und Datenanbindungen. Ihre [Usage-Ansicht](https://www.palantir.com/docs/foundry/ontology-manager/view-usage) bezieht auch tatsächliche Lese- und Schreibzugriffe von Anwendungen ein. Unsere Verwendungsanzeige zählt dagegen RDF-Aussagen in den 20 Fallvorlagen; sie sagt nichts über laufende Akten oder Anwendungen aus. Palantir bietet eine [globale und objektbezogene Änderungshistorie mit Wiederherstellung](https://www.palantir.com/docs/foundry/ontology-manager/restore-changes). Der NaC-Editor zeigt derzeit die fallbezogene GitHub-Historie; eine frühere Fassung erzeugt ausschließlich einen neuen Prüfentwurf und ändert `main` nicht direkt.

Das Ziel ist deshalb ein **vollwertiger Editor für den abgegrenzten NaC-Fachkatalog**, keine Kopie der gesamten Foundry-Plattform. BPMN bleibt in NaC für Abläufe zuständig. SHACL ist eine spätere Prüfschicht und wird erst nach einer konkreten Shapes-Entscheidung bearbeitet.

Die [Editor-Roadmap vom 01.10.2026](editor-roadmap.md) priorisiert den nachgewiesenen Schreibweg, reproduzierbare Browserprüfungen und Bedienqualität vor weiteren Modellierungsfunktionen. Sie enthält Abnahmekriterien und grobe Token-Schätzungen für spätere Ausbauschritte.

Die [UI-Prüfung mit Korrektur vom 30.09.2026](editor-ux-audit-2026-09-29.md) trennt Oberflächengestaltung und technische UI-Abnahme von der notariellen Fachprüfung. Die App zeigt keine Turtle-Rohansicht; die technische Fassung bleibt im Git-Repository.

Die lokale Browserprüfung des aktuellen UI-Entwurfs bestätigte alle 20 Fallansichten einschließlich ihrer jeweiligen sichtbaren Graph-Bausteine. Am Immobilienkaufvertrag wurden die Ansicht „Verknüpft“ (14 Bausteine, 8 Verbindungen), der Zugang zu 8 unverknüpften Bausteinen, die Gesamtansicht, die nichtmodale Detailfläche, Zoom, Suche mit Tastatur, die fallbezogene Info, die Verbindungswahl per Suche und das Öffnen der Bearbeitungsfelder durchgeklickt. Bei 1438, 1100 und 500 Pixeln Breite traten in diesen Prüfwegen keine horizontalen Seitenüberläufe auf. Eine notarielle Fachfreigabe wurde dadurch nicht erteilt.

Die wiederholbare [Browserprüfung](../tests/editor.browser.spec.mjs) nutzt den echten Cloud-Editorserver mit einem lokalen GitHub-Ersatz. Sie öffnet alle 20 Fallmodule aus Turtle, prüft Suche und Tastatur, einen schmalen Bildschirm sowie Bearbeiten, Vorschau, Speichern und Einreichen. GitHub Actions führt sie als eigenen Job aus. Der Test schreibt keine Falldaten nach GitHub und ersetzt den noch offenen angemeldeten Schreibdurchlauf am gehosteten Piloten nicht.

#> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# Offene Produktabnahme

1. Die reale GitHub App ist auf `notariat8/ontology` begrenzt installiert; `ofunk` konnte sich anmelden und Fälle lesen. Offen sind ein echter Bearbeitungs-/PR-Test und der Prüfweg mit einem zweiten, notariellen Konto.
2. Der HTTPS-Host mit Azure Key Vault und genau einer Editor-Instanz ist als Pilot bereitgestellt. Der technische Stand und seine Grenzen stehen in [`editor-hosting.md`](editor-hosting.md). Die kanonische Webadresse der Ontologie wird später entschieden.
3. Den manuellen Merge-Weg mit den eingeladenen Konten nachweisen: dokumentiertes notarielles Review auf dem aktuellen Commit, grüne CI und Prüfung durch die merge-verantwortliche Person. Ein technisch erzwungener Gate bleibt als spätere Härtung in [Issue #7](https://github.com/notariat8/ontology/issues/7). Die fachlich geprüften Anzeigenamen technischer NaC-Werte stehen in [Issue #8](https://github.com/notariat8/ontology/issues/8).

**Historische Token-Schätzung vor dem Hosting, kein Restaufwand:** Für GitHub-App-Integration, Bereitstellung, Sicherheits- und Nutzertests samt Korrekturen wurden zuvor grob **20.000–40.000 Modell-Token** geschätzt. Hosting, App-Installation und erster Login sind inzwischen umgesetzt; aus dem Repository lässt sich weder der tatsächliche Verbrauch noch eine belastbare neue Restschätzung ablesen. Notarielle Fachprüfung und SHACL-Implementierung waren in der ursprünglichen Spanne nicht enthalten.

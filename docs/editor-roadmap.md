> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# Roadmap für den NaC-Ontologie-Editor

Stand: 01.10.2026. Diese Roadmap leitet konkrete nächste Schritte aus dem Vergleich mit Protégé Desktop, WebProtégé und Fluent Editor ab. Sie ist ein Umsetzungsplan für den auf 20 NaC-Vorgangsarten begrenzten Editor, keine fachliche Freigabe neuer Ontologieinhalte.

#> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# Ausgangsstand und Leitentscheidung

Der [aktuelle Produktstand](editor-produktstand.md) umfasst Fallgraph, fallbezogene und katalogweite Suche, strukturierte Pflegefelder, eine fachliche Änderungsvorschau, GitHub-Entwürfe und Pull Requests, fallbezogene Historie, Vokabularpflege und eine Anzeige der technischen Verwendung in den 20 Fällen. Die eigenen Parser-/Serializer-Tests prüfen bereits den semantisch verlustfreien Durchlauf aller 20 Fallmodule. Lokale Browserprüfungen für die Arbeitsfläche liegen vor; ein reproduzierbarer Browserlauf in CI und ein echter angemeldeter Speichern-/PR-Durchlauf auf dem aktuellen Azure-Stand fehlen. Der Editor-Stand liegt im [Draft-PR #6](https://github.com/notariat8/ontology/pull/6).

**Produktgrenze:** `ontology/core.ttl` und die 20 Fallmodule bleiben Pflegequelle. GitHub speichert die Änderungen; Mermaid entsteht aus Turtle. Die App speichert keine realen Aktenwerte. NaC-BPMN bleibt Quelle für Abläufe. Notarielle Fachfreigabe und technische UI-Abnahme sind getrennte Vorgänge. Wir bauen keinen allgemeinen OWL-Editor und keinen zweiten dauerhaften Ontologiedatenspeicher.

Aus Protégé übernehmen wir **prüfbare Modellqualität und Interoperabilität**, aus WebProtégé **kontextbezogene Zusammenarbeit**, aus Fluent Editor **geführte verständliche Formulierungen**. Wir kopieren ihre allgemeinen Funktionskataloge nicht: Reasoner, freie OWL-Axiome und SWRL-Debugging bringen den heutigen 20 Fallvorlagen keinen belegten Nutzen. Die ersten Investitionen gelten der Zuverlässigkeit des bereits vorhandenen Schreibwegs und der Bedienqualität.

#> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# Reihenfolge und Abnahme

Die Tokenangaben sind grobe **zusätzliche Modell-Token für Implementierung, Tests und Korrekturen**, keine gemessenen Verbräuche oder Kalendertermine. Externe Konten, Fachprüfung und eventuelle Anbieterbedingungen sind darin nicht enthalten. Nach jedem Paket wird anhand der Abnahme entschieden, ob das nächste noch sinnvoll ist.

| Schritt | Ergebnis | Grobe Modell-Token |
| --- | --- | ---: |
| **P0** | Produktweg im Browser und als Prüf-PR nachgewiesen | 14.000–26.000 |
| **P1** | Durchgängige, aufgeräumte Bedienung | 12.000–22.000 |
| **P2** | Änderungen direkt im Graphen verständlich | 12.000–22.000 |
| **P3** | Rückfragen am betroffenen Baustein | 10.000–18.000 |
| **P4** | Geführte deutsche Eingabe von Beziehungen | 12.000–24.000 |
| **P5** | Versionierte SHACL-Regeln und verständliche Befunde | 18.000–32.000 nach Shapes-Entscheidung |

##> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# P0 · Produktweg absichern

**Umsetzung:** Die bisher nur lokal ausgeführten Browserwege als wiederholbaren Test in `tests/` und CI aufnehmen: Fallwahl, Graph, Suche, Bearbeitungsfelder, Vorschau, 20 Fallmodule, Tastatur und schmale Breiten. Den gehosteten Ablauf mit angemeldetem Editor an einer echten, reviewbaren Korrektur bis zum Pull Request zur Fachprüfung nachweisen. Kein Testinhalt wird nach `main` gemergt.

**Abnahme:** CI prüft Browser und API. Der live erzeugte PR verändert nur das gewählte Fallmodul und dessen generierte Seite. Erwartete und tatsächliche GitHub-Dateien, Commit und Sichtbarkeit sind dokumentiert.

**Teilstand 01.10.2026:** Der Browserlauf für alle 20 Fälle, Suche und Tastatur, drei Bildschirmbreiten sowie Bearbeiten, Vorschau, Speichern und Einreichen gegen einen lokalen GitHub-Ersatz ist im Repository und als CI-Job angelegt. Lokal sind fünf Browserprüfungen erfolgreich. Der angemeldete Schreib- und PR-Durchlauf am gehosteten Piloten bleibt als gesonderter Live-Nachweis offen.

##> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# P1 · Bedienqualität und Wartbarkeit

**Umsetzung:** Die gewachsene `editor/app.js` und mehrfach überlagerte CSS-Regeln in klar getrennte Zustände, Ansichten und wiederverwendbare Bedienelemente ordnen. Lesemodus, Entwurf, Fehler, leere Ansichten, Fokus und ungespeicherte Eingaben durchgängig gestalten. Struktur und Datenvertrag bleiben gleich.

**Abnahme:** Alle 20 Fälle bleiben funktional gleich. Automatisierte Tastaturprüfungen und visuelle Prüfungen für Desktop, mittlere Breite und Mobil bestehen. Der Umbau verändert keine TTL-Datei.

##> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# P2 · Änderungsfolgen sichtbar machen

**Umsetzung:** Nach dem Vorbild der Modellprüfung in Protégé die vorhandene Textvorschau und Vokabularanzeige um einen **Graphvergleich vor und nach einer Änderung** ergänzen. Hinzugefügte, entfernte und geänderte Bausteine und Beziehungen sowie betroffene Nachbarn und Fälle markieren. Jede Aussage muss auf eine RDF-Differenz zurückführbar sein.

**Abnahme:** Änderungen an Knoten oder Beziehungen sind in Text und Graph gleich erklärt. Tests vergleichen die Erklärung mit den tatsächlichen Tripeln; es gibt keine erfundene fachliche Wirkung oder Aktennutzung.

##> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# P3 · Rückfragen am Gegenstand

**Umsetzung:** Nach dem Vorbild von WebProtégé aus dem bestehenden Prüfkorb direkt zum betroffenen Baustein oder zur Beziehung springen. Rückfragen mit stabiler Kennung und geprüftem Commit an den GitHub-PR binden. Zuvor GitHub-App-Rechte und das Verhalten bei späteren Commits prüfen. Es entsteht keine zweite Kommentardatenbank.

**Abnahme:** Nach einem neuen Commit sind Kommentare eindeutig dem alten oder neuen Stand zugeordnet. Nur berechtigte Konten können fachliche Entscheidungen dokumentieren. Die Live-Abnahme braucht das später benannte Notarkonto.

##> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# P4 · Geführte deutsche Formulierungen

**Umsetzung:** Angeregt durch Fluent Editor eine Beziehung als kontrollierten deutschen Satz aus **vorhandenen** Bausteinen und zulässigen Beziehungstypen bilden, etwa „Prüffrage A erfordert Dokumenttyp B“. Vor dem Speichern Richtung, Beziehungstyp und genaue fachliche Änderung zeigen. Freie Sprache oder KI-Ausgaben schreiben niemals ungeprüft Turtle.

**Abnahme:** Jeder Satz entspricht genau einer zulässigen RDF-Änderung und lässt sich wieder gleich anzeigen. Fachlich geprüfte Anzeigenamen aus [Issue #8](https://github.com/notariat8/ontology/issues/8) sind Voraussetzung für verbindliche Formulierungen.

##> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# P5 · SHACL pflegen

**Umsetzung:** Zuerst einen begrenzten Katalog von Strukturregeln und getrennt davon fachliche Regeln entscheiden. Shapes als versionierte Dateien im Repository speichern, gegen alle 20 Fallmodule ausführen und verständliche Fehlermeldungen im Editor anzeigen. Ein Shape-Editor kommt erst nach dem geprüften Shapes-Vertrag.

**Abnahme:** Kommandozeile und CI liefern dieselben Befunde. Jede Regel hat einen Testfall und eine verständliche Erklärung; fachliche Regeln wurden notariell geprüft.

#> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# Früher Entscheidungstest gegen fertige Werkzeuge

Bevor P2–P5 umfangreich gebaut werden, prüfen wir die tatsächliche Austauschbarkeit an `ontology/core.ttl` sowie mindestens Immobilienkaufvertrag und Erbausschlagung: Import in Protégé Desktop, WebProtégé und, falls eine nutzbare Installation verfügbar ist, Fluent Editor; eine kleine Änderung; Export; Vergleich der RDF-Tripel, Kennungen, Quellen und Dateigrenzen. Für WebProtégé wird zusätzlich geprüft, ob ein **Rückweg als GitHub-PR** für genau unsere Turtle-Module praktisch funktioniert. Die öffentlich beschriebenen [GitHub-Integrationsdienste](https://github.com/protegeproject/webprotege-gh-history-service) belegen einen Import der Historie, noch keinen für NaC verifizierten verlustfreien PR-Rückweg. Ein Anbieterzugang oder die Einrichtung des [mehrteiligen WebProtégé-Stacks](https://github.com/protegeproject/webprotege-deploy) darf P0/P1 nicht aufhalten.

Ergebnis dieses Tests ist eine kurze Entscheidung: **übernehmen**, **ergänzend einsetzen** oder **für diesen Katalog nicht einsetzen**, jeweils mit reproduzierbarem RDF-Vergleich. Geschätzt 8.000–16.000 Modell-Token für den Vergleich ohne aufwendige Fremdinstallation; eine zusätzliche WebProtégé-Bereitstellung wird erst nach Sichtung ihrer Betriebsfolgen entschieden.

#> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# Erstes umsetzbares Arbeitspaket

P0 beginnt ohne neue fachliche Aussagen: (1) das lokale Browser-Prüfskript in ein wartbares Repository-Testwerkzeug überführen; (2) den bestehenden Mock-GitHub-Ablauf für Erstellen, Vorschau, Speichern und Einreichen vom Browser aus prüfen; (3) den Lauf in `.github/workflows/validate.yml` aufnehmen; (4) die 20 Fallansichten und die entscheidenden Tastatur-/Breitenwege prüfen; (5) anschließend mit `ofunk` eine **echte fachlich sinnvolle Änderung** über den gehosteten Editor als Pull Request zur Fachprüfung vorführen. Für Schritt 5 muss eine konkrete Korrektur vorliegen; ein erfundener Fallinhalt wird nicht als Test geschrieben. Das zweite notarielle Konto ist erst für die Live-Prüfung von P3 und die fachliche Freigabe erforderlich.

Nach P0/P1 ist eine technische Release-Kandidatur prüfbar. Ein produktiver fachlicher Betrieb braucht weiterhin den dokumentierten notariellen Review-Weg; der optionale technisch erzwungene Merge-Gate bleibt in [Issue #7](https://github.com/notariat8/ontology/issues/7). Ohne belegten Nutzwert wird weder ein allgemeiner OWL-Reasoner noch eine zweite Ontologie-Datenbank Teil dieses Editors.

#> Herkunft: aus dem ontology-Editorzweig übernommen. Historische Azure-/PR-Nachweise sind keine neue Deploymentbestätigung. Softwarepflege erfolgt seit 2026-10-01 in editor8; Daten bleiben in notariat8/ontology.

# Quellen für den Vergleich

- [Protégé Desktop und WebProtégé: Funktionen und Formate](https://protege.stanford.edu/software/)
- [WebProtégé: selbst gehosteter Dienstverbund](https://github.com/protegeproject/webprotege-deploy)
- [WebProtégé: Import von GitHub-Ontologiehistorie](https://github.com/protegeproject/webprotege-gh-history-service)
- [Fluent Editor: Controlled English, Diagramme und Zusammenarbeit](https://www.cognitum.eu/semantics/FluentEditor/)

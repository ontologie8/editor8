# Roadmap für editor8

Stand: 06.10.2026. editor8 pflegt Software, Oberfläche, Anmeldung, Datenadapter und Betrieb. Fachmodelle liegen im ausdrücklich gewählten Datenrepository. Die 20 kanonischen Vorgangsarten gehören zu `notariat8/ontology`; der Editor übernimmt die Fallanzahl aus dem jeweiligen Katalog.

Herkunft: Die ursprüngliche Planung wurde aus dem ontology-Editorzweig übernommen. Historische Nachweise dieses Zweigs sind keine Deploymentbestätigung für editor8. Der heutige Stand und verbleibende Abnahmen sind hier getrennt aufgeführt.

## Nachgewiesener Stand

Die Office-Oberfläche wurde mit [editor8 PR #4](https://github.com/ontologie8/editor8/pull/4) ausgeliefert. Der Softwarecommit `eceae59c0b62a258a5b496e88a9e17eff56a1122` wurde auf Azure als aktive gesunde Revision geprüft; Release-Kennung und ausgelieferte HTML-, CSS- und JavaScript-Dateien stimmten überein. Das ist der belegte Ausgangsstand dieser Aktualisierung. Die laufende Kennung steht unter `/api/release`; spätere Builds benötigen einen eigenen Nachweis.

Umgesetzt sind Verstehen → Bearbeiten → Prüfen, äußere Bereichsnavigation, innerer Datenbaum, Graph mit rechter Detail-/Bearbeitungsfläche, einklappbares Office-Menüband, deutsche Standardbefehle, allgemeine und kontextbezogene Hilfe, Drucken, Repository-Auswahl und Release-Anzeige. [DESIGN.md](../DESIGN.md) ist die verbindliche UI-Vorgabe.

Die Software-CI prüft Python, JavaScript, synthetische Browserwege und den Container. OAuth-Prüfungen verwenden künstliche Codes und Provider-Antworten; sie prüfen Browserbindung, Wiederverwendung, Fehlerdiagnose und die Sitzungserstellung. Die Datenintegration umfasst 48 Python- und fünf Browserprüfungen gegen den getrennten Notardatensatz. Der regelmäßige Workflow liegt ausschließlich im privaten Datenrepository; genaue Revisionspaare und Wiederholung beschreibt [Datenintegration in CI](editor-integration-ci.md).

Der [Trainingsbereich](../training/README.md) enthält sechs Lektionen mit 18 Browserfolien, Lernfragen und einer rein künstlichen Speicherübung. Das [Produkthandbuch](product/README.md) beschreibt acht Themen von Einstieg bis Fehlerbehandlung. JSON-Quellen erzeugen Browser- und Markdownfassung gemeinsam; CI prüft ihren Gleichstand. Training und Handbuch gehören zur Pflege jedes geänderten Produktablaufs. Die produktive Zwei-Personen-Abnahme bleibt offen.

GitHub bleibt die versionierte Datenquelle. Turtle ist Pflegequelle, Mermaid wird daraus erzeugt. Die App speichert keine realen Aktenwerte. NaC bleibt Quelle der Prozessabläufe. Technische Prüfung und notarielle Fachfreigabe sind getrennte Nachweise.

## Reihenfolge und offene Abnahmen

| Paket | Bereits umgesetzt | Verbleibende Arbeit |
| --- | --- | --- |
| **P0 – Produktweg absichern** | Wiederholbare Software-/Browser-CI, getrennte Datenintegration, Azure-Auslieferung mit Release- und Assetprüfung | Echte angemeldete fachlich sinnvolle Änderung über Azure bis zum Daten-PR; Zwei-Personen-Abnahme auf Nutzerwunsch bis zur Nachfrage am 01.12.2026 zurückgestellt |
| **P0 – Benutzerverwaltung entkoppeln** | GitHub-Anmeldung und Datenrechte, getrennte fachliche Rollen; externe App-Autorisierung ermöglicht | Statische Nutzer- und Rollenlisten aus Azure beziehungsweise dem Image ablösen. Benutzerverwaltung ohne Build oder Container-Revision; Anbieterentscheidung und Migration gemäß [IAM-Zielbild](iam-zielbild.md) |
| **P0 – Betreiber und Dateninstallation trennen** | Bestehende App nach `ontologie8` übertragen; Name, Homepage, unveränderte Identität und fortbestehende Installation in `notariat8` geprüft; Betriebshelfer korrigiert; Nutzer-Screenshot belegt den geöffneten Editor als `ofunk` mit geladenen Notar-Fachmodellen nach der Übertragung | Genaue Installationsauswahl zusätzlich prüfen; aktuelle Nachweise unter [App-Eigentum und Dateninstallation](github-app-ownership.md) |
| **P1 – Bedienqualität und Wartbarkeit** | Office-Struktur, kompakte Desktopmaße, fachliche Hilfe, Hover-/Fokushinweise und Kontextmenüs; eigene Interaktions- und Wiederaufnahmeschicht; offene Modelleingaben und Begründungen nach Neuladen oder erneuter Anmeldung prüfen und wieder aufnehmen | Übrige `app.js` in klare Zustände und Ansichten ordnen; weitere Fehler und leere Ansichten prüfen; abschließende Bedienabnahme |
| **P2 – Änderungsfolgen sichtbar machen** | Text und grafischer Vorher/Nachher-Vergleich aus tatsächlichen RDF-Differenzen für Fallmodelle und gemeinsame Begriffe, einschließlich direktem Umfeld und Prüfkorb | Darstellung großer Änderungsumfänge und fachliche Verständlichkeit gemeinsam abnehmen; technische Verwendung bleibt von tatsächlicher Aktennutzung getrennt |
| **P3 – Rückfragen am Gegenstand** | Prüfkorb, begründete Änderungswünsche und commitgebundene Freigabe | Direkt zum betroffenen Baustein oder zur Beziehung springen; Rückfragen mit stabilen Kennungen und geprüftem Stand verbinden |
| **P4 – Geführte deutsche Formulierungen** | Strukturierte Felder und Beziehungsauswahl | Kontrollierte Sätze aus vorhandenen Bausteinen und zulässigen Beziehungen; fachlich freigegebene Anzeigenamen |
| **P5 – SHACL pflegen** | Als spätere Prüfschicht geplant | Regelkatalog und Shapes-Vertrag entscheiden; Regeln im Datenrepository versionieren und Befunde im Editor erklären |

### P0: echter Schreib- und Prüfweg

Der Live-Nachweis braucht eine konkrete, fachlich sinnvolle Korrektur. Eine Person meldet sich an, erstellt einen Entwurf, bearbeitet und bestätigt den Vergleich, speichert und reicht einen tatsächlichen PR im Datenrepository ein. Der Nachweis nennt Datenbasis, erwartete und tatsächliche Dateien, Commit und PR. Erfundenen Testinhalt nicht nach Daten-`main` übernehmen.

`hheise-ch` und `jjwarzecha` sind im Datenziel als notarielle Reviewer eingetragen. Die reale Prüfung einer Änderung einer anderen Person, die Freigabe auf dem aktuellen Commit und der anschließende manuelle Merge-Weg bleiben nachzuweisen. Die Registrierung ist keine bereits durchgeführte Abnahme. [Issue #7](https://github.com/notariat8/ontology/issues/7) bleibt eine optionale technische Erzwingung des Freigabeschritts.

**Nutzerentscheidung vom 06.10.2026:** Aktuell arbeitet nur der Nutzer selbst mit. Die reale Zwei-Personen-Abnahme ist deshalb zurückgestellt und blockiert die beauftragte Softwareentwicklung nicht. Am 01.12.2026 wird einmal nach einer zweiten tatsächlichen Person gefragt. Zwei Konten derselben Person ersetzen diese Abnahme nicht; fachliche Freigaberegeln bleiben bestehen.

### P1: Zustände und Bedienung

Der Speicherablauf hat einen eigenen Zustand für Vorschau und laufende Anfrage. Wiederholtes Speichern erzeugt keine parallelen Anfragen; bestätigt wird die zuvor geprüfte Fassung. Fehler bleiben im Vorschaufenster sichtbar, offene Eingaben erhalten. Abmelden fragt vor dem Verwerfen. Langsame Fallantworten dürfen eine spätere Auswahl oder neue Eingaben nicht ersetzen. Synthetische Browserprüfungen decken diese Verzögerungs-, Fehler- und Abbruchwege ab. Die vollständige Aufteilung von `app.js` und die abschließende Bedienabnahme bleiben offen.

Alle Vorgangsarten des angegebenen Datenkatalogs müssen funktional gleich bleiben. Tastatur-/Fokusprüfungen und sichtbare Zustände für Lesen, ungespeicherte Änderung, Entwurf, Einreichen und Fehler ergänzen. Primär ist die bildschirmfüllende Desktop-App bei 27–34 Zoll und 2K–4K; Windows-Skalierung und reduzierte Browserhöhe sind zu berücksichtigen. Mobil ist sekundär. Dieser Umbau verändert keine Fachmodelle.

### P2: Graphvergleich

Umgesetzt ist der Vergleich tatsächlicher RDF-Differenzen zwischen gespeicherter und vorgeschlagener Fassung. Fallmodelle und gemeinsame Begriffe zeigen hinzugefügte, entfernte und geänderte Bausteine sowie hinzugefügte oder entfernte Beziehungen mit dem direkten Umfeld. Beide Ansichten verwenden gleiche Positionen und stabile Kennungen. Wörter, Farben und Feldvergleich erklären dieselbe Änderung wie die Textvorschau. Der Prüfkorb nutzt denselben Vergleich. Tests führen die Darstellung auf tatsächliche RDF-Tripel zurück; daraus folgt keine unbelegte fachliche Wirkung oder Aktennutzung.

### P3: Rückfragen und Bezug zum geprüften Stand

Aus dem Prüfkorb zum betroffenen Gegenstand springen. Rückfragen mit stabiler Kennung und Commit an GitHub binden, ohne zweite Kommentardatenbank. Nach späteren Commits muss erkennbar bleiben, welcher Stand gemeint war. App-Rechte und das Verhalten bei neuen Commits prüfen; den Live-Weg mit zwei tatsächlichen Personen nachweisen.

### P4: kontrollierte deutsche Eingabe

Eine Beziehung als deutschen Satz aus vorhandenen Bausteinen und zulässigen Typen bilden. Vor dem Speichern Richtung, Beziehungstyp und genaue Änderung zeigen. Jede Formulierung entspricht genau einer zulässigen RDF-Änderung. Freie Sprache oder KI-Ausgaben schreiben keine ungeprüften Fachmodelle. [Issue #8](https://github.com/notariat8/ontology/issues/8) zu fachlichen Anzeigenamen ist offen und gehört ins Datenprojekt.

### P5: versionierte SHACL-Regeln

Zuerst Strukturregeln und getrennt davon fachliche Regeln festlegen. Shapes im Datenrepository versionieren, gegen dessen Fallmodule ausführen und verständliche Befunde im Editor anzeigen. Kommandozeile und CI müssen gleiche Ergebnisse liefern; jede Regel braucht einen Test und eine Erklärung. Fachregeln benötigen notarielle Prüfung. Ein Shape-Editor folgt erst auf einen geprüften Shapes-Vertrag.

## Nächstes Arbeitspaket

Zuerst die Benutzerverwaltung gemäß [IAM-Zielbild](iam-zielbild.md) entkoppeln: neue Nutzer und fachliche Rollen ohne Softwareauslieferung oder Container-Revision verwalten. Die Anbieterentscheidung ist noch offen. Unabhängige P1-Arbeit weiterführen: übrige Ansichten und Fehlerzustände ordnen, große Änderungsvergleiche und die fachliche Bedienung abnehmen. Den echten Schreib-/PR-Weg mit einer sinnvollen Korrektur separat nachweisen; die zurückgestellte Zwei-Personen-Abnahme nicht als Softwareblocker behandeln. Danach P3 mit Rückfragen am Gegenstand konkretisieren. Die [Literatureinordnung](research/2026-10-06-editor-scope-semantic-books.md) begrenzt den Produktumfang auf fachliche Modellpflege. Historische Token-Schätzungen sind keine aktuelle Restaufwandsschätzung.

Vor umfangreichen Investitionen in P2–P5 bleibt ein begrenzter Interoperabilitätstest mit Protégé/WebProtégé und gegebenenfalls Fluent Editor sinnvoll: Import, kleine Änderung, Export und Vergleich von RDF-Tripeln, Kennungen, Quellen und Dateigrenzen. Eine Fremdinstallation darf P0/P1 nicht aufhalten. Ein allgemeiner OWL-Reasoner, freie OWL-Axiome und eine zweite dauerhafte Ontologiedatenbank sind ohne belegten Bedarf nicht vorgesehen.

# Produktstand von editor8

Stand: 02.10.2026. Dieses Repository enthält die Software. Die Oberfläche bearbeitet fachliche Vorlagen aus einem getrennten, ausdrücklich konfigurierten Datenrepository. Der aktuelle NaC-Adapter wird gegen die 20 kanonischen Vorgangsarten von `notariat8/ontology` geprüft; die Fallanzahl ist im Editor nicht fest codiert. Reale Aktenwerte gehören nicht in diese Projekte.

Herkunft: Die frühere Produktbeschreibung wurde aus dem ontology-Editorzweig übernommen. Historische Nachweise bleiben von der Auslieferung der getrennten Software unterschieden.

## Umgesetzte Funktionen

| Aufgabe | Umgesetzter Weg |
| --- | --- |
| Orientierung | Office-Arbeitsfläche mit Verstehen, Bearbeiten und Prüfen außen, Datenbaum innen, Arbeitsbereich in der Mitte und Details/Formular rechts. Datei, Startseite, Ansicht und Hilfe oben; Menüband einklappbar, Datenbaum unabhängig schaltbar. |
| Datenziel wählen | Repository-Liste aus `config/data-repositories.json`, gefiltert nach Zulassung und tatsächlichem GitHub-Zugriff. Zielwechsel ist sitzungsbezogen. Das Software-Repository ist kein Datenziel. |
| Einen Fall verstehen | Fachgraph, direkte Beziehungen, Zugang zu unverknüpften Bausteinen, Gesamtansicht und Auswahl des Umfelds. Beschreibung, Quellen und NaC-Prozessablauf über Informationen. |
| Finden und erklären | Suche im Fall und im Datenkatalog; allgemeine Hilfe und künstliche Beispiele oben, kontextbezogene Hilfe am Baustein. |
| Fachliche Inhalte pflegen | Strukturierte Felder für Fragen, Dokumenttypen, Entscheidungen, Prüfschritte, Nachweistypen und Beziehungen. Beim Bearbeiten bleibt der Graph sichtbar; vor dem Speichern fachlicher Textvergleich mit Bestätigung. Turtle bleibt Pflegequelle. |
| Gemeinsame Begriffe pflegen | Klassen und Eigenschaften sowie Anzeige ihrer technischen RDF-Verwendung im Datenkatalog. |
| Änderungen prüfen | Entwurfsbranches und PRs, Quellenstand, Begründung, Prüfkorb, begründete Änderungswünsche und Freigaben auf einem geprüften Commit durch ein anderes eingetragenes Notarkonto. |
| Arbeit fortsetzen | Eigene gespeicherte Fall-/Vokabularzweige wieder öffnen oder ablegen; ungespeicherte Browser-Eingaben sind keine dauerhafte Speicherung. |
| Frühere Fassung prüfen | Fallbezogene GitHub-Historie; Wiederherstellungsvorschlag erzeugt nach Differenzvorschau einen neuen Prüfentwurf. |
| Drucken und Release vergleichen | Lesefassung unter Datei → Drucken. Editor-Release in der Fußzeile verlinkt den eingebetteten Softwarecommit; voller SHA unter `/api/release`. |

[DESIGN.md](../DESIGN.md) hält die verbindlichen Desktopmaße, deutsche Befehle und Microsoft-Referenzen fest. Menüs und Repository-Auswahl bleiben ohne Seitenscrollen erreichbar; Baum und Arbeitsinhalt können intern scrollen. Primär sind 27–34 Zoll bei 2K–4K, einschließlich Windows-Skalierung; Mobil ist sekundär.

## Technischer Nachweis

Die Office-Auslieferung aus [PR #4](https://github.com/ontologie8/editor8/pull/4), Commit `eceae59c0b62a258a5b496e88a9e17eff56a1122`, wurde als aktive gesunde Azure-Revision mit passender Release-Kennung und übereinstimmenden HTML-/CSS-/JavaScript-Hashes geprüft. Spätere Releases benötigen denselben eigenen Nachweis. Der Host ist in [Betrieb](editor-hosting.md) beschrieben.

Die Software-CI führt 13 Python-Tests, die JavaScript-Syntaxprüfung, sechs [synthetische Browserprüfungen](../tests/smoke.browser.spec.mjs) und Containerprüfungen aus. Die getrennte Datenintegration umfasst 48 Python- und fünf [Browserprüfungen](../tests/integration/editor.browser.spec.mjs), einschließlich semantischem Durchlauf aller 20 gepflegten Fälle. Der regelmäßige private Workflow und reproduzierbare Revisionspaare stehen unter [Datenintegration in CI](editor-integration-ci.md).

Die UI wurde bei 1536 × 864 CSS-Pixeln und Geräteskalierung 2,5 sichtbar geprüft; zusätzliche Größenprüfungen umfassen reduzierte Browserhöhe und Desktopgrößen bis 4K. Technische Tests verwenden einen lokalen GitHub-Ersatz und erteilen keine notarielle Fachfreigabe.

## Verbleibende Abnahmen und Ausbau

1. Einen tatsächlich angemeldeten Schreib-/PR-Durchlauf auf Azure mit konkreter fachlich sinnvoller Korrektur nachweisen. Login und Lesen waren nachgewiesen; synthetisches Speichern ersetzt diesen Live-Nachweis nicht.
2. `hheise-ch` ist als notarieller Reviewer konfiguriert. Die tatsächliche Prüfung einer fremden Änderung, Freigabe auf dem aktuellen Commit und der manuelle Merge-Weg müssen noch gemeinsam nachgewiesen werden. [Issue #7](https://github.com/notariat8/ontology/issues/7) ist optionale technische Erzwingung.
3. Vollständige Bedienprüfung für Fokus, Tastatur, Fehler, leere Ansichten und ungespeicherte Eingaben sowie die Aufteilung der umfangreichen `app.js` abschließen.
4. Anschließend grafischen Vorher/Nachher-Vergleich, Rückfragen am Baustein und kontrollierte deutsche Beziehungseingabe ausbauen. Fachliche Anzeigenamen fehlen teilweise; [Issue #8](https://github.com/notariat8/ontology/issues/8) liegt im Datenprojekt.
5. SHACL erst nach Entscheidung über Regelkatalog und Shapes-Vertrag ergänzen; Regeln gehören ins Datenrepository.

Die [Roadmap](editor-roadmap.md) trennt erledigte Umsetzung und verbleibende Abnahme. RDF-Verwendung ist keine Messung tatsächlicher Akten- oder Anwendungsnutzung; die App ist keine allgemeine Foundry-/OWL-Plattform. NaC bleibt Quelle der Prozessabläufe.

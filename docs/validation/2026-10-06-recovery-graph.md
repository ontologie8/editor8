# Prüfung von Wiederaufnahme und Graphvergleich

Stand: 06.10.2026. Softwareänderung auf `codex/recovery-and-graph-comparison`; keine fachlichen Modelländerungen und keine Änderung von App-Rechten.

## Lokale Nachweise

- 26 Python-Tests erfolgreich; darunter vier Vergleiche tatsächlicher RDF-Differenzen mit Hinzufügen, Entfernen, Feldänderung und unveränderter Bedeutung trotz anderer Serialisierung.
- 31 synthetische Browserprüfungen erfolgreich. Erfasst sind Neuladen, Sitzungsende, eigene Entwürfe, Konto- und Bestandsgrenzen, parallele Feldänderungen, Konflikte, nicht verfügbarer Browserspeicher, Dateiexport, erneute Anmeldung, verlorene Speicherantwort und offene Prüfbegründungen. Wiederherstellen speichert keine Änderung automatisch.
- 48 Python- und fünf Browserprüfungen gegen den ausdrücklich angegebenen getrennten Checkout `notariat8/ontology`, Datencommit `d0b69e48d90b2ae42f81406833c094f74d9fdf77`, erfolgreich. Daten-Arbeitsverzeichnis danach unverändert.
- JavaScript-Syntax und Gleichstand der generierten Handbuch- und Trainingsfassungen geprüft. Alle 18 künstlichen Trainingsfolien und ihre Übungen sind Teil der Browserprüfung.

## Sichtbare Prüfung

Der Graphvergleich wurde bei 1536 × 760 CSS-Pixeln und Geräteskalierung 2,5 sowie bei 390 × 844 CSS-Pixeln angesehen. Auf dem primären Desktop passen Vorher/Nachher, Feldvergleich und Speichern in das Vorschaufenster. Große Inhalte scrollen innerhalb des Dialogs. Auf Mobil stehen die beiden Graphen untereinander; der Dialog scrollt intern. Tastaturauswahl und sichtbarer Fokus sind geprüft.

Der zentrale Browserprüfer wurde mit installiertem Edge gegen den lokalen künstlichen Modellbestand ausgeführt. Erfolgreicher Lauf: `2026-10-06T08-04-32-827Z-c4572219`, Konto `browser-tester` sichtbar und passend, Desktop 1440 × 1000 und Mobil 390 × 844. Beide Bilder wurden angesehen. Keine Seiten-, Konsolen- oder Anfragefehler und kein horizontaler Seitenüberlauf. Die Bilder und Ergebnisse bleiben lokal unter dem ignorierten `artifacts/browser`; Graphbilder unter `test-results`. Frühere Versuche mit ungeeigneten Bereitschafts- beziehungsweise Identitätsselektoren bleiben als fehlgeschlagene Diagnosen erhalten.

## Grenze der Abnahme und Auslieferung

Diese Browserprüfungen verwenden einen lokalen GitHub-Ersatz und künstliche Sitzungen. Sie beweisen keine erneute reale Anmeldung oder notarielle Prüfung auf Azure. Der fachlich sinnvolle Live-Schreib-/PR-Weg bleibt separat nachzuweisen. Die echte Zwei-Personen-Abnahme ist auf ausdrücklichen Nutzerwunsch zurückgestellt; einmalige Nachfrage am 01.12.2026, ohne die Softwareentwicklung zu blockieren.

Der Release-Workflow muss vor Abschluss das neue Azure-Image, die aktive gesunde Revision, den erwarteten Softwarecommit unter `/api/release` und die ausgelieferten Dateihashes prüfen. Die beiden neuen Dateien `recovery.js` und `comparison.js` sind in Container- und Deploymentprüfung enthalten. Ein lokaler Erfolg oder ein offener PR allein ist kein abgeschlossener Build.

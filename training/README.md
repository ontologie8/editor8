# Training: Ontologien verstehen und pflegen

Im Editor **Hilfe → Training** öffnen. Ohne Anmeldung ist derselbe Kurs unter `/learning/` erreichbar. Sechs Lektionen enthalten insgesamt 18 Folien, Lernfragen mit Erläuterungen und ein bedienbares künstliches Modell. **Weiter**, **Zurück** und die Pfeiltasten wechseln die Folie. **Abspielen** wechselt alle 15 Sekunden; Anhalten erlaubt beliebig viel Lesezeit. **Drucken** enthält sämtliche Folien einschließlich Erklärungen.

## Lernfolge

1. **Was pflegen wir?** Vorlage und konkrete Akte unterscheiden; den Zweck einer Änderung nennen.
2. **Baum und Bausteine:** Fragen, Dokumenttypen, Entscheidungen, Prüfschritte und Nachweistypen unterscheiden.
3. **Beziehungen lesen:** Ausgangspunkt, Beziehung und Ziel verstehen. Der Baum ist keine Ausführungsreihenfolge.
4. **Gezielt bearbeiten:** Bezeichnung und Bedeutung getrennt pflegen; bestehende Bausteine ändern, statt Duplikate anzulegen.
5. **Speichern und prüfen:** Vorschau, Bestätigung, gespeicherter Entwurf und Fachprüfung auseinanderhalten.
6. **Pflege im Alltag:** Zuständigkeiten, Quellenstand, kleine Änderungen und wiederkehrende Prüfung.

## Übung

**Bezeichnung üben** öffnet ein Feld für die Frage „Benötigte Schutzausrüstung“. Eine neue Bezeichnung eingeben, **Speichern** wählen, den Vergleich lesen und **Speichern bestätigen** wählen. Erst die Bestätigung ändert das künstliche Modell im Browser. Neu laden setzt es zurück. Diese Übung verwendet weder GitHub noch echte Fachmodelle und simuliert keine notarielle Freigabe.

Die vorliegende Fassung besteht aus Browserfolien, nicht aus einer Videodatei. Für eine spätere Aufnahme lassen sich die Folien mit der Übung vorführen. Empfohlenes Sprechmuster: Problem zeigen, eine Handlung vorführen, Ergebnis erklären, Lernfrage beantworten; Aufnahme pro Lektion statt eines langen Films.

## Quellen und Pflege

Die [Recherche](../docs/research/2026-10-03-ontology-training.md) erklärt, welche Lehrmuster von Palantir und Protégé übernommen und auf unsere tatsächlichen Funktionen angepasst wurden. Inhalte sind eigenständig formuliert; keine fremden Produktbilder oder Videos werden kopiert.

- Kursquelle: [course.json](course.json); lesbare Folienfassung: [course.md](course.md).
- Künstliches Modell: [workshop.json](examples/workshop.json).
- Klassische Produktdokumentation: [Produkthandbuch](../docs/product/README.md).
- Nach einer Quellenänderung `python scripts/build_learning.py` ausführen. Mit `--check` prüft CI, dass Browser, Folien und Handbuch denselben Stand enthalten. Die Browserprüfung testet Navigation, Lernfragen und die Speicherübung.

Inhalt: CC-BY-4.0; Browsercode: AGPL-3.0-or-later.

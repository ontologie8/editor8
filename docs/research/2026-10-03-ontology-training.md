# Recherche: Ontologien erklären und pflegen

Geprüft am 03.10.2026. Grundlage sind frei zugängliche Produktdokumentation, schriftliche Übungen und ein Lehrpapier. Videos wurden nicht angesehen. Die Beispiele im Training sind vollständig künstlich und eigenständig formuliert.

| Quelle | Lehrmuster | Umsetzung in editor8 |
| --- | --- | --- |
| [Palantir Ontology Manager](https://www.palantir.com/docs/foundry/ontology-manager/overview) | Begriffe, Eigenschaften und Beziehungen getrennt erklären; Auswahl führt zu Details. | Die fünf Bausteinarten erklären, einen Baustein auswählen und Bedeutung statt nur Namen lesen. |
| [Palantir Action Types: Getting started](https://www.palantir.com/docs/foundry/action-types/getting-started) | Ein kleines Ticketbeispiel, eine begrenzte Änderung und ein nachvollziehbarer Test. | Eine Bezeichnung ändern, Vorschau ansehen, bestätigen und Ergebnis vergleichen. Foundry-Actions und Datenpipelines sind keine zugesagten editor8-Funktionen. |
| [Palantir Ontology proposals](https://www.palantir.com/docs/foundry/ontologies/review-ontology-proposals) | Änderungen in einem Zweig bündeln, vergleichen und prüfen lassen. | Arbeitsentwurf, Speichern und Fachprüfung getrennt vermitteln; keine automatische Freigabe behaupten. |
| [Stanford: Ontology Development 101](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf) | Mit Zweck, Umfang und beantwortbaren Fragen anfangen; Klassen und konkrete Instanzen unterscheiden; iterativ verbessern. | Vorlage gegen konkrete Akte abgrenzen und vor jeder Änderung deren Zweck nennen. Unsere Kategorien sind fachliche Gliederung, keine zugesagte OWL-Klassenbearbeitung. |
| [Protégé: Pizzas in 10 minutes](https://protegewiki.stanford.edu/wiki/Protege4Pizzas10Minutes) | Ein vertrautes kleines Beispiel verwenden und Schritt für Schritt Begriffe strukturieren. | Fantasiewerkstatt mit fünf Bausteinen; stabile Kennungen trotz geänderter Bezeichnung. Die historische Protégé-Oberfläche wird nicht nachgebaut. |
| [WebProtégé User Guide](https://protegewiki.stanford.edu/wiki/WebProtegeUsersGuide) | Bearbeitungsrechte, Zusammenarbeit und Änderungshistorie sichtbar machen. | GitHub-Nutzerrechte, zugelassene Datenziele und notarielle Rollen separat erklären. Der ältere Leitfaden belegt ein Lehrmuster, keine aktuelle editor8-Funktion. |

## Grenzen

Die Folien erklären vorhandene editor8-Arbeitsschritte. Sie ersetzen weder Fachschulung noch die eigenständige notarielle Prüfung. Ein künstlicher Speichertest beweist keine produktive GitHub-Änderung. Zwei unabhängige Konten müssen den produktiven Einreichungs- und Freigabeablauf weiterhin abnehmen. Automatische Schlussfolgerungen, Fachmodellgenerierung und Workflowausführung werden nicht versprochen.

## Pflegeauftrag

Bei geänderten Feldern, Befehlen, Rollen oder Speicherabläufen müssen Handbuch und betroffene Lektion im selben Softwareänderungsvorschlag aktualisiert werden. Quellen werden in JSON gepflegt; Markdown und Browserinhalt werden daraus erzeugt und in CI auf Gleichstand geprüft. Neue Übungen bleiben künstlich und werden funktional sowie sichtbar im Desktoplayout geprüft.

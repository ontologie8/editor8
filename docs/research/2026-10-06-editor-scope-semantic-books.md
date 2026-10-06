# Literatur und Abgrenzung von editor8

Geprüft am 06.10.2026. Grundlage sind öffentlich zugängliche Verlagsübersichten und der Begleitartikel der Autorin; die vollständigen Bücher wurden nicht gelesen. Ein frei zugänglicher vollständiger Buchtext wurde nicht gefunden. Beide Verlagsseiten bieten einen kostenpflichtigen PDF-Download an. Keine vollständigen Bücher oder fremden Produktquelltexte in dieses Repository übernehmen.

## Quellen und Nutzen

- Dave Wells: [Designing and Implementing Semantic Data Layers](https://technicspub.com/designing-and-implementing-semantic-data-layers/). Die Übersicht behandelt Bedeutung, Modellierung und die Einordnung semantischer Schichten in eine größere Datenarchitektur. Nützlich für die Grenze zwischen Modellpflege und operativer Datenverarbeitung.
- Jessica Talisman: [Ontology Pipeline](https://technicspub.com/ontology-pipeline/). Die Übersicht verbindet Vokabular, Metadaten, Taxonomie, Thesaurus, Ontologie und Wissensgraph. Nützlich für fachliche Begriffe und die Reihenfolge der Modellpflege.
- Jessica Talisman: [Ontology Pipeline Studio](https://jessicatalisman.substack.com/p/ontology-pipeline-studio), mit [interaktivem Begleiter](https://jesstalisman-ia.github.io/ontology-pipeline/). Die tatsächlich geöffnete Oberfläche führt durch Zweck, Begriffe, Hierarchien, Beziehungen, Modellfragen und Prüfungen. Sie ist öffentlich benutzbar und kein vollständiger Buchtext. Der Fußbereich nennt Copyright und „All rights reserved“; es wird kein fremder Quelltext übernommen.

## Einordnung für unseren Editor

Die folgenden Punkte sind unsere Ableitung, keine behauptete Empfehlung aus einem vollständig gelesenen Buch:

editor8 unterstützt Ontologiepfleger und Notare beim Verstehen, Bearbeiten und Prüfen wiederverwendbarer Fachmodelle. Der Nutzer muss Bedeutung, Quelle, Beziehungen und Änderungsstand beurteilen können. Die äußere Office-Navigation bleibt Verstehen → Bearbeiten → Prüfen. Die Gruppierung des Baums nach Fragen, Dokumenttypen und weiteren Bausteinarten ist eine Bedienhilfe; sie behauptet keine fachliche Unterklassenbeziehung.

| Gehört zur Modellpflege im Editor | Führende Zuständigkeit |
| --- | --- |
| Bezeichnungen, Definitionen und stabile Kennungen verstehen und pflegen | Fachmodellbestand; Darstellung und Bedienung in editor8 |
| Bausteine, Oberklassen und zulässige Beziehungen bearbeiten | Vertrag des jeweiligen Datenadapters |
| Quellenstand, Entwurf, Änderungsvergleich und Prüfentscheidung nachvollziehen | Versionierter Datenbestand und Editorablauf |
| Synonyme und alternative Bezeichnungen | Gezielter späterer Ausbau nach einem ausdrücklich vereinbarten Datenvertrag; aktuell keine zugesicherte Vollfunktion |
| Modellregeln prüfen und verständliche Befunde zeigen | Versionierte Regeln im Datenprojekt; Editor erklärt Ergebnisse |

Aktenwerte, Prozessausführung, eine allgemeine Datenintegrationsplattform, ein Analyse-Warehouse und eine zweite dauerhafte Ontologiedatenbank gehören nicht zum derzeitigen Editorauftrag. Ein Wissensgraph- oder Reasoner-Ausbau benötigt einen konkret belegten Anwendungsbedarf. Die Literatur erweitert diesen Auftrag nicht automatisch.

## Fragen zur Abnahme des Produktumfangs

Für eine kleine künstliche Vorlage prüfen:

1. Kann der Pfleger erklären, was eine benötigte Angabe bedeutet und wo ihre Definition gilt?
2. Findet er die Dokumenttypen und Beziehungen, die zu dieser Angabe gehören?
3. Sieht er vor dem Speichern, welche Modellaussagen geändert werden und welches direkte Umfeld betroffen ist?
4. Kann er seine noch offenen Eingaben nach einer Unterbrechung wieder aufnehmen, ohne zwischenzeitliche Änderungen zu überschreiben?
5. Kann eine prüfende Person die Änderung, ihren Grund und den tatsächlich geprüften Stand zuordnen?

Die reale Abnahme mit einer zweiten Person ist auf Nutzeranweisung vom 06.10.2026 zurückgestellt: Derzeit arbeitet nur der Nutzer selbst mit. Nachfrage am 01.12.2026. Diese Zurückstellung erteilt keine notarielle Fachfreigabe und blockiert die beauftragten Softwareverbesserungen nicht.

Die laufenden Arbeiten zu Eingabewiederherstellung und RDF-basiertem Graphvergleich beantworten Fragen 3 und 4. Synonympflege, weitere Modellregeln oder eine Datenplattform sind gesonderte spätere Entscheidungen.

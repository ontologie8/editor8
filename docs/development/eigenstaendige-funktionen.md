# Eigenständige Funktionen und Anschluss an schema

Stand: 13.10.2026. Auftrag: nützliche Funktionen aus den Produktbeschreibungen von OpenLink und Helix eigenständig für editor8 entwickeln. Nutzerentscheidung: ausschließlich Schemadefinitionen und Fachmodelle pflegen; Instanz- und Aktenwerte bleiben in nutzenden Anwendungen.

## Herkunft und Vorgehen

Die Produktprüfung hat auch fremden Quellcode betrachtet. Diese Arbeit ist deshalb keine formale Clean-Room-Entwicklung. Die folgende Umsetzung verwendet selbst formulierte Anforderungen, bestehenden editor8-Code und Primärstandards. Fremde Implementierungen, Dokumentationstexte, Grafiken, Beispiele und Tests werden nicht übernommen. Vorherige Produktvergleiche sind keine Abhängigkeiten des Builds.

Urheberrecht schützt die konkrete Ausdrucksform; die zugrunde liegenden Ideen sind davon zu unterscheiden. Das erlaubt keine pauschale Garantie für jede denkbare Nachbildung. Maßgeblich sind [Art. 1 der Richtlinie 2009/24/EG](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32009L0024) und [EuGH C-406/10](https://eur-lex.europa.eu/legal-content/EN/SUM/?uri=CELEX:62010CJ0406). Insbesondere werden auch fremde Handbuchtexte nicht nachgeschrieben oder umbenannt übernommen. editor8 behält AGPL-3.0-or-later für eigenen Code und CC-BY-4.0 für eigene Dokumentation.

## Führendes Projekt

`ontologie8/schema`, veröffentlichter Commit `734c53e05aca68bbe748866c77afaef64047cde8`, führt im Pilot 0.1.0 einen JSON-Vertrag mit JSON Schema 2020-12. RDF ist eine kontrollierte Projektion. IDs, Sprache, Zeitpräzision, Quelle, Aussageart und Revisionen sind eigenständige Dimensionen. Das Schema ist keine produktive Datenbank und erteilt keine Zugriffsrechte.

Die am 13.10. lokal betrachtete Erweiterung für Module, Profile und portable Pakete war noch nicht veröffentlicht. Ihre exakten Versionen und Artefaktbindungen werden erst nach Veröffentlichung für eine Datenanbindung ausgewählt. Keine Kopie dieser gepflegten Fachdefinitionen wird im Editor-Image angelegt. Ebenso wird kein Code aus schema automatisch vom Editor ausgeführt.

Der vorhandene NaC-RDF-Adapter bleibt ein eigener Datenvertrag. Der JSON-/Paketadapter ist eine nachfolgende Integration; dieses erste Paket bezeichnet ihn nicht als bereits implementiert.

## Erstes Paket und Akzeptanz

| ID | Verhalten | Nachweis |
| --- | --- | --- |
| EF-01 | Eingaben verwenden eine getrennte, wiederverwendbare Darstellungsschicht; Feldhinweise können aus einem Adapterprofil kommen. | Browser: bestehende Eingaben bleiben bearbeitbar und unverändert speicherbar. |
| EF-02 | Der NaC-Adapter liefert Erläuterungen zu Bausteintypen, Feldern und Beziehungen aus dem ausgewählten Vokabular. | Python: deutsche/ungekennzeichnete Texte, fehlende Angaben, mehrfache Domain-/Range-Angaben und ungefährliche Darstellung prüfen. |
| EF-03 | Eine Verbindung wird vor dem Hinzufügen als deutscher Satz mit Ausgang, Beziehung und Ziel angezeigt. | Browser: Auswahl, Richtung, doppelte Verbindung und Leserrechte prüfen. |
| EF-04 | Vokabularhinweise stammen aus demselben Git-Commit wie der Fall. Fehlende Hinweise werden ausdrücklich angezeigt. | Adaptertest: feste Commitbindung; kein stiller Zugriff auf main. |
| EF-05 | Hinweise zu Domain/Range erläutern das Vokabular und sind keine zusätzliche Validierungs- oder Fachfreigaberegel. | Tests: Vorschau schreibt nichts; bestehende Servervalidierung und Rechte bleiben maßgeblich. |
| EF-06 | Hilfe und Training erklären den Ablauf für Fachanwender mit eigenen künstlichen Beispielen. | Generierung und Browserprüfung. |

Review vor Code: RDFS-Domain und -Range beschreiben Semantik und dürfen nicht als geschlossene Eingabesperre ausgegeben werden. Das Profil enthält ausschließlich Darstellungshinweise; Rechte und zulässige Schreiboperationen werden weiterhin vom Server geprüft. Texte werden als Textknoten dargestellt. Die Cloud liest Metadaten am festgehaltenen Fallcommit, nicht an einem beweglichen zweiten Stand.

## Nachfolgende Pakete

1. Einen veröffentlichten schema-Paketstand mit Quellcommit, Versionen und Artefaktidentitäten anbinden; Schema-, Profil- und Moduldefinitionen getrennt anzeigen. Keine automatische Verbraucherumstellung.
2. Geführte Pflege dieser Definitionen mit semantischen Prüfungen des führenden Vertrags, Feldvergleich und GitOps-Vorschlag. Keine Eingabemasken für produktive Modellinstanzen.
3. Änderungsübersichten und Wiederaufnahme für große Fachmodelle weiter ausbauen. Datenimport, KI-Analyst und operative Datenbanken sind zusätzliche Produktaufgaben und gehören nicht allein aufgrund eines Vorbilds in editor8.

Primärstandards: [RDF Schema 1.1](https://www.w3.org/TR/rdf-schema/), [JSON Schema 2020-12](https://json-schema.org/draft/2020-12). Der NaC-Adapter und der spätere JSON-/Paketadapter können dasselbe Darstellungshilfenprofil liefern; dieses Profil ersetzt keinen Datenvertrag.

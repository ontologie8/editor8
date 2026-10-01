# Datenvertrag, Version 1

Software: `ontologie8/editor8`. Notardaten: `notariat8/ontology`.

| Pfad im Datenrepository | Bedeutung |
| --- | --- |
| `catalog/nac-baseline.json` | `business_case_type_ids`: eindeutige sichere Fall-IDs; optional `editor_contract_version: 1` |
| `catalog/nac-usecases.ttl` | Bezeichnungen, stabile IRIs und BPMN-Verweise |
| `cases/<id>/ontology.ttl` | Führendes Fachmodell |
| `cases/<id>/README.md` | Abgeleitete Mermaid-Leseseite |
| `ontology/core.ttl` | Gemeinsames Vokabular |

Der Adapter unterstützt derzeit das NaC-RDF-Schema unter `https://notariat8.github.io/ontology/id/`. Das ist ein technischer Bezeichner. Andere RDF-Schemata brauchen einen eigenen Adapter; die Repositorytrennung allein macht den Editor nicht zu einem universellen RDF-Editor.

Fallzahl und Kennungen werden aus dem Datenkatalog gelesen, nicht aus dem Softwarecheckout. Für den aktuellen Notardatensatz gelten weiterhin genau 20 kanonische IDs. Die App legt keine weiteren Falltypen an. Alle Dateien einer Cloudansicht werden am gleichen unveränderlichen Commit gelesen. Ein nicht unterstützter Vertrag, doppelte Kennungen und Pfadzeichen werden zurückgewiesen.

Lokale Entwicklung verlangt `EDITOR8_DATA_ROOT` als separaten Datencheckout. Cloudbetrieb liest den Katalog mit dem angemeldeten Nutzer über `GITHUB_REPOSITORY`; kein Fachmodell wird in das Image eingebaut. Der Softwarecheckout wird als Datenziel abgelehnt.

Schreiben erzeugt begrenzte Änderungen auf eigenen Datenzweigen mit Revisionsprüfung. Falländerungen enthalten Turtle und die erzeugte Leseseite; Vokabularänderungen nur `ontology/core.ttl`. Ein Pull Request bleibt fachlicher Vorschlag. Datenvalidatoren und notarielle Prüfung gehören zum Datenrepository. Eigene fachliche Freigaben und ein leerer Notar-Reviewer-Kreis erlauben keine Freigabe.

Technische Formatabbildungen und der Leseseiten-Adapter sind Anwendungscode. Die Integration prüft ihre Ausgabe gegen den Dokumentgenerator im Datenprojekt; dessen fachliche Daten bleiben die einzige gepflegte Quelle. Keine zweite Kopie der 20 Modelle in editor8 anlegen.

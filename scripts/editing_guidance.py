# SPDX-License-Identifier: AGPL-3.0-or-later
"""Display hints for the existing NaC adapter; never permissions or constraints."""
import hashlib

from rdflib import Graph, Namespace, RDFS, URIRef

from data_contract import CATEGORIES, EDGES

N8 = Namespace("https://notariat8.github.io/ontology/id/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
FIELD_HINTS = {
    "label": (SKOS.prefLabel, "Bezeichnung des Fachbausteins, keine Antwort einer konkreten Person."),
    "question": (N8.offeneFrage, "Beschreibe, welche fachliche Frage noch zu klären ist."),
    "section": (N8.quellabschnitt, "Nenne den Abschnitt der Vorlage, auf den sich der Baustein bezieht."),
    "detail": (RDFS.comment, "Erkläre Bedeutung und Verwendung dieses Bausteins im Fachmodell."),
    "owner_role": (N8.verantwortlicheRolle, "Fachliche Zuständigkeit; diese Angabe erteilt keine technischen Rechte."),
    "privacy_class": (N8.datenschutzklasse, "Verwende eine im Fachmodell vereinbarte Datenschutzklasse."),
    "document_source": (N8.dokumentquelle, "Beschreibe die Herkunft des Dokumenttyps, keine konkrete Akte."),
}


def _text(graph, subject, predicates):
    for predicate in predicates:
        values = [value for value in graph.objects(subject, predicate)
                  if getattr(value, "language", None) in (None, "de", "de-DE")]
        if values:
            values.sort(key=lambda value: (getattr(value, "language", None) is None, str(value)))
            return str(values[0])[:1500]
    return ""


def profile(core_text=""):
    """Return plain JSON hints. Multiple RDFS ranges remain multiple hints."""
    graph = Graph()
    available = bool(core_text)
    if core_text:
        graph.parse(data=core_text, format="turtle")

    def reference(uri):
        return {"id": str(uri), "label": _text(graph, uri, (SKOS.prefLabel, RDFS.label)) or str(uri)}

    result = {
        "version": 1, "available": available,
        "revision": hashlib.sha256(core_text.encode()).hexdigest() if available else None,
        "fields": {}, "types": {}, "relations": {},
    }
    for field, (predicate, fallback) in FIELD_HINTS.items():
        result["fields"][field] = {"description": _text(graph, predicate, (RDFS.comment, SKOS.definition)) or fallback}
    for category, (name, _) in CATEGORIES.items():
        result["types"][category] = {
            "id": str(N8[name]), "description": _text(graph, N8[name], (RDFS.comment, SKOS.definition)),
        }
    for name in EDGES.values():
        predicate = N8[name]
        result["relations"][name] = {
            "description": _text(graph, predicate, (RDFS.comment, SKOS.definition)),
            "domain": [reference(uri) for uri in sorted(graph.objects(predicate, RDFS.domain), key=str) if isinstance(uri, URIRef)],
            "range": [reference(uri) for uri in sorted(graph.objects(predicate, RDFS.range), key=str) if isinstance(uri, URIRef)],
        }
    return result

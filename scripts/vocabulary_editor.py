# SPDX-License-Identifier: AGPL-3.0-or-later
"""Constrained, lossless editing of the shared ontology vocabulary."""

from __future__ import annotations

import hashlib
import json
import re

from rdflib import Graph, Literal, RDF, RDFS, OWL, URIRef
from rdflib.compare import to_isomorphic

from case_editor_model import N8


KINDS = {"class": OWL.Class, "object_property": OWL.ObjectProperty, "datatype_property": OWL.DatatypeProperty}
KIND_LABELS = {"class": "Begriffsklasse", "object_property": "Verbindung", "datatype_property": "Merkmal"}
FIELDS = {"parent": RDFS.subClassOf, "domain": RDFS.domain, "range": RDFS.range}
PREFIXES = {
    "n8": str(N8), "skos": "http://www.w3.org/2004/02/skos/core#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}
LOCAL = re.compile(r"[A-Za-z][A-Za-z0-9]*\Z")
BLOCK = re.compile(r"(?m)^n8:([A-Za-z][A-Za-z0-9]*) a owl:(Class|ObjectProperty|DatatypeProperty)\b")
ORDER = (RDF.type, RDFS.subClassOf, RDFS.domain, RDFS.range, RDFS.label, RDFS.comment)


def _uri(value: str) -> URIRef:
    if not isinstance(value, str) or ":" not in value:
        raise ValueError("Ungültiger Bezug auf einen Begriff")
    prefix, local = value.split(":", 1)
    if prefix not in PREFIXES or not LOCAL.fullmatch(local):
        raise ValueError("Der Bezug muss ein bekannter Begriff sein")
    return URIRef(PREFIXES[prefix] + local)


def _name(value: URIRef) -> str:
    for prefix, base in PREFIXES.items():
        local = str(value).removeprefix(base)
        if local != str(value) and LOCAL.fullmatch(local):
            return f"{prefix}:{local}"
    raise ValueError(f"Nicht unterstützter Begriffsbezug: {value}")


def _graph(text: str) -> Graph:
    return Graph().parse(data=text, format="turtle")


def _one(graph: Graph, subject: URIRef, predicate: URIRef) -> str:
    values = list(graph.objects(subject, predicate))
    if len(values) > 1:
        raise ValueError("Ein Begriff hat mehrere konkurrierende Angaben")
    return _name(values[0]) if values else ""


def model(text: str) -> dict:
    graph = _graph(text)
    terms = []
    for subject in sorted(set(graph.subjects(RDF.type, None)), key=str):
        if not str(subject).startswith(str(N8)):
            continue
        kinds = [kind for kind, rdf_type in KINDS.items() if (subject, RDF.type, rdf_type) in graph]
        if not kinds:
            continue
        if len(kinds) != 1:
            raise ValueError("Ein Begriff hat mehrere Arten")
        labels = [str(value) for value in graph.objects(subject, RDFS.label) if isinstance(value, Literal) and value.language == "de"]
        comments = [str(value) for value in graph.objects(subject, RDFS.comment) if isinstance(value, Literal) and value.language == "de"]
        if len(labels) != 1 or len(comments) > 1:
            raise ValueError("Bezeichnung oder Erläuterung ist nicht eindeutig")
        terms.append({
            "id": str(subject).removeprefix(str(N8)), "kind": kinds[0],
            "label": labels[0], "comment": comments[0] if comments else "",
            **{name: _one(graph, subject, predicate) for name, predicate in FIELDS.items()},
        })
    return {"terms": terms, "revision": hashlib.sha256(text.encode("utf-8")).hexdigest()}


def _valid_text(value: object, name: str, limit: int, required: bool = False) -> str:
    if not isinstance(value, str) or len(value) > limit or "\x00" in value or (required and not value.strip()):
        raise ValueError(f"{name} fehlt oder ist zu lang")
    return value.strip()


def validate(original: str, proposed: dict) -> dict:
    current = model(original)
    if not isinstance(proposed, dict) or proposed.get("revision") != current["revision"]:
        raise ValueError("Das Vokabular wurde inzwischen geändert. Bitte neu laden.")
    incoming = proposed.get("terms")
    if not isinstance(incoming, list) or len(incoming) > 200:
        raise ValueError("Ungültige Begriffsliste")
    previous = {item["id"]: item for item in current["terms"]}
    result = []
    seen = set()
    for item in incoming:
        if not isinstance(item, dict):
            raise ValueError("Ungültiger Begriff")
        identifier, kind = item.get("id"), item.get("kind")
        if not isinstance(identifier, str) or not LOCAL.fullmatch(identifier) or kind not in KINDS or identifier in seen:
            raise ValueError("Begriffskennung oder Art ist ungültig oder doppelt")
        seen.add(identifier)
        if identifier in previous and kind != previous[identifier]["kind"]:
            raise ValueError("Die Art eines vorhandenen Begriffs kann nicht geändert werden")
        if identifier not in previous and (URIRef(str(N8) + identifier), None, None) in _graph(original):
            raise ValueError("Die Kennung wird bereits anderweitig verwendet")
        label = _valid_text(item.get("label"), "Bezeichnung", 150, True)
        comment = _valid_text(item.get("comment"), "Erläuterung", 1000, identifier not in previous)
        output = {"id": identifier, "kind": kind, "label": label, "comment": comment}
        for field in FIELDS:
            value = item.get(field, "")
            if not isinstance(value, str):
                raise ValueError("Ungültiger Begriffsbezug")
            output[field] = value.strip()
        if kind != "class" and output["parent"]:
            raise ValueError("Nur Begriffsklassen können eine Oberklasse haben")
        if kind == "class" and (output["domain"] or output["range"]):
            raise ValueError("Klassen haben keinen Wertebereich oder Geltungsbereich")
        result.append(output)
    if set(previous) - seen:
        raise ValueError("Vorhandene Begriffe dürfen nicht entfernt werden")
    classes = {item["id"] for item in result if item["kind"] == "class"}
    for item in result:
        for field in FIELDS:
            value = item[field]
            if not value:
                continue
            _uri(value)
            if field in ("parent", "domain") and value not in {f"n8:{name}" for name in classes} | {"skos:Concept"}:
                raise ValueError("Oberklasse und Geltungsbereich müssen bekannte Klassen sein")
            if field == "range":
                if item["kind"] == "object_property" and value not in {f"n8:{name}" for name in classes} | {"skos:Concept"}:
                    raise ValueError("Ziel einer Verbindung muss eine Klasse sein")
                if item["kind"] == "datatype_property" and value not in {"xsd:string", "xsd:boolean", "xsd:integer", "xsd:date", "xsd:dateTime", "xsd:anyURI"}:
                    raise ValueError("Datentyp für dieses Merkmal ist nicht unterstützt")
    parents = {item["id"]: item["parent"][3:] for item in result if item["kind"] == "class" and item["parent"].startswith("n8:")}
    for identifier in parents:
        path, cursor = set(), identifier
        while cursor in parents:
            if cursor in path:
                raise ValueError("Oberklassen dürfen keinen Kreis bilden")
            path.add(cursor)
            cursor = parents[cursor]
    return {"terms": sorted(result, key=lambda item: item["id"]), "revision": current["revision"]}


def _block_span(text: str, identifier: str) -> tuple[int, int]:
    matches = [hit for hit in BLOCK.finditer(text) if hit.group(1) == identifier]
    if len(matches) != 1:
        raise ValueError("Die Turtle-Struktur kann nicht sicher bearbeitet werden")
    start = matches[0].start()
    rest = text[start:]
    end_match = re.search(r"(?m)^.*\.[ \t]*$", rest)
    if end_match is None:
        raise ValueError("Der Begriff hat keinen abgeschlossenen Turtle-Block")
    end = start + end_match.end()
    if text[end:end + 1] == "\n":
        end += 1
    return start, end


def _statement(item: dict, graph: Graph) -> str:
    subject = URIRef(str(N8) + item["id"])
    pairs = list(graph.predicate_objects(subject))
    if any(predicate not in ORDER for predicate, _ in pairs):
        raise ValueError("Dieser Begriff enthält weitere Aussagen und muss direkt in Turtle bearbeitet werden")
    if any(predicate in (RDFS.label, RDFS.comment) and (not isinstance(value, Literal) or value.language != "de") for predicate, value in pairs):
        raise ValueError("Mehrsprachige Begriffe müssen direkt in Turtle bearbeitet werden")
    pairs.sort(key=lambda pair: ORDER.index(pair[0]))
    rendered = []
    for predicate, value in pairs:
        predicate_name = "a" if predicate == RDF.type else "rdfs:" + str(predicate).rsplit("#", 1)[1]
        value_name = (json.dumps(str(value), ensure_ascii=False) + "@de") if isinstance(value, Literal) else ("owl:" + str(value).rsplit("#", 1)[1] if predicate == RDF.type else _name(value))
        rendered.append(f"  {predicate_name} {value_name}")
    return f"n8:{item['id']} " + " ;\n".join(part.strip() if index == 0 else part for index, part in enumerate(rendered)) + " .\n"


def prepare_change(original: str, proposed: dict) -> tuple[str, list[str], bool]:
    checked = validate(original, proposed)
    old_model = model(original)
    old = {item["id"]: item for item in old_model["terms"]}
    new = {item["id"]: item for item in checked["terms"]}
    labels = {f"n8:{identifier}": item["label"] for identifier, item in {**old, **new}.items()}
    labels.update({"skos:Concept": "Allgemeiner Fachbegriff", "xsd:string": "Text", "xsd:boolean": "Ja oder Nein", "xsd:integer": "Ganze Zahl", "xsd:date": "Datum", "xsd:dateTime": "Datum und Uhrzeit", "xsd:anyURI": "Webadresse"})
    def shown(value: str) -> str:
        return labels.get(value, value) if value else "(leer)"
    changes = []
    graph = _graph(original)
    edits = []
    for identifier, item in new.items():
        previous = old.get(identifier)
        if previous == item:
            continue
        subject = URIRef(str(N8) + identifier)
        if previous is None:
            changes.append(f"{KIND_LABELS[item['kind']]} hinzugefügt: {item['label']} ({identifier})")
            for field, title in (("comment", "Erläuterung"), ("parent", "Oberklasse"), ("domain", "Geltungsbereich"), ("range", "Ziel oder Datentyp")):
                if item[field]:
                    changes.append(f"{item['label']} · {title}: {shown(item[field])}")
            graph.add((subject, RDF.type, KINDS[item["kind"]]))
        else:
            for field, title in (("label", "Bezeichnung"), ("comment", "Erläuterung"), ("parent", "Oberklasse"), ("domain", "Geltungsbereich"), ("range", "Ziel oder Datentyp")):
                if previous[field] != item[field]:
                    changes.append(f"{previous['label']} · {title}: {shown(previous[field])} → {shown(item[field])}")
        for field, predicate in FIELDS.items():
            graph.remove((subject, predicate, None))
            if item[field]:
                graph.add((subject, predicate, _uri(item[field])))
        for predicate, field in ((RDFS.label, "label"), (RDFS.comment, "comment")):
            for value in list(graph.objects(subject, predicate)):
                if isinstance(value, Literal) and value.language == "de":
                    graph.remove((subject, predicate, value))
            if item[field]:
                graph.add((subject, predicate, Literal(item[field], lang="de")))
        block = _statement(item, graph)
        if previous is not None:
            start, end = _block_span(original, identifier)
            edits.append((start, end, block))
        else:
            edits.append((len(original), len(original), ("\n" if not original.endswith("\n\n") else "") + block))
    if not edits:
        return original, [], False
    updated = original
    for start, end, replacement in sorted(edits, key=lambda edit: edit[0], reverse=True):
        updated = updated[:start] + replacement + updated[end:]
    if to_isomorphic(_graph(updated)) != to_isomorphic(graph):
        raise ValueError("Die Turtle-Änderung lässt sich nicht verlustfrei schreiben")
    return updated, changes, True

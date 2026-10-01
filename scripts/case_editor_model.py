# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read and update the maintained case Turtle without exposing RDF syntax in the UI."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse

from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.compare import to_isomorphic

from data_contract import CATEGORIES, EDGES, APP_ROOT, DATA_ROOT, local_root, parse_baseline
from case_document import render
from turtle_edit import minimal_turtle


ROOT = DATA_ROOT
N8 = Namespace("https://notariat8.github.io/ontology/id/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
DCT = Namespace("http://purl.org/dc/terms/")
DE = "de"
NODE_ID = re.compile(r"[a-z][a-z0-9._-]{0,79}\Z")
MAX_TEXT = 2000
RELATIONS = tuple(EDGES.values())
CATEGORY_NAMES = {key: name for key, (name, _) in CATEGORIES.items()}
NODE_FIELDS = {
    "label": (SKOS.prefLabel, "lang"),
    "status": (N8.quellstatus, "text"),
    "question": (N8.offeneFrage, "lang"),
    "section": (N8.quellabschnitt, "text"),
    "detail": (RDFS.comment, "lang"),
    "owner_role": (N8.verantwortlicheRolle, "text"),
    "privacy_class": (N8.datenschutzklasse, "text"),
    "document_source": (N8.dokumentquelle, "lang"),
    "contains_personal_data": (N8.enthaeltPersonendaten, "bool"),
    "required_for": (N8.erforderlichFuer, "list"),
    "options": (N8.entscheidungsoption, "list"),
}


def slugs(root: Path | None = None) -> list[str]:
    root = local_root(root if root is not None else ROOT)
    baseline = parse_baseline((root / "catalog/nac-baseline.json").read_text(encoding="utf-8"))
    return baseline["business_case_type_ids"]


def case_path(slug: str, root: Path | None = None) -> Path:
    root = local_root(root if root is not None else ROOT)
    if slug not in slugs(root):
        raise ValueError("Unbekannter Fall")
    return root / "cases" / slug / "ontology.ttl"


def case_uri(slug: str) -> URIRef:
    return N8[f"vorgangsart-{slug}"]


def node_uri(slug: str, node_id: str) -> URIRef:
    return URIRef(f"{N8}case/{slug}/node/{node_id}")


def revision(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _one(graph: Graph, subject: URIRef, predicate: URIRef) -> str:
    value = graph.value(subject, predicate)
    return str(value) if value is not None else ""


def _graph_to_model(slug: str, graph: Graph) -> dict:
    case = case_uri(slug)
    nodes = []
    for node in graph.objects(case, N8.hatBaustein):
        category = next(
            (key for key, name in CATEGORY_NAMES.items() if (node, RDF.type, N8[name]) in graph),
            None,
        )
        if category is None:
            raise ValueError(f"Unbekannter Knotentyp: {node}")
        item = {"id": _one(graph, node, N8.nacNodeId) or _one(graph, node, N8.lokaleNodeId), "category": category}
        for field, (predicate, kind) in NODE_FIELDS.items():
            if kind == "list":
                item[field] = sorted(str(value) for value in graph.objects(node, predicate))
            elif kind == "bool":
                value = graph.value(node, predicate)
                item[field] = bool(value.toPython()) if value is not None else None
            elif field == "status":
                item[field] = _one(graph, node, N8.quellstatus) or _one(graph, node, N8.pflegeStatus)
            else:
                item[field] = _one(graph, node, predicate)
        nodes.append(item)
    nodes.sort(key=lambda item: (list(CATEGORIES).index(item["category"]), item["id"]))
    node_ids = {node_uri(slug, item["id"]): item["id"] for item in nodes}
    edges = []
    for source, predicate, target in graph:
        if predicate in {N8[name] for name in RELATIONS} and source in node_ids and target in node_ids:
            edges.append({"from": node_ids[source], "type": str(predicate).removeprefix(str(N8)), "to": node_ids[target]})
    edges.sort(key=lambda edge: (edge["from"], edge["type"], edge["to"]))
    return {
        "slug": slug,
        "summary": _one(graph, case, DCT.description),
        "sources": sorted(str(value) for value in graph.objects(case, DCT.references)),
        "nac_source": _one(graph, case, DCT.source),
        "nodes": nodes,
        "edges": edges,
    }


def load_case(slug: str, root: Path | None = None) -> dict:
    root = local_root(root if root is not None else ROOT)
    path = case_path(slug, root)
    graph = Graph().parse(path, format="turtle")
    model = _graph_to_model(slug, graph)
    model["revision"] = revision(path)
    catalog = Graph().parse(root / "catalog/nac-usecases.ttl", format="turtle")
    model["title"] = _one(catalog, case_uri(slug), SKOS.prefLabel)
    model["bpmn_source"] = _one(catalog, case_uri(slug), N8.hatBpmnModell)
    return model


def _clean_string(value: object, name: str, required: bool = False) -> str:
    if not isinstance(value, str) or len(value) > MAX_TEXT:
        raise ValueError(f"{name}: Text fehlt oder ist zu lang")
    cleaned = value.strip()
    if required and not cleaned:
        raise ValueError(f"{name}: darf nicht leer sein")
    return cleaned


def _clean_list(value: object, name: str) -> list[str]:
    if not isinstance(value, list) or len(value) > 30:
        raise ValueError(f"{name}: ungültige Liste")
    result = [_clean_string(item, name, required=True) for item in value]
    if len(result) != len(set(result)):
        raise ValueError(f"{name}: doppelte Einträge")
    return result


def validate_model(slug: str, data: object, root: Path | None = None) -> dict:
    case_path(slug, root)
    if not isinstance(data, dict) or data.get("slug") != slug:
        raise ValueError("Fallkennung stimmt nicht")
    summary = _clean_string(data.get("summary"), "Beschreibung", required=True)
    sources = _clean_list(data.get("sources"), "Rechtsquellen")
    for source in sources:
        parsed = urlparse(source)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError(f"Rechtsquelle muss eine HTTPS-Adresse sein: {source}")
    raw_nodes = data.get("nodes")
    if not isinstance(raw_nodes, list) or len(raw_nodes) > 200:
        raise ValueError("Ungültige Bausteinliste")
    nodes = []
    ids = set()
    categories = set()
    for raw in raw_nodes:
        if not isinstance(raw, dict):
            raise ValueError("Ungültiger Baustein")
        node_id = raw.get("id")
        category = raw.get("category")
        if not isinstance(node_id, str) or not NODE_ID.fullmatch(node_id) or node_id in ids:
            raise ValueError(f"Ungültige oder doppelte Baustein-ID: {node_id}")
        if category not in CATEGORY_NAMES:
            raise ValueError(f"Ungültiger Bausteintyp: {category}")
        ids.add(node_id)
        categories.add(category)
        node = {"id": node_id, "category": category}
        for field, (_, kind) in NODE_FIELDS.items():
            value = raw.get(field, "" if kind not in ("list", "bool") else ([] if kind == "list" else None))
            if kind == "list":
                node[field] = _clean_list(value, field)
            elif kind == "bool":
                if value is not None and type(value) is not bool:
                    raise ValueError("Personendaten-Angabe muss Ja, Nein oder leer sein")
                node[field] = value
            else:
                node[field] = _clean_string(value, field, required=field in ("label", "status"))
        nodes.append(node)
    if categories != set(CATEGORIES):
        raise ValueError("Jeder der fünf Bausteintypen muss mindestens einmal vorkommen")
    raw_edges = data.get("edges")
    if not isinstance(raw_edges, list) or not raw_edges or len(raw_edges) > 500:
        raise ValueError("Es muss mindestens eine gültige Beziehung geben")
    edges = []
    seen = set()
    for edge in raw_edges:
        if not isinstance(edge, dict):
            raise ValueError("Ungültige Beziehung")
        key = (edge.get("from"), edge.get("type"), edge.get("to"))
        if key[0] not in ids or key[2] not in ids or key[1] not in RELATIONS or key in seen:
            raise ValueError(f"Ungültige oder doppelte Beziehung: {key}")
        seen.add(key)
        edges.append({"from": key[0], "type": key[1], "to": key[2]})
    return {"slug": slug, "summary": summary, "sources": sources, "nodes": nodes, "edges": edges}


def graph_from_model(slug: str, data: object, original: Graph, root: Path | None = None) -> Graph:
    model = validate_model(slug, data, root)
    graph = Graph()
    graph += original
    case = case_uri(slug)
    old_nodes = set(graph.objects(case, N8.hatBaustein))
    new_nodes = {node_uri(slug, item["id"]) for item in model["nodes"]}
    for item in model["nodes"]:
        uri = node_uri(slug, item["id"])
        if uri not in old_nodes and not item["id"].startswith("local."):
            raise ValueError("Neue Bausteine brauchen eine Kennung mit local. als Präfix")
        if uri in old_nodes and (uri, N8.nacNodeId, None) in graph:
            original_status = graph.value(uri, N8.quellstatus)
            if original_status is not None and item["status"] != str(original_status):
                raise ValueError("Der NaC-Vorlagenstatus kann hier nicht geändert werden")
    if any((uri, N8.nacNodeId, None) in graph for uri in old_nodes - new_nodes):
        raise ValueError("Bausteine aus der NaC-Vorlage können nicht entfernt werden")
    for predicate in (DCT.description, DCT.references, N8.hatBaustein):
        graph.remove((case, predicate, None))
    graph.add((case, DCT.description, Literal(model["summary"], lang=DE)))
    for source in model["sources"]:
        graph.add((case, DCT.references, URIRef(source)))
    for node in new_nodes:
        graph.add((case, N8.hatBaustein, node))
    for node in old_nodes - new_nodes:
        graph.remove((node, None, None))
        graph.remove((None, None, node))
    for item in model["nodes"]:
        node = node_uri(slug, item["id"])
        for category_name in CATEGORY_NAMES.values():
            graph.remove((node, RDF.type, N8[category_name]))
        graph.add((node, RDF.type, N8[CATEGORY_NAMES[item["category"]]]))
        graph.remove((node, N8.nacNodeId, None))
        graph.remove((node, N8.lokaleNodeId, None))
        graph.add((node, N8.lokaleNodeId if item["id"].startswith("local.") else N8.nacNodeId, Literal(item["id"])))
        for field, (predicate, kind) in NODE_FIELDS.items():
            graph.remove((node, predicate, None))
            value = item[field]
            if field == "status":
                graph.remove((node, N8.pflegeStatus, None))
                graph.add((node, N8.pflegeStatus if item["id"].startswith("local.") else N8.quellstatus, Literal(value)))
            elif kind == "list":
                for member in value:
                    graph.add((node, predicate, Literal(member)))
            elif kind == "bool":
                if value is not None:
                    graph.add((node, predicate, Literal(value)))
            elif value:
                graph.add((node, predicate, Literal(value, lang=DE) if kind == "lang" else Literal(value)))
    for predicate in (N8[name] for name in RELATIONS):
        for source, _, target in list(graph.triples((None, predicate, None))):
            if source in old_nodes and target in old_nodes:
                graph.remove((source, predicate, target))
    for edge in model["edges"]:
        graph.add((node_uri(slug, edge["from"]), N8[edge["type"]], node_uri(slug, edge["to"])))
    return graph


def prepare_change(slug: str, data: object, expected_revision: str, root: Path | None = None) -> tuple[str, str, bool]:
    root = local_root(root if root is not None else ROOT)
    path = case_path(slug, root)
    if revision(path) != expected_revision:
        raise ValueError("Die Datei wurde inzwischen geändert. Fall neu laden und Änderung erneut prüfen.")
    original = Graph().parse(path, format="turtle")
    candidate = graph_from_model(slug, data, original, root)
    if to_isomorphic(candidate) == to_isomorphic(original):
        return path.read_text(encoding="utf-8"), render(slug, root=root), False
    ttl = minimal_turtle(path.read_text(encoding="utf-8"), original, candidate, slug)
    page = render(slug, candidate, root=root)
    return ttl, page, True

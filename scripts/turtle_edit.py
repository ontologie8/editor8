# SPDX-License-Identifier: AGPL-3.0-or-later
"""Write editor changes without reformatting unrelated Turtle statements.

The maintained case files use one case statement, one statement per typed
node, and a final section of one-line relationships. If that layout changes,
the editor refuses to rewrite it instead of silently creating a large diff.
"""

from __future__ import annotations

import re

from rdflib import Graph, Literal, RDF, URIRef
from rdflib.compare import to_isomorphic

from data_contract import EDGES


N8 = "https://notariat8.github.io/ontology/id/"
DCT = "http://purl.org/dc/terms/"
SKOS = "http://www.w3.org/2004/02/skos/core#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
RELATION_NAMES = set(EDGES.values())
RELATIONS = {URIRef(N8 + name) for name in RELATION_NAMES}
RELATION_LINE = re.compile(r"^<([^>]+)> n8:([A-Za-z]+) <([^>]+)> \.$")
PREDICATE_ORDER = [
    RDF.type, URIRef(N8 + "nacNodeId"), URIRef(N8 + "lokaleNodeId"),
    URIRef(SKOS + "prefLabel"), URIRef(DCT + "description"),
    URIRef(DCT + "source"), URIRef(DCT + "license"),
    URIRef(DCT + "references"), URIRef(N8 + "quellstatus"),
    URIRef(N8 + "pflegeStatus"), URIRef(N8 + "offeneFrage"),
    URIRef(N8 + "quellabschnitt"), URIRef(RDFS + "comment"),
    URIRef(N8 + "verantwortlicheRolle"), URIRef(N8 + "datenschutzklasse"),
    URIRef(N8 + "dokumentquelle"), URIRef(N8 + "enthaeltPersonendaten"),
    URIRef(N8 + "erforderlichFuer"), URIRef(N8 + "entscheidungsoption"),
    URIRef(N8 + "hatBaustein"),
]


def _term(value: URIRef | Literal, *, predicate: bool = False) -> str:
    if isinstance(value, Literal):
        return value.n3()
    if value == RDF.type and predicate:
        return "a"
    uri = str(value)
    for base, prefix in ((N8, "n8"), (DCT, "dcterms"), (SKOS, "skos"), (RDFS, "rdfs")):
        local = uri.removeprefix(base)
        if local != uri and re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", local):
            return f"{prefix}:{local}"
    return f"<{uri}>"


def _spans(text: str, slug: str) -> dict[URIRef, tuple[int, int, str]]:
    spans = {}
    lines = text.splitlines(keepends=True)
    offsets = []
    offset = 0
    for line in lines:
        offsets.append(offset)
        offset += len(line)
    case = URIRef(N8 + "vorgangsart-" + slug)
    node_prefix = N8 + f"case/{slug}/node/"
    for index, line in enumerate(lines):
        subject = None
        if line.startswith(f"n8:vorgangsart-{slug}\n"):
            subject = case
        elif line.startswith("<") and "> a n8:" in line:
            uri = line[1:line.index(">")]
            if uri.startswith(node_prefix):
                subject = URIRef(uri)
        if subject is None:
            continue
        end = index
        while end < len(lines) and not lines[end].rstrip().endswith("."):
            end += 1
        if end == len(lines) or subject in spans:
            raise ValueError("Die Turtle-Struktur kann nicht sicher bearbeitet werden")
        start_pos, end_pos = offsets[index], offsets[end] + len(lines[end])
        spans[subject] = (start_pos, end_pos, text[start_pos:end_pos])
    if case not in spans:
        raise ValueError("Der Fallblock in Turtle wurde nicht gefunden")
    return spans


def _statement(subject: URIRef, graph: Graph, old_block: str, case: URIRef) -> str:
    pairs = [(predicate, obj) for _, predicate, obj in graph.triples((subject, None, None)) if predicate not in RELATIONS]
    if not pairs:
        return ""
    order = {predicate: index for index, predicate in enumerate(PREDICATE_ORDER)}

    def key(pair):
        predicate, obj = pair
        token = _term(obj)
        position = old_block.find(token)
        return (order.get(predicate, len(order)), 0 if position >= 0 else 1, position if position >= 0 else str(obj))

    pairs.sort(key=key)
    if subject == case:
        lines = [_term(subject)]
    else:
        types = [pair for pair in pairs if pair[0] == RDF.type]
        if not types:
            raise ValueError("Ein Baustein hat keinen Turtle-Typ")
        first = types[0]
        pairs.remove(first)
        lines = [f"{_term(subject)} a {_term(first[1])}"]
    for predicate, obj in pairs:
        lines.append(f"  {_term(predicate, predicate=True)} {_term(obj)}")
    if subject == case:
        if len(lines) == 1:
            raise ValueError("Der Fallblock ist leer")
        lines = [lines[0], *[line + (" ." if index == len(lines) - 1 else " ;") for index, line in enumerate(lines[1:], 1)]]
    else:
        lines = [line + (" ." if index == len(lines) - 1 else " ;") for index, line in enumerate(lines)]
    return "\n".join(lines) + "\n"


def minimal_turtle(source: str, original: Graph, candidate: Graph, slug: str) -> str:
    """Return a small, semantic-preserving edit of a maintained case file."""
    case = URIRef(N8 + "vorgangsart-" + slug)
    node_prefix = N8 + f"case/{slug}/node/"
    spans = _spans(source, slug)
    before, after = set(original), set(candidate)
    changed = before ^ after
    affected = {subject for subject, predicate, _ in changed if predicate not in RELATIONS}
    if any(subject != case and not str(subject).startswith(node_prefix) for subject in affected):
        raise ValueError("Diese Turtle-Änderung braucht einen manuellen Pull Request")
    edits = []
    additions = []
    for subject in affected:
        old = spans.get(subject)
        block = _statement(subject, candidate, old[2] if old else "", case)
        if old:
            edits.append((old[0], old[1], block))
        elif block:
            additions.append((str(subject), block))
    marker = "# Beziehungen aus dem NaC-Vorlagengraphen; keine BPMN-Sequenzflüsse."
    if source.count(marker) != 1:
        raise ValueError("Der Beziehungsabschnitt in Turtle wurde nicht gefunden")
    relation_start = source.index(marker)
    for start, end, replacement in sorted(edits, reverse=True):
        source = source[:start] + replacement + source[end:]
    relation_start = source.index(marker)
    if additions:
        inserted = "# Lokale Ergänzungen\n\n" + "\n".join(block for _, block in sorted(additions)) + "\n"
        source = source[:relation_start] + inserted + source[relation_start:]
        relation_start += len(inserted)
    head, tail = source[:relation_start], source[relation_start:]
    retained = []
    existing = set()
    for line in tail.splitlines(keepends=True):
        match = RELATION_LINE.fullmatch(line.rstrip("\r\n"))
        if match and match[2] in RELATION_NAMES:
            triple = (URIRef(match[1]), URIRef(N8 + match[2]), URIRef(match[3]))
            existing.add(triple)
            if triple not in after:
                continue
        retained.append(line)
    added_relations = sorted((subject, predicate, obj) for subject, predicate, obj in after - before if predicate in RELATIONS)
    for subject, predicate, obj in added_relations:
        if (subject, predicate, obj) not in existing:
            retained.append(f"<{subject}> n8:{str(predicate).removeprefix(N8)} <{obj}> .\n")
    result = head + "".join(retained)
    if "rdfs:" in result and "@prefix rdfs:" not in result:
        prefix_line = f"@prefix rdfs: <{RDFS}> .\n"
        last_prefix = list(re.finditer(r"(?m)^@prefix [^\n]+\n", result))
        if not last_prefix:
            raise ValueError("Turtle-Präfixe fehlen")
        position = last_prefix[-1].end()
        result = result[:position] + prefix_line + result[position:]
    if to_isomorphic(Graph().parse(data=result, format="turtle")) != to_isomorphic(candidate):
        raise ValueError("Die Turtle-Änderung konnte nicht verlustfrei geschrieben werden")
    return result

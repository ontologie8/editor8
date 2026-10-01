# SPDX-License-Identifier: AGPL-3.0-or-later
"""Find where shared vocabulary terms occur in the pinned 20-case catalog."""

from __future__ import annotations

from collections import Counter

from data_contract import catalog_ids
from rdflib import Graph, RDF, URIRef

from case_editor_model import N8
from vocabulary_editor import model as vocabulary_model


def impact_index(core_text: str, catalog_text: str, cases: dict[str, str], source_ref: str, expected_ids: list[str] | None = None) -> dict:
    """Count RDF uses per case, including its catalog entry and subject area.

    A use is an RDF type assertion of a shared class or a triple using a
    shared property. This is a technical change-impact view, not a claim that
    every legal or process dependency is represented in RDF.
    """
    catalog = Graph().parse(data=catalog_text, format="turtle")
    expected = expected_ids if expected_ids is not None else catalog_ids(catalog)
    if set(cases) != set(expected):
        raise ValueError("Die Auswirkungsübersicht benötigt den vollständigen Datenkatalog")
    identifiers = {URIRef(str(N8) + item["id"]): item["id"] for item in vocabulary_model(core_text)["terms"]}
    uses = {name: [] for name in identifiers.values()}
    for slug in expected:
        graph = Graph().parse(data=cases[slug], format="turtle")
        case = N8[f"vorgangsart-{slug}"]
        for predicate, obj in catalog.predicate_objects(case):
            graph.add((case, predicate, obj))
        for area in catalog.objects(case, N8.hatFachbereich):
            for predicate, obj in catalog.predicate_objects(area):
                graph.add((area, predicate, obj))
        counts: Counter[str] = Counter()
        for _, predicate, obj in graph:
            if predicate in identifiers:
                counts[identifiers[predicate]] += 1
            if predicate == RDF.type and obj in identifiers:
                counts[identifiers[obj]] += 1
        for identifier, count in sorted(counts.items()):
            uses[identifier].append({"slug": slug, "count": count})
    return {"source_ref": source_ref, "case_count": len(expected), "terms": uses}

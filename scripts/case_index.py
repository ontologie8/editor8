# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build a small, read-only index of the pinned NaC case building blocks."""

from __future__ import annotations

from data_contract import catalog_ids
from rdflib import Graph

from case_editor_model import N8, SKOS, _graph_to_model


def build_case_index(catalog_text: str, cases: dict[str, str], source_ref: str, expected_ids: list[str] | None = None) -> dict:
    catalog = Graph().parse(data=catalog_text, format="turtle")
    pinned = expected_ids if expected_ids is not None else catalog_ids(catalog)
    if set(cases) != set(pinned):
        raise ValueError("Die Fallübersicht muss den vollständigen Datenkatalog enthalten")
    entries = []
    for slug in pinned:
        title = catalog.value(N8[f"vorgangsart-{slug}"], SKOS.prefLabel)
        if title is None:
            raise ValueError(f"Bezeichnung der Vorgangsart fehlt: {slug}")
        model = _graph_to_model(slug, Graph().parse(data=cases[slug], format="turtle"))
        for node in model["nodes"]:
            entries.append({
                "slug": slug,
                "case_title": str(title),
                "node_id": node["id"],
                "label": node["label"],
                "category": node["category"],
                "question": node["question"],
                "detail": node["detail"],
            })
    return {"source_ref": source_ref, "case_count": len(pinned), "entries": entries}

# SPDX-License-Identifier: AGPL-3.0-or-later
"""Turn a historical case graph into a reviewable, exact RDF proposal."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from rdflib import Graph
from rdflib.compare import to_isomorphic

from case_editor_model import _graph_to_model, load_case, prepare_change


def prepare_historical_case(
    slug: str, historical_turtle: str, root: Path, describe: Callable[[dict, dict], list[str]],
) -> dict:
    current = load_case(slug, root)
    historical_graph = Graph().parse(data=historical_turtle, format="turtle")
    historical = _graph_to_model(slug, historical_graph)
    historical["revision"] = current["revision"]
    turtle, page, changed = prepare_change(slug, historical, current["revision"], root)
    if to_isomorphic(Graph().parse(data=turtle, format="turtle")) != to_isomorphic(historical_graph):
        raise ValueError("Die frühere Fassung enthält RDF-Aussagen außerhalb der Editorfelder. Bitte in GitHub prüfen.")
    return {"changed": changed, "changes": describe(current, historical) if changed else [], "turtle": turtle, "page": page, "model": historical}

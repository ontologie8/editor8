# SPDX-License-Identifier: AGPL-3.0-or-later
"""Graph explanations derived from the RDF that preview/save actually use."""
from rdflib import Graph, URIRef
from rdflib.compare import graph_diff, to_isomorphic

from case_editor_model import N8, RELATIONS, _graph_to_model, node_uri


def compare_graphs(before: Graph, after: Graph, old: dict, new: dict, uris: dict) -> dict:
    _, added, removed = graph_diff(to_isomorphic(before), to_isomorphic(after))
    old_nodes = {node["id"]: node for node in old["nodes"]}
    new_nodes = {node["id"]: node for node in new["nodes"]}
    relation_predicates = {N8[name] for name in RELATIONS}
    changed_subjects = {s for s, p, _ in list(added) + list(removed) if p not in relation_predicates}
    changes = {}
    for node_id in old_nodes.keys() | new_nodes.keys():
        changes[node_id] = ("added" if node_id not in old_nodes else "removed" if node_id not in new_nodes
                            else "changed" if uris[node_id] in changed_subjects else "unchanged")
    edge_key = lambda edge: (edge["from"], edge["type"], edge["to"])
    old_edges, new_edges = {edge_key(e) for e in old["edges"]}, {edge_key(e) for e in new["edges"]}
    affected = {node_id for node_id, change in changes.items() if change != "unchanged"}
    for source, _, target in old_edges ^ new_edges:
        affected.update((source, target))
    neighbours = set(affected)
    for source, _, target in old_edges | new_edges:
        if source in affected or target in affected:
            neighbours.update((source, target))

    def side(model, other_edges, side_name):
        nodes = [{**node, "change": changes[node["id"]]} for node in model["nodes"] if node["id"] in neighbours]
        edges = [{**edge, "change": side_name if edge_key(edge) not in other_edges else "unchanged"}
                 for edge in model["edges"] if edge["from"] in neighbours and edge["to"] in neighbours]
        return {"nodes": nodes, "edges": edges, "total_nodes": len(model["nodes"])}

    return {"before": side(old, new_edges, "removed"),
            "after": side(new, old_edges, "added"),
            "rdf_added": len(added), "rdf_removed": len(removed),
            "affected_nodes": sorted(affected),
            "node_changes": {name: sum(change == name for change in changes.values()) for name in ("added", "removed", "changed")},
            "edge_changes": {"added": len(new_edges - old_edges), "removed": len(old_edges - new_edges)}}


def case_comparison(slug: str, before_text: str, after_text: str) -> dict:
    before = Graph().parse(data=before_text, format="turtle")
    after = Graph().parse(data=after_text, format="turtle")
    old, new = _graph_to_model(slug, before), _graph_to_model(slug, after)
    uris = {node["id"]: node_uri(slug, node["id"]) for node in old["nodes"] + new["nodes"]}
    return compare_graphs(before, after, old, new, uris)


def vocabulary_comparison(before_text: str, after_text: str) -> dict:
    from vocabulary_editor import model
    before = Graph().parse(data=before_text, format="turtle")
    after = Graph().parse(data=after_text, format="turtle")
    def projection(text):
        terms = model(text)["terms"]
        ids = {term["id"] for term in terms}
        return {"nodes": [{**term, "category": term["kind"]} for term in terms],
                "edges": [{"from": term["id"], "type": field, "to": term[field]}
                          for term in terms for field in ("parent", "domain", "range") if term.get(field) in ids]}
    old, new = projection(before_text), projection(after_text)
    uris = {node["id"]: URIRef(str(N8) + node["id"]) for node in old["nodes"] + new["nodes"]}
    return compare_graphs(before, after, old, new, uris)

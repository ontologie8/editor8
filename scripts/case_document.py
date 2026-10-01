# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render every case's human-readable Mermaid page from its Turtle module."""

import json
from pathlib import Path

from rdflib import Graph, Namespace, RDF


from data_contract import DATA_ROOT as ROOT, local_root, parse_baseline
N8 = Namespace("https://notariat8.github.io/ontology/id/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
DCT = Namespace("http://purl.org/dc/terms/")
CATEGORIES = [
    (N8.Angabenfrage, "Angabenfragen", "info"),
    (N8.Dokumenttyp, "Dokumenttypen", "doc"),
    (N8.Entscheidungspunkt, "Entscheidungen", "decision"),
    (N8.Pruefgate, "Prüfgates", "gate"),
    (N8.Nachweistyp, "Nachweistypen", "evidence"),
]
RELATIONS = {
    N8.erfordert: "erfordert",
    N8.informiert: "informiert",
    N8.blockiertBisVollstaendig: "blockiert bis vollständig",
    N8.blockiertBisGeprueft: "blockiert bis geprüft",
    N8.erfordertEntscheidung: "erfordert Entscheidung",
    N8.belegtDurch: "belegt durch",
    N8.fuellt: "füllt",
    N8.bestimmt: "bestimmt",
}


def node_id(graph: Graph, node) -> str:
    value = graph.value(node, N8.nacNodeId) or graph.value(node, N8.lokaleNodeId)
    return str(value) if value is not None else ""


def mermaid_label(value: str) -> str:
    return value.replace('"', "#quot;").replace("\n", " ").replace("|", "/")


def render(slug: str, case_graph: Graph | None = None, root: Path | None = None) -> str:
    root = local_root(root if root is not None else ROOT)
    baseline = parse_baseline((root / "catalog/nac-baseline.json").read_text(encoding="utf-8"))
    detailed = baseline.get("editor_document_version", 1) == 2
    graph = Graph()
    graph.parse(root / "catalog/nac-usecases.ttl", format="turtle")
    if case_graph is None:
        graph.parse(root / "cases" / slug / "ontology.ttl", format="turtle")
    else:
        graph += case_graph
    case = N8[f"vorgangsart-{slug}"]
    title = str(graph.value(case, SKOS.prefLabel))
    summary = str(graph.value(case, DCT.description))
    source = str(graph.value(case, DCT.source))
    bpmn = str(graph.value(case, N8.hatBpmnModell))
    nodes = set(graph.objects(case, N8.hatBaustein))
    by_type = {}
    for node_type, heading, style in CATEGORIES:
        by_type[heading] = (style, sorted((n for n in nodes if (n, RDF.type, node_type) in graph), key=lambda n: node_id(graph, n)))
    order = [n for _, group in by_type.values() for n in group]
    ids = {node: f"n{index}" for index, node in enumerate(order, 1)}
    lines = [
        f"# {title}",
        "",
        f"{summary}",
        "",
        f"[Turtle-Quelle](ontology.ttl) · [NaC-Vorlagengraph]({source}) · [NaC-BPMN]({bpmn})",
        "",
    ]
    if detailed and slug == "erbausschlagung":
        lines.extend([
            "[Vollständiger Ablaufplan](../../sources/erbausschlagung/ablaufplan.md) · [Übernahme und Prüfpunkte](../../docs/erbausschlagung/import-notes.md) · [Synthetische Prüfszenarien](../../docs/erbausschlagung/synthetische-szenarien.md)",
            "",
        ])
    lines.extend([
        "Ausgangspunkt dieses Fachgraphen sind **Vorlagenbegriffe** aus NaC; lokale Ergänzungen tragen eine `local.`-Kennung. `open` in der NaC-Quelle bedeutet eine offene Modellierungsfrage, keinen Status einer echten Akte. Die Pfeile zeigen fachliche Beziehungen; den zeitlichen Ablauf beschreibt das verlinkte BPMN-Modell. Eine notarielle Prüfung dieser Übernahme steht noch aus.",
        "",
        "## Fallgraph",
        "",
        "```mermaid",
        "flowchart LR",
    ])
    for index, (heading, (style, group)) in enumerate(by_type.items(), 1):
        lines.append(f'    subgraph g{index}["{heading}"]')
        for node in group:
            label = mermaid_label(str(graph.value(node, SKOS.prefLabel)))
            lines.append(f'        {ids[node]}["{label}"]')
        lines.append("    end")
    edges = []
    for pred, label in RELATIONS.items():
        for start, _, target in graph.triples((None, pred, None)):
            if start in ids and target in ids:
                edges.append((ids[start], ids[target], label))
    for start, target, label in sorted(edges):
        lines.append(f"    {start} -->|{label}| {target}")
    lines.extend([
        "    classDef info fill:#e8f2ff,stroke:#4b77a7,color:#111;",
        "    classDef doc fill:#eef8ee,stroke:#4d8a55,color:#111;",
        "    classDef decision fill:#fff4df,stroke:#ac7a21,color:#111;",
        "    classDef gate fill:#fdebec,stroke:#b45c64,color:#111;",
        "    classDef evidence fill:#f3edff,stroke:#8060aa,color:#111;",
    ])
    for style, group in by_type.values():
        if group:
            lines.append(f"    class {','.join(ids[node] for node in group)} {style};")
    lines.extend(["```", "", "## Enthaltene Bausteine", "", "| Gruppe | Anzahl |", "| --- | ---: |"])
    for heading, (_, group) in by_type.items():
        lines.append(f"| {heading} | {len(group)} |")
    chapters = {chapter: index for index, chapter in enumerate(("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"))}
    local_nodes = sorted(
        (node for node in order if graph.value(node, N8.lokaleNodeId) is not None),
        key=lambda node: (chapters.get(str(graph.value(node, N8.quellabschnitt)), 99), str(graph.value(node, SKOS.prefLabel))),
    )
    if detailed and local_nodes:
        lines.extend(["", "## Ergänzungen aus der Fachvorlage", "", "Diese Einträge sind ein fachlicher Entwurf. Die Kapitelangabe verweist auf den vollständigen Ablaufplan; Entscheidungen und Prüfgates ersetzen keine Einzelfallprüfung.", "", "| Kapitel | Baustein | Prüfgegenstand oder mögliche Optionen |", "| --- | --- | --- |"])
        for node in local_nodes:
            chapter = str(graph.value(node, N8.quellabschnitt) or "–")
            label = str(graph.value(node, SKOS.prefLabel)).replace("|", "/")
            explanation = str(graph.value(node, RDFS.comment) or graph.value(node, N8.offeneFrage) or "")
            if not explanation:
                explanation = ", ".join(sorted(str(value) for value in graph.objects(node, N8.entscheidungsoption)))
            if not explanation:
                explanation = f"Siehe Kapitel {chapter} des vollständigen Ablaufplans."
            lines.append(f"| {chapter} | {label} | {explanation.replace('|', '/')} |")
    legal = sorted({str(url) for url in graph.objects(case, DCT.references)})
    lines.extend(["", "## In NaC genannte Rechtsquellen", ""])
    for url in legal:
        lines.append(f"- [{url}]({url})")
    lines.extend([
        "",
        "Diese Links dokumentieren die Quellen des NaC-Vorlagengraphen; sie belegen keine erneute rechtliche Prüfung.",
        "",
        "## Pflege",
        "",
        "Fachbegriffe und Beziehungen mit dem [Browser-Editor](https://github.com/ontologie8/editor8#lokal-starten) oder in [ontology.ttl](ontology.ttl) ändern. Der Editor erzeugt diese Seite beim Speichern. Bei manueller Turtle-Pflege `python scripts/render_case_docs.py --write` ausführen und beide Änderungen gemeinsam reviewen.",
        "",
    ])
    return "\n".join(lines)

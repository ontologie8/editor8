# SPDX-License-Identifier: AGPL-3.0-or-later
"""Artificial examples, deliberately unrelated to maintained notarial models."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

class DemoDataset:
    def __init__(self):
        self.temp = TemporaryDirectory(prefix='editor8-demo-')
        self.root = Path(self.temp.name)
        (self.root/'catalog').mkdir()
        (self.root/'ontology').mkdir()
        self.ids = ['demo-eins', 'demo-zwei']
        (self.root/'catalog/nac-baseline.json').write_text(json.dumps({'editor_contract_version':1,'business_case_type_ids':self.ids}), encoding='utf-8')
        prefixes = '@prefix n8: <https://notariat8.github.io/ontology/id/> .\n@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n@prefix dcterms: <http://purl.org/dc/terms/> .\n'
        catalog = prefixes
        classes = ['Angabenfrage','Dokumenttyp','Entscheidungspunkt','Pruefgate','Nachweistyp']
        for slug in self.ids:
            title = 'Künstlicher Fall ' + slug
            catalog += f'n8:vorgangsart-{slug} skos:prefLabel "{title}"@de ; n8:hatBpmnModell <https://example.org/process/{slug}> .\n'
            directory=self.root/'cases'/slug; directory.mkdir(parents=True)
            nodes=[f'<https://notariat8.github.io/ontology/id/case/{slug}/node/demo{i}>' for i in range(5)]
            text=prefixes+f'n8:vorgangsart-{slug}\n  dcterms:description "Künstliches Modell für Tests"@de ; dcterms:source <https://example.org/source> ; dcterms:references <https://example.org/reference> ; n8:hatBaustein '+', '.join(nodes)+' .\n'
            for i, (node, kind) in enumerate(zip(nodes,classes)):
                text += f'{node} a n8:{kind} ; n8:nacNodeId "demo{i}" ; n8:quellstatus "open" ; skos:prefLabel "Beispiel {kind}"@de .\n'
            text += f'# Beziehungen aus dem NaC-Vorlagengraphen; keine BPMN-Sequenzflüsse.\n{nodes[0]} n8:erfordert {nodes[1]} .\n'
            (directory/'ontology.ttl').write_text(text,encoding='utf-8')
        (self.root/'catalog/nac-usecases.ttl').write_text(catalog,encoding='utf-8')
        core=prefixes+'@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n@prefix owl: <http://www.w3.org/2002/07/owl#> .\n'
        for kind in classes: core+=f'n8:{kind} a rdfs:Class, owl:Class ; skos:prefLabel "Beispiel {kind}"@de ; rdfs:label "Beispiel {kind}"@de ; rdfs:comment "Vollständig künstlicher Begriff für die Bedienprüfung."@de .\n'
        (self.root/'ontology/core.ttl').write_text(core,encoding='utf-8')
    def close(self):
        self.temp.cleanup()

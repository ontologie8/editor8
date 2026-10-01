# SPDX-License-Identifier: AGPL-3.0-or-later
"""Version 1 NaC RDF adapter. No maintained notarial models live here."""
import json
import os
from pathlib import Path
import re

CONTRACT_VERSION = 1
APP_ROOT = Path(__file__).resolve().parents[1]
# Missing configuration must never silently target the software checkout.
DATA_ROOT = Path(os.environ['EDITOR8_DATA_ROOT']).expanduser().resolve() if os.environ.get('EDITOR8_DATA_ROOT') else APP_ROOT / '.unconfigured-data-root'
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')

def parse_baseline(text: str) -> dict:
    value = json.loads(text)
    if not isinstance(value, dict) or type(value.get('editor_contract_version', 1)) is not int or value.get('editor_contract_version', 1) != CONTRACT_VERSION:
        raise ValueError('Unbekannte Datenvertragsversion')
    if type(value.get('editor_document_version', 1)) is not int or value.get('editor_document_version', 1) not in (1, 2):
        raise ValueError('Unbekannte Leseseitenversion')
    ids = value.get('business_case_type_ids')
    if not isinstance(ids, list) or not 1 <= len(ids) <= 1000 or any(not isinstance(item, str) or not SLUG.fullmatch(item) for item in ids) or len(ids) != len(set(ids)):
        raise ValueError('Ungültige Fallkennungen im Datenkatalog')
    return value

def local_root(root=None):
    selected = Path(root).resolve() if root is not None else DATA_ROOT
    if selected == APP_ROOT:
        raise ValueError('Das Software-Repository darf kein Datenziel sein')
    if not (selected / 'catalog/nac-baseline.json').is_file():
        raise ValueError('EDITOR8_DATA_ROOT muss auf einen separaten Datencheckout zeigen')
    if APP_ROOT in selected.parents:
        raise ValueError('Das Software-Repository darf kein Datenziel sein')
    return selected

def catalog_ids(catalog):
    from rdflib.namespace import SKOS
    prefix = 'https://notariat8.github.io/ontology/id/vorgangsart-'
    ids = sorted({str(subject)[len(prefix):] for subject in catalog.subjects(SKOS.prefLabel, None) if str(subject).startswith(prefix)})
    return parse_baseline(json.dumps({'business_case_type_ids': ids}))['business_case_type_ids']

CATEGORIES = {
    "required_information": ("Angabenfrage", "Angabenfragen"),
    "documents": ("Dokumenttyp", "Dokumenttypen"),
    "decisions": ("Entscheidungspunkt", "Entscheidungen"),
    "gates": ("Pruefgate", "Prüfgates"),
    "evidence": ("Nachweistyp", "Nachweistypen"),
}

EDGES = {
    "requires": "erfordert",
    "informs": "informiert",
    "blocks_until_complete": "blockiertBisVollstaendig",
    "blocks_until_reviewed": "blockiertBisGeprueft",
    "requires_decision": "erfordertEntscheidung",
    "evidenced_by": "belegtDurch",
    "populates": "fuellt",
    "determines": "bestimmt",
}

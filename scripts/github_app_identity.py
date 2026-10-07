# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate the editor's App registration from its explicit data installation."""
import json
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from release_info import REPOSITORY
from repository_registry import NAME

SOFTWARE_REPOSITORY = urlparse(REPOSITORY).path.strip('/')
APP_OWNER = SOFTWARE_REPOSITORY.split('/')[0]
APP_NAME = 'Ontologie8 Editor'
SLUG = re.compile(r'[A-Za-z0-9-]+\Z')


def validate_targets(app_owner: str, data_repository: str) -> None:
    if app_owner.lower() != APP_OWNER.lower():
        raise ValueError('Die GitHub-App-Registrierung gehört zum Editorbetreiber ' + APP_OWNER)
    if not NAME.fullmatch(data_repository) or data_repository.lower() == SOFTWARE_REPOSITORY.lower():
        raise ValueError('Ein separates Datenrepository muss ausdrücklich angegeben werden')


def existing_app(slug: str, client_id: str) -> dict:
    if not SLUG.fullmatch(slug):
        raise ValueError('Ungültige GitHub-App-Kennung')
    request = Request('https://api.github.com/apps/' + slug, headers={
        'Accept': 'application/vnd.github+json', 'User-Agent': 'editor8-app-identity',
    })
    with urlopen(request, timeout=20) as response:
        app = json.load(response)
    if app.get('owner', {}).get('login', '').lower() != APP_OWNER.lower():
        raise ValueError('Die bestehende GitHub-App ist noch nicht beim Editorbetreiber ' + APP_OWNER)
    if not client_id or app.get('client_id') != client_id:
        raise ValueError('Client-ID und bestehende GitHub-App stimmen nicht überein')
    if app.get('slug') != slug or not isinstance(app.get('name'), str) or not app['name']:
        raise ValueError('Unvollständige GitHub-App-Identität')
    return {'name': app['name'], 'slug': slug, 'owner': APP_OWNER,
            'settings_url': f'https://github.com/organizations/{APP_OWNER}/settings/apps/{slug}'}

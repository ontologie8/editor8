# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tenant-bound OIDC with PKCE, nonce, signed tokens and delegated group checks."""
import json
import secrets
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen
from uuid import UUID

import jwt
import msal

from access_control import AccessDenied


class EntraIdentity:
    SCOPES = ["User.Read"]

    def __init__(self, tenant, client, secret, origin):
        self.tenant, self.client = str(UUID(tenant)), str(UUID(client))
        self.secret = secret
        self.origin = origin.rstrip("/")
        self.authority = "https://login.microsoftonline.com/" + self.tenant
        self.keys = jwt.PyJWKClient(self.authority + "/discovery/v2.0/keys", timeout=15)

    def application(self, cache=None):
        return msal.ConfidentialClientApplication(self.client, authority=self.authority,
                                                 client_credential=self.secret, token_cache=cache,
                                                 timeout=15)

    def begin(self):
        flow = self.application().initiate_auth_code_flow(self.SCOPES, redirect_uri=self.origin + "/entra/callback")
        flow["editor8_nonce"] = parse_qs(urlparse(flow["auth_uri"]).query)["nonce"][0]
        return flow

    def complete(self, flow, query):
        cache = msal.SerializableTokenCache()
        result = self.application(cache).acquire_token_by_auth_code_flow(flow, query, scopes=self.SCOPES)
        if not result.get("access_token") or not result.get("id_token"):
            raise AccessDenied("Die Betreiberanmeldung konnte nicht bestätigt werden. Bitte erneut anmelden.")
        token = result["id_token"]
        claims = jwt.decode(token, self.keys.get_signing_key_from_jwt(token).key,
                            algorithms=["RS256"], audience=self.client,
                            issuer=self.authority + "/v2.0",
                            options={"require": ["exp", "iat", "iss", "aud", "tid", "oid", "nonce"]})
        if claims["tid"] != self.tenant:
            raise AccessDenied("Dieses Konto gehört nicht zum zugelassenen Mandanten.")
        if not secrets.compare_digest(claims["nonce"], flow["editor8_nonce"]):
            raise AccessDenied("Die Anmeldebestätigung gehört zu einer anderen Anmeldung.")
        if "App.Use" not in claims.get("roles", []):
            raise AccessDenied("Dieses Konto ist der Editor-Anwendung nicht zugewiesen.")
        # MSAL verifies nonce against its hashed flow nonce as well as state.
        if claims["oid"] != result["id_token_claims"]["oid"]:
            raise AccessDenied("Die Anmeldebestätigung stimmt nicht überein.")
        return {"principal": self.tenant + ":" + str(UUID(claims["oid"])),
                "entra_oid": str(UUID(claims["oid"])), "entra_cache": cache.serialize()}

    def memberships(self, session, group_ids):
        cache = msal.SerializableTokenCache()
        cache.deserialize(session["entra_cache"])
        app = self.application(cache)
        accounts = app.get_accounts()
        if len(accounts) != 1:
            raise AccessDenied("Bitte die Betreiberanmeldung erneuern.")
        token = app.acquire_token_silent(self.SCOPES, account=accounts[0])
        session["entra_cache"] = cache.serialize()
        if not token or not token.get("access_token"):
            raise AccessDenied("Bitte die Betreiberanmeldung erneuern.")
        groups = sorted(group_ids)
        memberships = set()
        for start in range(0, len(groups), 20):
            req = Request("https://graph.microsoft.com/v1.0/me/checkMemberGroups",
                          data=json.dumps({"groupIds": groups[start:start + 20]}).encode(),
                          headers={"Authorization": "Bearer " + token["access_token"], "Content-Type": "application/json"},
                          method="POST")
            with urlopen(req, timeout=15) as response:
                result = json.load(response)
            values = result.get("value")
            if not isinstance(values, list) or not set(values) <= set(groups[start:start + 20]):
                raise ValueError("Ungültige Gruppenantwort")
            memberships.update(values)
        return memberships

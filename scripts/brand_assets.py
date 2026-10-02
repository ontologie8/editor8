# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit public allowlist for the user-selected software8 brand images."""

BRAND_ASSETS = {
    f"/assets/brand/{mark}_{size}.png": f"assets/brand/{mark}_{size}.png"
    for mark in ("e8", "n8")
    for size in (32, 192, 526)
}

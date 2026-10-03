# SPDX-License-Identifier: AGPL-3.0-or-later
"""Public, artificial learning content; never expose arbitrary repo paths."""
LEARNING_ASSETS = {
    "/learning/": ("learning/index.html", "text/html; charset=utf-8"),
    "/learning/index.html": ("learning/index.html", "text/html; charset=utf-8"),
    "/learning/style.css": ("learning/style.css", "text/css; charset=utf-8"),
    "/learning/app.js": ("learning/app.js", "text/javascript; charset=utf-8"),
    "/learning/content.js": ("learning/content.js", "text/javascript; charset=utf-8"),
}
